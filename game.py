
# Pygloo imports
# 
import pygloo
from pygloo import *
from ctypes import *
from simpleShader import makeProgram

# Sort of useful mat libs
# 
from vec import *
import math
from random import randrange, random

# Pygame
# 
from pygame.locals import *
from gameInput import *

# State stuff
# 
from highscore import HighScoreState

# Other stuff
# 
from GL_assets import *
from collections import defaultdict
import pygame
import ascii

from random import randint, choice
#
#
Assets = GL_assets()



class GameState(object):
	"""docstring for GameState"""
	def __init__(self):
		super(GameState, self).__init__()
		self.substate = ExpositionSubState()

	def tick(self, controller):
		nstate = self.substate.tick(self, controller)
		if nstate:
			if isinstance(nstate, GameSubState):
				self.substate = nstate
			else:
				return nstate

	def render(self, gl, w, h, ascii_r=None):
		return self.substate.render(gl, w, h, ascii_r)

class GameSubState(object):
	"""docstring for GameSubState"""
	def tick(self, game, controller):
		pass

	def render(self, gl, w, h, ascii_r=None):
		return mat4.identity()
	







class ExpositionSubState(object):
	"""docstring for ExpositionSubState"""
	def __init__(self):
		super(ExpositionSubState, self).__init__()
		self.textarea = ascii.TextArea((120,60), 'big')
		self.textarea.align = 'c'
		self.textarea.showcursor = True
		self.textarea.blinkinterval = 20
		self.textarea.writeinterval = 2
		with open('./Backstory.txt') as file:
			self.textarea.write(file.read().replace(r'\0', '\0').replace(r'\\', '\\'))
		# }
	# }
	
	def tick(self, game, controller):
		if controller.key_pressed(C_TRIGGER): return LevelInformationSubState(1)
	# }
	
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r is None: return
		dw, dh = ascii_r._text_size
		#new_size = (max(0, dw - 20), max(0, dh - 10))
		#old_size = self.textarea.size
		#self.textarea.size = new_size
		#if old_size != new_size: self.textarea.invalidate()
		#str(self.textarea)
		ascii_r.draw_text(self.textarea, textorigin=(0.5, 0.5), screenorigin=(0.5,0.5))
		#print 'foooooo', self.pause
	# }
# }

class LevelInformationSubState(GameSubState):
	"""
	Displays the current enemy as well as a small exposition before you go into battle
	"""
	def __init__(self, level = 1, score = 0):
		super(LevelInformationSubState, self).__init__()
		self.level = level
		self.score = score
		self.alive_for = 0

		self.textarea = ascii.TextArea((200,40), 'big')
		self.textarea.align = 'c'
		self.textarea.showcursor = True
		self.textarea.blinkinterval = 20
		self.textarea.writeinterval = 2

		with open('./bandit_dialog.txt') as dialogs, open('./bandit_names.txt') as names, open('./bandit_quips.txt') as quips:
			d = choice(dialogs.readlines()).strip('\n')
			n = choice(names.readlines()).strip('\n')
			q = choice(quips.readlines()).strip('\n')

			level_info = d.format(name=n, quip=q)
			self.textarea.write(level_info.replace(r'\0', '\0').replace(r'\\', '\\'))


	def tick(self, game, controller):
		if controller.key_pressed(C_TRIGGER): return PlayGameSubState(level=self.level, score=self.score)

	def render(self, gl, w, h, ascii_r=None):

		self.alive_for += 1

		zfar = 1000
		znear = 0.1

		# Create view and projection matrix
		#
		proj = mat4.perspectiveProjection(math.pi / 3, float(w)/h, znear, zfar)

		cam_pos = vec3([0,-4,15])
		view = mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z).inverse()
		model = mat4.rotateX(math.pi * 0.3) * mat4.rotateY(math.pi * (self.alive_for/100.0)) * mat4.scale(0.25, 0.25, 0.25)
		mv = view * model

		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="enemyship")
		prog = Assets.get_shader(tag="ship")

		# Render Ship
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		
		gl.glUniform3f(gl.glGetUniformLocation(prog, "color"), 0.333, 1, 1)
		gl.glUniform1f(gl.glGetUniformLocation(prog, "explode_time"), 0.0)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


		if ascii_r:
			art = ascii.wordart("Level {l}".format(l=self.level), 'big', align='c')
			ascii_r.draw_text(art, color = (1, 0.333, 1), screenorigin = (0.5,0.333), textorigin = (0.5, 0.0), align = 'c')
			ascii_r.draw_text(self.textarea, screenorigin=(0.5,0.333), textorigin=(0.5, 1.0))



		return proj

		
		

