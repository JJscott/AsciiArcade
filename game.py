
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

# State stuff
# 
from highscore import HighScoreState

# Other stuff
# 
from GL_assets import *
from collections import defaultdict
import pygame
import ascii


##
##
Assets = GL_assets()


class GameState(object):
	"""GameState"""
	def __init__(self):
		super(GameState, self).__init__()
		self.reset()
		self.show_spheres = False
			

	def reset(self):
		self.scene = {}
		self.scene["bullet_collection"] = BulletCollection()
		self.scene["ship"] = Ship()
		self.scene["enemy_ship"] = EnemyShip()
		self.scene["asteroid_field"] = AsteroidField()
	

	# Game logic
	#
	def tick(self, pressed):

		# GameLogic
		# 
		if pressed[K_s]:
			self.show_spheres = not self.show_spheres

		# Update all objects in the scene
		#
		scene_itr = self.scene.copy()
		for (_, obj) in scene_itr.items():
			obj.update(self.scene, pressed)

		# Process results of update
		#
		if self.scene["ship"].dead:
			#HACKY HACKY RESET
			if pressed[K_SPACE]:
				return HighScoreState()
				# self.reset()
						

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


		if self.scene["ship"].dead and ascii_r:
			art = ascii.wordart('PRESS SPACE\nTO GO TO\nHIGHSCORE', 'big')

			# temp
			ascii_r.draw_text(art, color = (0.333, 1, 1), screenorigin = (0.5,0.5), textorigin = (0.5, 0.5), align = 'c')
			


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














class BulletCollection(object):
	"""docstring for BulletCollection"""
	def __init__(self):
		super(BulletCollection, self).__init__()
		self.bullet_list = []
	
	def update(self, scene, pressed):
		ship_z = scene["ship"].get_position().z
		self.bullet_list = [b for b in self.bullet_list if b.power > 0 ] # TODO cleanup / removes if it gets 100 away from the ship
		for b in self.bullet_list:
			b.update(scene, pressed)
			

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
	
	def get_position(self):
		return self.position

	def get_sphere(self):
		return sphere(self.position, 0.25)
	
	def update(self, scene, pressed):
		self.position = self.position + self.velocity
		self.power -= 1

