class PlayGameSubState(GameSubState):
	"""docstring for PlayGameSubState"""
	def __init__(self, level = 1, score = 0):
		super(PlayGameSubState, self).__init__()
		self.show_spheres = False
		self.show_score = False
		self.level = level
		self.bounty = self.level * 100000
		self.score = score
		self.ammo_bill = 0
		self.damage_bill = 0
		self.soundover = False
		pygame.mixer.music.stop()

		self.reset()

	def reset(self):
		self.scene = {}
		self.scene["bullet_collection"] = BulletCollection()
		self.scene["mine_collection"] = MineCollection()
		self.scene["enemy_ship"] = _generate_enemy(self.level)
		self.scene["asteroid_field"] = AsteroidField()
		ship = Ship()
		self.scene["ship"] = ship
		# display only
		ship.score = self.score
		ship.level = self.level
	
	
	def update_score(self, ship):
		self.damage_bill = (100 - ship.health) * 1000
		self.ammo_bill = ship.shots_fired * 100
		self.score += self.bounty - self.damage_bill - self.ammo_bill
	# }
	
	# Game logic
	#
	def tick(self, game, controller):

		# GameLogic
		# 
		if controller.key_pressed(K_s):
			self.show_spheres = not self.show_spheres

		# Update all objects in the scene
		#
		scene_itr = self.scene.copy()
		for (_, obj) in scene_itr.items():
			obj.update(self.scene, controller)

		# Process results of update
		#
		ship = self.scene["ship"]
		if ship.gameover > 60 and pygame.mixer.get_busy() == False:
			if ship.lose:
				# you lost -> game over
				# enemy escaped -> you suck so no one will pay you bounties
				if self.soundover == False:
					Assets.get_sound(tag="gameover").play()
					self.soundover = True
				if controller.key_pressed(C_TRIGGER) and self.soundover == True:
					# still have you enter a name cause multiple levels
					# but dont update the score from this level
					return HighScoreState(self.score, 0 if self.score > 0.0 else 1)
			elif ship.win:
				# you won -> can continue
				if controller.key_pressed(C_TRIGGER):
					if not self.show_score:
						ship.gameover = 1
						self.show_score = True
						self.update_score(ship)
					elif self.level < 10:
						return LevelInformationSubState(self.level+1, self.score)
					else:
						return HighScoreState(self.score, 0)
		# }

	# Render logic
	#
	def render(self, gl, w, h, ascii_r=None):
		zfar = 1000
		znear = 0.1

		# Create view and projection matrix
		#
		proj = mat4.perspectiveProjection(math.pi / 3, float(w)/h, znear, zfar)
		view = self.scene["ship"].get_view_matrix()
		# view = self.scene["enemy_ship"].get_view_matrix()

		# Render all objects in the scene
		# 
		for (_, obj) in self.scene.items():
			obj.draw(gl, proj, view)

		if ascii_r:
			for (_, obj) in self.scene.items():
				obj.draw_ascii(ascii_r, proj, view)

			ship = self.scene['ship']
			
			if ship.win:
				if self.show_score :
					art = ascii.wordart('Bonuses!\n', 'big', align='c')
					ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.5,0.75), textorigin = (0.5, 0.0))

					# Draw the bonus from mission_info
					art = ascii.wordart('Bounty\nDamage Bill\nAmmo Bill\nProfit', 'big', align='r')
					ascii_r.draw_text(art, color = (1, 0.333, 1), screenorigin = (0.45,0.75), textorigin = (1.0, 1.0))

					#Scores associated with bonuses
					art = ascii.wordart('${0}\n$-{1}\n$-{2}\n${3}'.format(self.bounty, self.damage_bill, self.ammo_bill, self.score), 'big', align='r')
					ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.55,0.75), textorigin = (0.0, 1.0))

				else :
					art = ascii.wordart('NICE BRO!\n[Press SPACE to continue]', 'big', align='c')
					ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.5,0.5), textorigin = (0.5, 0.5))
				
			elif self.scene["ship"].dead:
				art = ascii.wordart('YOU HAVE DIED!\nYOU LOSE!\n[Press SPACE]', 'big', align='c')
				ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.5,0.5), textorigin = (0.5, 0.5))
			
			elif self.scene["enemy_ship"].win:
				art = ascii.wordart('YOUR BOUNTY ESCAPED!\nYOU LOSE!\n[Press SPACE]', 'big', align='c')
				ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.5,0.5), textorigin = (0.5, 0.5))
		# temp ?
		
		


		# Debug colliding spheres
		#
		if self.show_spheres:
			all_spheres = [s for (_, obj) in self.scene.items() for s in obj.get_sphere_list()]
			# all_spheres.extend( self.scene["ship"].get_sphere_list() )
			# all_spheres.extend( self.scene["bullet_collection"].get_sphere_list() )
			# all_spheres.extend( self.scene["asteroid_field"].get_sphere_list() )

			if len(all_spheres) > 0 :

				# Retreive model and shader
				#
				vao, vao_size = Assets.get_geometry(tag="sphere")
				inst_vbo = Assets.get_inst_vbo(tag="sphere")
				prog = Assets.get_shader(tag="sphere")

				# Load geometry, shader and projection once
				#
				gl.glUseProgram(prog)
				gl.glBindVertexArray(vao)
				gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

				gl.glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

				# Create and buffer the instance data
				# 
				mv_array = []
				for s in all_spheres:
					scale = mat4.scale(s.radius, s.radius, s.radius)
					position = mat4.translate(s.center.x, s.center.y, s.center.z)
					mv = (view * position * scale).transpose()
					mv_array.extend(mv.flatten())

				mv_c_array = pygloo.c_array(GLfloat, mv_array)
				gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
				gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )

				# Render
				# 	
				gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, len(all_spheres))

				gl.glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


				
		# ascii needs proj matrix
		return proj


class SceneObject(object):
	"""docstring for BulletCollection"""
	def update(self, scene, controller):
		pass

	def draw(self, gl, proj, view):
		pass

	def draw_ascii(self, ascii_r, proj, view):
		pass

	def get_sphere_list(self):
		return []







class BulletCollection(SceneObject):
	"""docstring for BulletCollection"""
	def __init__(self):
		super(BulletCollection, self).__init__()
		self.bullet_list = []

		self.bullet_count = 0
		self.bullet_hit_count = 0
	
	def update(self, scene, controller):
		ship_z = scene["ship"].get_position().z
		self.bullet_hit_count += len([b for b in self.bullet_list if b.exploded])
		self.bullet_list = [b for b in self.bullet_list if b.power > 0 and not b.exploded] # TODO cleanup / removes if it gets 100 away from the ship
		for b in self.bullet_list:
			b.update(scene, controller)
			

	def draw(self, gl, proj, view):
		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="bullet")
		inst_vbo = Assets.get_inst_vbo(tag="bullet")
		prog = Assets.get_shader(tag="bullet")

		# Load geometry, shader and projection once
		#
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		# Create and buffer the instance data
		# 
		mv_array = []
		model = mat4.scale(0.5,0.5,0.5)

		for b in self.bullet_list:
			# Set up matricies
			#
			position = mat4.translate(b.position.x, b.position.y, b.position.z)
			mv = (view * position * model).transpose()
			mv_array.extend(mv.flatten())

		mv_c_array = pygloo.c_array(GLfloat, mv_array)
		gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
		gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )

		# Render
		# 	
		gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, len(self.bullet_list))


	def add_bullet(self, position, direction, velocity):
		self.bullet_count += 1
		self.bullet_list.append(Bullet(position, direction, velocity))

	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for a in self.bullet_list]

class Bullet(object):
	"""docstring for Bullet"""
	def __init__(self, position, direction, velocity):
		super(Bullet, self).__init__()
		self.position = position
		self.velocity = direction.unit().scale(5) + velocity
		self.power = 60				# Live for 60 "ticks"
		self.exploded = False
	
	def get_position(self):
		return self.position

	def get_sphere(self):
		return sphere(self.position, 0.25)
	
	def update(self, scene, controller):
		self.position = self.position + self.velocity
		self.power -= 1
		
		ship = scene['ship']
		enemyship = scene["enemy_ship"]
		
		a = self.get_sphere()
			
		if any( ss.sphere_intersection(a) <= 0 for ss in enemyship.get_sphere_list()):
			Assets.get_sound(tag="hitbybullet").play()
			enemyship.take_damage(10)
			ship.shots_hit += 1
			self.exploded = True
		
		for m in scene['mine_collection'].mine_list:
			if m.get_sphere().sphere_intersection(a) <= 0:
				m.exploded = True
			# }
		# }
	# }
# }