class Ship(object):

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

		# Feilds
		self.position = vec3([0, 0, 0])
		self.velocity = vec3([0, 0, -2.0])
		self.euler_rotation = vec3([0,0,0])
		self.dead = False
		self.fired = False
		self.cooldown = 0


		# Get joystick controls
		self.joystick_count = pygame.joystick.get_count()
		for i in range(self.joystick_count):
			self.joystick = pygame.joystick.Joystick(i)
			self.joystick.init()
		
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 0, 6])
		cam_Xrot = -math.pi / 9
		ship_pos = vec3([self.position.x, self.position.y, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			mat4.rotateX(cam_Xrot) *
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
		return mat4.rotateX(self.euler_rotation.x) * mat4.rotateZ(self.euler_rotation.z)

	def apply_acceleration(self, accel):
		self.velocity = vec3.clamp(self.velocity + accel, self.min_velocity, self.max_velocity)
	
		
	def update(self, scene, pressed):

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
			if pressed[K_LEFT] and not pressed[K_RIGHT] :	dx = -1.0
			if pressed[K_RIGHT] and not pressed[K_LEFT] :	dx =  1.0
			if pressed[K_UP] and not pressed[K_DOWN]:		dy = -1.0
			if pressed[K_DOWN] and not pressed[K_UP]:		dy =  1.0
			if pressed[K_f] and not pressed[K_b]:			dz = -1.0
			if pressed[K_b] and not pressed[K_f]:			dz =  1.0
			firebutton = firebutton or pressed[K_SPACE]

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


			
			# Update euler_rotation TODO update
			if abs(dx) >= 0.01 : self.euler_rotation.z = -dx * math.pi/8
			if abs(dy) >= 0.01 : self.euler_rotation.x = dy * math.pi/8

			# move_mag = move.mag()
			# if move_mag < 0.01:
			# 	self.euler_rotation.x = 0
			# 	self.euler_rotation.z = 0
			# else:
			# 	if move_mag > 1.0:
			# 		move = move.scale(1/move_mag)
			# 	self.position = self.position + move
			

			# Update foward position
			#
			self.position = self.position + self.velocity
			# forward = vec3([0, 0, self.max_forward_speed])
			# self.position = self.position + forward


			# Colision detection
			#
			ship_broad_sphere = sphere(self.position, 4)
			ship_spheres = self.get_sphere_list()
			if any( ss.sphere_intersection(a) <=0 for ss in ship_spheres for a in scene["asteroid_field"].get_asteroid_collisions(ship_broad_sphere)):
				# self.dead = True
				return


			# Update Bullets
			#
			if firebutton == 1:
				if not self.fired and self.cooldown <= 0:
					rotate = self.get_orientation_matrix()
					bullet_direction = (rotate.multiply_vec4(vec4([0,0,-1,0])).xyz).unit()
					bullet_offset = rotate.multiply_vec4(vec4([0.5,0,0,0])).xyz
					scene["bullet_collection"].add_bullet(self.position + bullet_offset, bullet_direction, self.velocity )
					scene["bullet_collection"].add_bullet(self.position - bullet_offset, bullet_direction, self.velocity )
					self.cooldown = 5
				self.fired = True
			else:
				self.fired = False
			self.cooldown -= 1



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

		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)















class EnemyShip(object):

	"""docstring for EnemyShip"""
	def __init__(self):
		super(EnemyShip, self).__init__()
		# Constants
		x_speed = 2
		y_speed = 2
		z_speed = 2
		self.max_velocity = vec3([x_speed, y_speed, -z_speed])
		self.min_velocity = vec3([-x_speed, -y_speed, -z_speed])
		self.acceleration = vec3([0.15, 0.15, 0])
		self.dampening = 0.01

		# Feilds
		self.position = vec3([0, 0, -10])
		self.velocity = vec3([0, 0, -2.0])
		self.euler_rotation = vec3([0,0,0])
		self.dead = False

		
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 0, 6])
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
			,sphere(self.position + self.velocity.scale(10), self.velocity.mag() * 10 + 1)
			]
		return all_spheres

	def get_orientation_matrix(self):
		return mat4.rotateX(self.euler_rotation.x) * mat4.rotateZ(self.euler_rotation.z)
	
	def apply_acceleration(self, accel):
		self.velocity = vec3.clamp(self.velocity + accel, self.min_velocity, self.max_velocity)
		
	def update(self, scene, pressed):

		if not self.dead:

			controls = vec3([0,0,0])

			dx = 0
			dy = 0

			# if pressed[K_LEFT] and not pressed[K_RIGHT] :	dx = -1.0
			# if pressed[K_RIGHT] and not pressed[K_LEFT] :	dx =  1.0
			# if pressed[K_UP] and not pressed[K_DOWN]:		dy = -1.0
			# if pressed[K_DOWN] and not pressed[K_UP]:		dy =  1.0

			controls = vec3([dx, dy, 0])

			# Look ahead 10 ticks for astroid sphere subset
			# 
			look_ahead = sphere(self.position + self.velocity.scale(10), self.velocity.mag() * 10 + 1)
			spheres_ahead = scene["asteroid_field"].get_asteroid_collisions(look_ahead)

			# Work out if the current course is not going to be appropriate
			# 
			if any( s.ray_intersection((self.position, self.velocity)) >= 0 for s in spheres_ahead ):
				print "OH NO GONNA CRASH!!!!"

				# Do some random raycasts and record the one that is most appropriate
				# 
				min_ray = vec3([0,0,-1])		# basis for most minimal change
				max_dis = 0						# maximum distance to an asteroid the ray
				min_change = 1					# how much this ray is from the original ray
				best_accel_ray = min_ray		# the current best trajectory

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
							print "FOUND A PATH!!!!", accel_ray

				print "Going to go with the new path ", best_accel_ray
				controls = best_accel_ray

				

			# Carry on with current course (with slight modifications)
			#
			else :
				pass

			# Apply dampening effect
			# 
			self.velocity = self.velocity.scale(1-self.dampening)

			# Change the velocity by applying acceleration
			#
			move_accel = self.acceleration * controls
			self.apply_acceleration(move_accel)




			# # Update euler_rotation
			# if abs(dx) >= 0.01 : self.euler_rotation.z = -dx * math.pi/8
			# if abs(dy) >= 0.01 : self.euler_rotation.x = dy * math.pi/8

			# move_mag = move.mag()
			# if move_mag < 0.01:
			# 	self.euler_rotation.x = 0
			# 	self.euler_rotation.z = 0
			# else:
			# 	if move_mag > 1.0:
			# 		move = move.scale(1/move_mag)
			# 	self.position = self.position + move
			

			# # Update foward position
			# #
			# forward = vec3([0, 0, self.forward_speed])
			self.position = self.position + self.velocity



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

		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


