class Ship(SceneObject):

	"""docstring for Ship"""
	def __init__(self):
		super(Ship, self).__init__()

		# Constants
		x_speed = 1
		y_speed = 1
		z_speed = 2
		self.max_velocity = vec3([x_speed, y_speed, 0])
		self.min_velocity = vec3([-x_speed, -y_speed, -z_speed])
		self.acceleration = vec3([0.1, 0.1, 0.1])
		self.dampening = 0.03

		# Fields
		self.position = vec3([0, 0, 0])
		self.velocity = vec3([0, 0, -2.0])
		self.euler_rotation = vec3([0,0,0])
		self.health = 100
		self.dead = False
		self.fired = True
		self.cooldown = 0
		self.enemy_position = vec3([0, 0, 0]) # doesn't matter what value
		self.mine_positions = []
		self.score = 0
		self.level = 1
		self.win = False
		self.lose = False
		self.autopilot = None # instance of EnemyShip for controlling our ship (after winning)
		
		self.gameover = 0 # counter for 'gameover' subsubnotstate
		
		self.end = 9999 # asteroids end when?
		
		self.explode_time = 0.0; # how exploded are we?
		
		self.shots_fired = 0
		self.shots_hit = 0
		
		# Get joystick controls
		self.joystick_count = pygame.joystick.get_count()
		for i in range(self.joystick_count):
			self.joystick = pygame.joystick.Joystick(i)
			self.joystick.init()
		
	def get_score(self):
		return self.score
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 1.5, 6])
		# cam_Xrot = -math.pi / 15
		ship_pos = vec3([self.position.x, self.position.y, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			# mat4.rotateX(cam_Xrot) *
			mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z)).inverse()

	# Spheres suited to ship model
	# 	approx sphere 0,0,0 radius 4
	def get_sphere_list(self):
		all_spheres = [sphere(self.position + vec3([0, 0, -1.0]), 0.5)]
		wing_offset = [ 
			vec4([0.5, 0, 0, 1]),
			vec4([1.3, 0, 0.2, 1]),
			vec4([1.8, 0, 0.5, 1]) ]
		wing_radii = [0.6, 0.3, 0.2]

		pos = mat4.translate(self.position.x, self.position.y, self.position.z)
		rot = self.get_orientation_matrix()
		comb = pos * rot
		flip = mat4.scale(-1,-1, 1)

		all_spheres.extend( [ sphere(comb.multiply_vec4(v).xyz, r) for (v,r) in zip(wing_offset, wing_radii) ] ) # Right wing
		all_spheres.extend( [ sphere((comb * flip).multiply_vec4(v).xyz, r) for (v,r) in zip(wing_offset, wing_radii) ] ) # Left wing

		return all_spheres

	def get_orientation_matrix(self):
		return mat4.rotateX(self.euler_rotation.x) * mat4.rotateY(self.euler_rotation.y) * mat4.rotateZ(self.euler_rotation.z)
	
	def apply_acceleration(self, accel):
		self.velocity = vec3.clamp(self.velocity + accel, self.min_velocity, self.max_velocity)
	
	def take_damage(self, damage):
		self.health -= damage
		#self.score -= 100
		
	def update(self, scene, controller):
		
		if self.lose or self.win: self.gameover += 1
		
		if self.dead:
			self.explode_time += 0.5
		# }
		
		if not self.dead:

			dx = 0
			dy = 0
			dz = 0
			firebutton = False

			# Controls for Joystick
			#
			if self.joystick_count:
				dx = self.joystick.get_axis( 0 )
				dy = self.joystick.get_axis( 1 )
				firebutton = self.joystick.get_button( 0 )  

			# Controls for keyboard
			# 
			dx = controller.x_axis()
			dy = controller.y_axis()
			firebutton = controller.key_pressed(C_TRIGGER)
			# if pressed[K_LEFT] and not pressed[K_RIGHT] :	dx = -1.0
			# if pressed[K_RIGHT] and not pressed[K_LEFT] :	dx =  1.0
			# if pressed[K_UP] and not pressed[K_DOWN]:		dy = -1.0
			# if pressed[K_DOWN] and not pressed[K_UP]:		dy =  1.0
			# if pressed[K_f] and not pressed[K_b]:			dz = -1.0
			# if pressed[K_b] and not pressed[K_f]:			dz =  1.0
			# firebutton = firebutton or pressed[K_SPACE]
			
			
			# FUCK SAKE IM SICK OF HOLDING BUTTON DOWN!
			# 
			dz = -1.0



			# Apply dampening effect
			# 
			self.velocity = self.velocity.scale(1-self.dampening)

			# Change the velocity by applying acceleration
			#
			controls = vec3([dx, dy, dz])
			move_accel = self.acceleration * controls
			self.apply_acceleration(move_accel)

			# Update position
			#
			self.position = self.position + self.velocity

			
			if self.autopilot:
				# this is slightly hairy
				# but otherwise, you can win and then still crash...
				self.autopilot.update({'asteroid_field' : scene['asteroid_field']}, None)
				self.position = self.autopilot.position
				self.velocity = self.autopilot.velocity
			# }
			
			
			# Update euler_rotation
			# 
			self.euler_rotation = vec3([
				self.velocity.y * math.pi/8,
				-self.velocity.x * math.pi/16,
				-self.velocity.x * math.pi/8])
			

			self.end = max(self.position.z - scene['asteroid_field'].zlimit, 0)
			
			# Colision detection
			#
			ship_broad_sphere = sphere(self.position, 4)
			ship_spheres = self.get_sphere_list()
			# hacky: we cant die on autopilot
			if any( ss.sphere_intersection(a) <=0 for ss in ship_spheres for a in scene["asteroid_field"].get_asteroid_collisions(ship_broad_sphere)) and not self.autopilot:
				Assets.get_sound(tag=("explosion"+str(randint(1,5)))).play()
				#gameover
				self.dead = True
				#return

			#Heath check
			
			if self.health <= 0:
				Assets.get_sound(tag=("explosion"+str(randint(1,5)))).play()
				self.dead = True
				#return
			
			if not self.win and scene['enemy_ship'].dead:
				self.autopilot = EnemyShip()
				self.autopilot.position = self.position
				self.autopilot.velocity = self.velocity
				self.win = True
			# }
			
			if not self.lose and scene['enemy_ship'].win:
				self.lose = True
				# you lose the bounty if enemy escapes
				self.score -= 1000
			# }
			
			if not self.lose and self.dead:
				self.lose = True
				# you lose the bounty if you die
				self.score -= 1000
			# }
			
			# Update Bullets
			#
			if not self.autopilot and firebutton == 1:
				if not self.fired and self.cooldown <= 0:
					Assets.get_sound(tag="laser").play()
					rotate = self.get_orientation_matrix()
					bullet_direction = (rotate.multiply_vec4(vec4([0,0,-1,0])).xyz).unit()
					bullet_offset = rotate.multiply_vec4(vec4([0.75,0,0,0])).xyz
					scene["bullet_collection"].add_bullet(self.position + bullet_offset, bullet_direction, self.velocity )
					scene["bullet_collection"].add_bullet(self.position - bullet_offset, bullet_direction, self.velocity )
					self.cooldown = 5
					#self.score -= 1
					self.shots_fired += 1
				self.fired = True
			else:
				self.fired = False
			self.cooldown -= 1


		# Keep track of enemy
		#
		self.enemy_position = scene["enemy_ship"].position

		# Keep track of active mines
		#
		self.mine_positions = scene["mine_collection"].mine_list


	def draw(self, gl, proj, view):
		# Set up matricies
		#
		model = mat4.rotateY(math.pi) * mat4.scale(0.2,0.2,0.2)
		rotation = self.get_orientation_matrix()
		position = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * position * rotation * model

		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="ship")
		prog = Assets.get_shader(tag="ship")

		# Render
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		
		gl.glUniform1f(gl.glGetUniformLocation(prog, "explode_time"), self.explode_time)
		if self.explode_time > 0.0:
			gl.glUniform3f(gl.glGetUniformLocation(prog, "color"), 1, 0.333, 1)
		else:
			gl.glUniform3f(gl.glGetUniformLocation(prog, "color"), 0.333, 1, 1)
		# }
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


	def draw_ascii(self, ascii_r, proj, view):
		ascii_r.draw_text(ascii.wordart(('LEVEL: '+str(self.level)), 'small'), color = (0.333, 1, 1), screenorigin = (0.0, 0.99), textorigin = (0.0, 1.0))
		ascii_r.draw_text(ascii.wordart(('SCORE: '+str(self.score)), 'small'), color = (0.333, 1, 1), screenorigin = (0.0, 0.99), textorigin = (0.0, 1.0), pos=(0,-5))
		ascii_r.draw_text(ascii.wordart(('END: '+str(self.end)), 'small'), color = (0.333, 1, 1), screenorigin = (0.0, 0.99), textorigin = (0.0, 1.0), pos=(0,-10))
		
		if not self.dead:
			# Retical for enemy ship HACKY
			#
			if self.enemy_position.z < self.position.z:
				ship_on_screen = (proj * view).multiply_vec4(vec4.from_vec3(self.enemy_position, 1)).vec3()
				ship_ascii_pos = vec3.clamp((ship_on_screen + vec3([1,1,1])).scale(0.5), vec3([0,0,0]), vec3([1,1,1]))
				ascii_r.draw_text("X--\0\0\0\0--X\n|\0\0\0\0\0\0\0\0|\n\n\0\0\0\0\0\0\0\0\0\0\n\n\0\0\0\0\0\0\0\0\0\0\n\n|\0\0\0\0\0\0\0\0|\nX--\0\0\0\0--X", color = (1, 0.333, 1), screenorigin = (ship_ascii_pos.x,ship_ascii_pos.y), textorigin = (0.5, 0.5))

			# Retical for mines
			#
			#for m in self.mine_positions:
			#	mine_on_screen = (proj * view).multiply_vec4(vec4.from_vec3(m.position, 1)).vec3()
			#	mine_ascii_pos = vec3.clamp((mine_on_screen + vec3([1,1,1])).scale(0.5), vec3([0,0,0]), vec3([1,1,1]))
			#	ascii_r.draw_text("X\0X\n\0X\0X\0\n\n\0X\0\n\0X\0X\0\nX\0X", color = (1, 0.333, 1), screenorigin = (mine_ascii_pos.x,mine_ascii_pos.y), textorigin = (0.5, 0.5))

			# Retical for aiming
			# 
			rotate = self.get_orientation_matrix()
			bullet_direction = (rotate.multiply_vec4(vec4([0,0,-1,0])).xyz).unit()
			t = ray_plane_intersection( (self.position, bullet_direction), (vec3([0,0,1]), self.enemy_position.z) )
			if t:
				shoot_pos = self.position + bullet_direction.scale(t)

				shoot_on_screen = (proj * view).multiply_vec4(vec4.from_vec3(shoot_pos, 1)).vec3()
				shoot_ascii_pos = (shoot_on_screen + vec3([1,1,1])).scale(0.5)
				ascii_r.draw_text("\0\0|\0\0|\0\0\n\0\0|\0\0|\0\0\n==#==#==\n\0\0|\0\0|\0\0\n\0\0|\0\0|\0\0", color = (0.333, 1, 1), screenorigin = (shoot_ascii_pos.x,shoot_ascii_pos.y), textorigin = (0.5, 0.5))

















class MineCollection(SceneObject):
	"""docstring for BulletCollection"""
	def __init__(self):
		super(MineCollection, self).__init__()
		self.mine_list = []
	
	def update(self, scene, controller):
		ship_z = scene["ship"].get_position().z
		self.mine_list = [b for b in self.mine_list if b.position.z < ship_z + 5]
		for b in self.mine_list:
			b.update(scene, controller)
			

	def draw(self, gl, proj, view, _cache = {}):
		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="mine")
		inst_vbo = Assets.get_inst_vbo(tag="mine")
		prog = Assets.get_shader(tag="mine")

		# Load geometry, shader and projection once
		#
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		# explode time instanced vbo
		vbo_explode_time = _cache.get('vbo_explode_time', None)
		if not vbo_explode_time:
			vbo_explode_time = GLuint(0)
			gl.glGenBuffers(1, vbo_explode_time)
			_cache['vbo_explode_time'] = vbo_explode_time
		# }
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_explode_time)
		gl.glEnableVertexAttribArray(7)
		gl.glVertexAttribPointer(7, 1, GL_FLOAT, GL_FALSE, 0, 0)
		gl.glVertexAttribDivisor(7, 1)
		
		# Create and buffer the instance data
		# 
		mv_array = []
		et_array = []
		sphere_mv_array = []
		model = mat4.scale(0.5,0.5,0.5)

		for m in self.mine_list:
			# Set up matricies
			#
			position = mat4.translate(m.position.x, m.position.y, m.position.z)
			mv = (view * position * model).transpose()
			mv_array.extend(mv.flatten())
			
			et_array.append(m.explode_time)
			
			scale = mat4.scale(m.explosion_radius, m.explosion_radius, m.explosion_radius)
			mv = (view * position * scale).transpose()
			sphere_mv_array.extend(mv.flatten())

		mv_c_array = pygloo.c_array(GLfloat, mv_array)
		gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
		gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_explode_time)
		gl.glBufferData(GL_ARRAY_BUFFER, len(et_array) * 4, pygloo.c_array(GLfloat, et_array), GL_STREAM_DRAW)
		
		# Render Mines
		# 	
		gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, len(self.mine_list))


		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="minesphere")
		inst_vbo = Assets.get_inst_vbo(tag="minesphere")

		# Load geometry, shader and projection once
		#
		gl.glBindVertexArray(vao)

		mv_c_array = pygloo.c_array(GLfloat, sphere_mv_array)
		gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
		gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )

		# Render Mine spheres
		# 	
		gl.glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		#gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, len(self.mine_list))
		gl.glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


	def add_mine(self, position, velocity):
		# print "ADDED MINE!!!"
		self.mine_list.append(Mine(position, velocity=velocity))

	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for a in self.mine_list]