class AsteroidField(object):

	"""docstring for AsteroidField"""
	def __init__(self):
		super(AsteroidField, self).__init__()
		self.asteroid_slice_list = []
		self.asteroid_sphere_list = {}
		for i in xrange(1,8):
			self.asteroid_sphere_list[i] = Assets.get_geometry_sphere(tag="asteroid{num}".format(num=i))

		self.next_slice_distance = 400 # How far away the next chunk should be generated
		self.last_slice_distance = -100 # The last min of the chunk

			
	def update(self, scene, pressed):
		
		# Trim the astroid slices behind the ship
		# 
		sx, sy, sz = scene["ship"].position
		self.asteroid_slice_list = [a for a in self.asteroid_slice_list if a.min_b.z < sz + 5 ]


		# Generate level ahead
		# 
		width = 150
		depth = 20

		# If the last slice is closer than next_slice_distance away from the ship
		if self.last_slice_distance > sz - self.next_slice_distance:
			min_b = vec3([sx-width, sy-width, self.last_slice_distance-depth ])
			max_b = vec3([sx+width, sy+width, self.last_slice_distance ])

			self.asteroid_slice_list.append(AsteroidSlice(self.asteroid_sphere_list, min_b, max_b))
			self.last_slice_distance = min_b.z

			# print "AST COUNT", len([a for ast_slice in self.asteroid_slice_list for a in ast_slice.get_asteroids()])

		# Update the astroids slices
		# 
		# for a in self.asteroid_slice_list:
		# 	a.update(scene, pressed)
	

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

		return [s for as_slice in self.asteroid_slice_list for s in as_slice.get_sphere_list()
			if as_slice.min_b.z < max_z and as_slice.max_b.z > min_z and s.sphere_intersection(sph) <= 0]



# Best thing since sliced bread
# 
class AsteroidSlice(object):
	"""docstring for AsteroidSlice, the best thing since sliced bread"""
	def __init__(self, ast_sphere_list, min_b, max_b):
		super(AsteroidSlice, self).__init__()
		self.min_b = vec3(min_b)
		self.max_b = vec3(max_b)
		self.size = vec3(self.max_b - self.min_b)

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
				a = Asteroid(p, rot=r, size=s, ast_num=n)
				a.sph = ast_sphere_list[n]
				self.asteroid_list.append(a)
	
	def get_asteroids(self):
		return self.asteroid_list

	def get_sphere_list(self):
		return [a.get_sphere() for a in self.asteroid_list]


	# def get_asteroid_collisions(self, sph):
		# Can optmize further
		# 
		# return [a for a in self.asteroid_list if a.sphere_intersection(sphere)]

	def update(self, scene, pressed):
		map(lambda x : x.update(scene, pressed), self.asteroid_list)



class Asteroid(object):
	"""docstring for Asteroid"""
	def __init__(self, pos, rot=(0,0,0), size=1, ast_num=1):
		super(Asteroid, self).__init__()
		self.position = vec3(pos) 
		self.rotation = vec3(rot)
		self.orientation = quat.axisangle(vec3.random(), 2 * math.pi * random()).unit()
		self.size = size
		self.ast_num = ast_num

		self.sph = sphere([0,0,0],0)
	
	def update(self, scene, pressed):
		if (self.rotation.mag() > 0):
			self.orientation = self.orientation.multiply(quat.axisangle(self.rotation, self.rotation.mag()).unit())


	def get_sphere(self):
		return sphere(self.sph.center + self.position, self.sph.radius * self.size * 1.5) #TODO change radius of asteroid
	
	













# Utility
# 

# class Timer(object):
# 	"""docstring for Timer"""
# 	def __init__(self, arg):
# 		super(Timer, self).__init__()
# 		self.arg = arg

# 	def update(self, scene, pressed):
		