class Mine(object):
	"""docstring for Mine"""

	dampening = 0.01
	radius = 1.0

	def __init__(self, position, explosion_radius_growth = 0.1, max_explosion_radius = 3, velocity=vec3([0,0,0])):
		super(Mine, self).__init__()

		self.position = position
		self.velocity = velocity
		self.explosion_radius_growth = explosion_radius_growth
		self.max_explosion_radius = max_explosion_radius
		self.explosion_radius = 0.1
		self.exploded = False
		self.explode_time = 0.0

	def get_sphere(self):
		return sphere(self.position, Mine.radius)

	
	def update(self, scene, controller):

		controls = vec3([0,0,0])
		ship = scene["ship"]
		
		if self.exploded:
			self.explode_time += 0.5
		# }
		
		if not self.exploded:
			# Increase explosion radius
			# 
			self.explosion_radius = min(self.explosion_radius + self.explosion_radius_growth, self.max_explosion_radius)

			# Check if ship is within our lock-on radius
			# 
			toShip = ship.position - self.position
			if toShip.mag() < self.explosion_radius + 5: #Arbiotrary scaleing shit, no need to worry
				if any(sphere(self.position, self.explosion_radius).sphere_intersection(ss) <= 0 for ss in ship.get_sphere_list()):
					ship.take_damage(10)
					Assets.get_sound(tag="hitbymine").play()
					self.exploded = True
					self.velocity = ship.velocity
		# }

		# Apply dampening effect
		# 
		self.velocity = self.velocity.scale(1-Mine.dampening)

		# Update position
		#
		self.position = self.position + self.velocity













_default_movement = lambda time: vec3 ([	math.sin((2*math.pi) * (time / 132.0) ) * 0.1,
											math.sin((2*math.pi) * (time / 233.0) ) * 0.1, -1 ])

def _generate_enemy(level):

	difficulty = (level-1)//3 + 1

	health  = (difficulty + 1) * 40

	mine_drop_rate = 128 / difficulty

	return EnemyShip(health, mine_drop_rate, _default_movement)




class EnemyShip(SceneObject):

	"""docstring for EnemyShip"""
	def __init__(self,h=1, mdr=-1, m=_default_movement):
		super(EnemyShip, self).__init__()
		# Constants
		x_speed = 2
		y_speed = 2
		z_speed = 2
		self.max_velocity = vec3([x_speed, y_speed, -z_speed])
		self.min_velocity = vec3([-x_speed, -y_speed, -z_speed])
		self.acceleration = vec3([0.15, 0.15, 0])
		self.dampening = 0.01

		self.x_period = 132.0
		self.y_period = 233.0

		# Fields
		self.position = vec3([0, 0, -50])
		self.velocity = vec3([0, 0, -2.0])
		self.euler_rotation = vec3([0,0,0])
		self.health = h
		self.mine_drop_rate = mdr
		self.mine_cooldown = mdr
		self.movement_function = m
		self.dead = False
		self.tick_time = 0
		self.win = False
		
		self.explode_time = 0.0 # how exploded are we?
		
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 3, 6])
		cam_Xrot = -math.pi / 9
		ship_pos = vec3([self.position.x, self.position.y, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			mat4.rotateX(cam_Xrot) *
			mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z)).inverse()

	# Spheres suited to ship model
	# 	approx sphere 0,0,0 radius 3
	def get_sphere_list(self):
		#Cheapp TODO 
		all_spheres = [sphere(self.position + vec3([0, 0, 0]), 2.5)
			# ,sphere(self.position + self.velocity.scale(10), self.velocity.mag() * 10 + 1)
			]
		return all_spheres

	def get_orientation_matrix(self):
		return mat4.rotateX(self.euler_rotation.x) * mat4.rotateY(self.euler_rotation.y) * mat4.rotateZ(self.euler_rotation.z)
	
	def apply_acceleration(self, accel):
		self.velocity = vec3.clamp(self.velocity + accel, self.min_velocity, self.max_velocity)
		
	def take_damage(self, damage):
		self.health -= damage
	
	def update(self, scene, controller):
		
		# controller can be None !!!
		
		if self.dead:
			self.explode_time += 0.5
		# }
		
		if controller and controller.key_pressed(K_w):
			self.health = 0
		# }
		
		if not self.dead:
			#Heath check
			if self.health <= 0:
				Assets.get_sound(tag=("explosion"+str(randint(1,5)))).play()
				self.dead = True
				return
				controls = vec3([0,0,0])

			dx = 0
			dy = 0

			# if pressed[K_LEFT] and not pressed[K_RIGHT] :	dx = -1.0
			# if pressed[K_RIGHT] and not pressed[K_LEFT] :	dx =  1.0
			# if pressed[K_UP] and not pressed[K_DOWN]:		dy = -1.0
			# if pressed[K_DOWN] and not pressed[K_UP]:		dy =  1.0

			if (controller and controller.key_pressed(K_m)) or (self.mine_cooldown < 0 and self.mine_drop_rate > 0):
				Assets.get_sound("minedrop").play()
				scene["mine_collection"].add_mine(self.position, self.velocity)
				self.mine_cooldown = self.mine_drop_rate

			self.mine_cooldown -= 1


			controls = vec3([dx, dy, 0])

			# Look ahead 10 ticks for astroid sphere subset
			# 
			look_ahead = sphere(self.position + self.velocity.scale(10), self.velocity.mag() * 10 + 1)
			spheres_ahead = scene["asteroid_field"].get_asteroid_collisions(look_ahead)

			# Work out if the current course is not going to be appropriate
			# 
			if any( s.ray_intersection((self.position, self.velocity)) >= 0 for s in spheres_ahead ):
				# Do some random raycasts and record the one that is most appropriate
				# 
				min_ray = vec3([0,0,-1])		# basis for most minimal change
				max_dis = 0						# maximum distance to an asteroid the ray
				min_change = 1					# how much this ray is from the original ray
				best_accel_ray = min_ray		# the current best trajectory

				# 10 seems like a good number
				for _ in range(10):
					# Come up with possible trajectory ray in terms of controls
					#
					accel_ray = vec3([2*(random()-0.5), 2*(random()-0.5), -1])
					
					# Cast a ray 10 ticks ahead and see what it hits
					#
					ray = accel_ray.mul(self.acceleration).scale(10)
					ray = vec3([accel_ray.x * self.acceleration.x, accel_ray.y * self.acceleration.y, 10 * self.max_velocity.z])
					distances = [d for d in [s.ray_intersection((self.position, ray)) for s in spheres_ahead] if d > 0]
					
					# If we find a collision and we are still trying to find a ray that doesn't collide
					# 
					if distances:
						if max_dis >= 0:
							dis = min(distances)
							if dis > max_dis:
								max_dis = dis
								best_accel_ray = accel_ray

					# If this ray doesn't collide 
					# 
					else:
						max_dis = -1
						change = 1-min_ray.dot(accel_ray.unit())
						if change < min_change:
							min_change = change
							best_accel_ray = accel_ray

				controls = best_accel_ray

				

			# Carry on with current course (with slight modifications)
			#
			else :
				controls = self.movement_function(self.tick_time)
				# controls = vec3 ([
				# 	math.sin((2*math.pi) * (self.tick_time / self.x_period) ) * 0.1,
				# 	math.sin((2*math.pi) * (self.tick_time / self.y_period) ) * 0.1,
				# 	-1
				# 	])

			# Apply dampening effect
			# 
			self.velocity = self.velocity.scale(1-self.dampening)
			
			# Change the velocity by applying acceleration
			#
			move_accel = self.acceleration * controls
			self.apply_acceleration(move_accel)

			# are we winning? (do we even exist?)
			if (self.position.z < scene['asteroid_field'].zlimit - 100) and (scene.get('enemy_ship', None) is not None):
				self.velocity = vec3((0, 0, -5))
				# have we won?
				if self.position.z < scene['asteroid_field'].zlimit - 1000:
					if not self.win:
						self.win = True
					# }
				# }
			# }
			

			# Update euler_rotation
			# 
			self.euler_rotation = vec3([
				self.velocity.y * math.pi/8,
				-self.velocity.x * math.pi/16,
				-self.velocity.x * math.pi/8])

			self.tick_time += 1
		
		
		# Update position, even if dead
		#
		self.position = self.position + self.velocity.scale(1 if not self.dead else 0.75)



	def draw(self, gl, proj, view):
		# Set up matricies
		#
		model = mat4.rotateY(math.pi) * mat4.scale(0.4,0.4,0.4)
		rotation = self.get_orientation_matrix()
		position = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * position * rotation * model

		# Retreive model and shader
		#
		vao, vao_size = Assets.get_geometry(tag="enemyship")
		prog = Assets.get_shader(tag="ship")

		# Render
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		
		gl.glUniform1f(gl.glGetUniformLocation(prog, "explode_time"), self.explode_time)
		if self.explode_time > 0.0:
			gl.glUniform3f(gl.glGetUniformLocation(prog, "color"), 1, 0.333, 1)
		else:
			gl.glUniform3f(gl.glGetUniformLocation(prog, "color"), 0.333, 1, 1)
		# }
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


















class AsteroidField(SceneObject):

	"""docstring for AsteroidField"""
	def __init__(self):
		super(AsteroidField, self).__init__()
		self.asteroid_slice_list = []
		self.asteroid_sphere_list = {}
		for i in xrange(1,8):
			self.asteroid_sphere_list[i] = Assets.get_geometry_sphere(tag="asteroid{num}".format(num=i))

		self.next_slice_distance = 400 # How far away the next chunk should be generated
		self.last_slice_distance = -100 # The last min of the chunk
		self.zlimit = -10000
		
	def update(self, scene, controller):
		
		# Trim the astroid slices behind the ship
		# 
		sx, sy, sz = scene["ship"].position
		self.asteroid_slice_list = [a for a in self.asteroid_slice_list if a.min_b.z < sz + 5 ]


		# Generate level ahead
		# 
		width = 150
		depth = 20

		# If the last slice is closer than next_slice_distance away from the ship
		# and we havent got to the end of the asteroids
		if (self.last_slice_distance > sz - self.next_slice_distance) and (self.last_slice_distance > self.zlimit):
			min_b = vec3([sx-width, sy-width, self.last_slice_distance-depth ])
			max_b = vec3([sx+width, sy+width, self.last_slice_distance ])

			self.asteroid_slice_list.append(AsteroidSlice(self.asteroid_sphere_list, min_b, max_b))
			self.last_slice_distance = min_b.z

			# print "AST COUNT", len([a for ast_slice in self.asteroid_slice_list for a in ast_slice.get_asteroids()])
		
		
		# Update the astroids slices
		# 
		# for a in self.asteroid_slice_list:
		# 	a.update(scene, controller)
	

	def draw(self, gl, proj, view):
		prog = Assets.get_shader(tag="asteroid")
		gl.glUseProgram(prog)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))


		model = mat4.scale(2,2,2)

		for i in xrange(1, 8):

			# Retreive model and shader, Load geometry once
			#
			vao, vao_size = Assets.get_geometry(tag="asteroid{num}".format(num=i))
			inst_vbo = Assets.get_inst_vbo(tag="asteroid{num}".format(num=i))
			gl.glBindVertexArray(vao)

			# Create buffer
			# 
			mv_array = []


			# Create the instance data
			# 
			count = 0
			for a in [a for ast_slice in self.asteroid_slice_list for a in ast_slice.get_asteroids() if a.ast_num == i]:

				# Set up matricies
				#
				rotation = mat4.rotateFromQuat(a.orientation)
				scale = mat4.scale(a.size,a.size,a.size)
				position = mat4.translate(a.position.x, a.position.y, a.position.z)
				mv = (view * position * rotation * scale * model).transpose()
				mv_array.extend(mv.flatten())
				count += 1


			# Upload the instace data
			# 
			mv_c_array = pygloo.c_array(GLfloat, mv_array)
			gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
			gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )

			# Render
			# 	
			gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, count)


	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for ast_slice in self.asteroid_slice_list for a in ast_slice.get_asteroids()]


	# Returns a list of sphere that interset with the given sphere
	# Makes some assumptions based on asteroid slicing
	# 
	def get_asteroid_collisions(self, sph):
		min_z = sph.center.z - sph.radius
		max_z = sph.center.z + sph.radius

		return [s for a_slice in self.asteroid_slice_list for s in a_slice.get_asteroid_collisions(sph)
			if a_slice.min_b.z < max_z and a_slice.max_b.z > min_z]
		# return [s for a_slice in self.asteroid_slice_list for s in a_slice.get_sphere_list()
		# 	if a_slice.min_b.z < max_z and a_slice.max_b.z > min_z and s]



# Best thing since sliced bread
# 
class AsteroidSlice(object):
	"""docstring for AsteroidSlice, the best thing since sliced bread"""
	def __init__(self, ast_sphere_list, min_b, max_b):
		super(AsteroidSlice, self).__init__()

		# Set up the size
		#
		self.min_b = vec3(min_b)
		self.max_b = vec3(max_b)
		self.size = vec3(self.max_b - self.min_b)


		# Generate asterois
		# 
		self.asteroid_list = []
		self._generate_asteroids(ast_sphere_list)

	def _generate_asteroids(self, ast_sphere_list):
		num_ast = abs(self.size.x * self.size.y * self.size.z) / 100000

		for i in range(int(num_ast)):
			p = vec3([random(), random(), random()]).mul(self.size) + self.min_b
			if random() > 0.5:
				r = vec3.random().scale( random() * math.pi * 0.02)
				s = random() * 4 + 0.1
				n = randrange(1, 8)
				a = Asteroid(p, rot=r, size=s, ast_num=n, model_sphere=ast_sphere_list[n] )
				self.asteroid_list.append(a)
	
	def get_asteroids(self):
		return self.asteroid_list

	def get_sphere_list(self):
		return [a.get_sphere() for a in self.asteroid_list]


	def get_asteroid_collisions(self, sph):
		return [s for s in self.get_sphere_list() if s.sphere_intersection(sph) <= 0]

	def update(self, scene, controller):
		map(lambda x : x.update(scene, controller), self.asteroid_list)



class Asteroid(object):
	"""docstring for Asteroid"""
	def __init__(self, pos, rot=(0,0,0), size=1, ast_num=1, model_sphere=sphere([0,0,0],0)):
		super(Asteroid, self).__init__()
		self.position = vec3(pos) 
		self.rotation = vec3(rot)
		self.orientation = quat.axisangle(vec3.random(), 2 * math.pi * random()).unit()
		self.size = size
		self.ast_num = ast_num
		self.sph = sphere(self.position, model_sphere.radius * self.size * 1.5) #TODO remove artbitrary scaling
	
	def update(self, scene, controller):
		if (self.rotation.mag() > 0):
			self.orientation = self.orientation.multiply(quat.axisangle(self.rotation, self.rotation.mag()).unit())


	def get_sphere(self):
		return self.sph
	
	













# Utility
# 

# class Timer(object):
# 	"""docstring for Timer"""
# 	def __init__(self, arg):
# 		super(Timer, self).__init__()
# 		self.arg = arg

# 	def update(self, scene, pressed):
		
