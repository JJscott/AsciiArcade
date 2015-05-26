
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

# Other stuff
# 
from GL_assets import *



class StarsGame(object):
	"""StarsGame"""
	def __init__(self, gl):
		super(StarsGame, self).__init__()

		self.assets = GL_assets()

		# Load geometry
		# 
		self.assets.load_geometry(gl, "bullet",		"Assets/Projectiles/ArrowHead.obj")
		self.assets.load_geometry(gl, "asteroid1",	"Assets/Asteroids/AsteroidT1.obj")
		self.assets.load_geometry(gl, "asteroid2",	"Assets/Asteroids/AsteroidT2.obj")
		self.assets.load_geometry(gl, "asteroid3",	"Assets/Asteroids/AsteroidT3.obj")
		self.assets.load_geometry(gl, "asteroid4",	"Assets/Asteroids/AsteroidT4.obj")
		self.assets.load_geometry(gl, "asteroid5",	"Assets/Asteroids/AsteroidT5.obj")
		self.assets.load_geometry(gl, "ship",		"Assets/Ship/ShipT.obj")

		# Load shader
		# 
		self.assets.load_shader(gl, "bullet",	open("Assets/Shaders/bullet_shader.glsl").read())
		self.assets.load_shader(gl, "asteroid",	open("Assets/Shaders/bullet_shader.glsl").read())
		self.assets.load_shader(gl, "ship",		open("Assets/Shaders/bullet_shader.glsl").read())

		self.reset()

		self.show_spheres = False
			

	def reset(self):
		self.scene = []
		self.ship = Ship()
		self.scene.append(self.ship)
		self.level = AsteroidField((5,5))
		self.scene.append(self.level)
	

	# Game logic
	#
	def tick(self, pressed):

		# GameLogic
		# 
		if pressed[K_s]:
			self.show_spheres = not self.show_spheres

		# Update all objects in the scene
		#
		scene_itr = self.scene[:]
		for obj in scene_itr:
			obj.update(self.scene, pressed)

		# Process results of update
		#
		if self.ship.dead:
			#HACKY HACKY RESET
			if pressed[K_SPACE]:
				self.reset()
						

	# Render logic
	#
	def render(self, gl, w, h):
		zfar = 10000
		znear = 0.1

		# Create view and projection matrix
		#
		proj = mat4.perspectiveProjection(math.pi / 3, float(w)/h, znear, zfar)
		view = self.ship.get_view_matrix().inverse()

		# Render all objects in the scene
		# 
		for obj in self.scene:
			obj.draw(gl, self.assets, proj, view)


		# Debug colliding spheres
		#
		# if self.show_spheres:
		# 	for sph in self.ship.get_sphere_list() + self.ship.bullets.get_sphere_list() + self.level.get_sphere_list():




				
		# ascii needs proj matrix
		return proj
			
	# TODO in Future
	#
	def render_GUI():
		pass
	
	# TODO in Future
	#
	def render_GUI_ascii():
		pass







class BulletCollection(object):
	"""docstring for BulletCollection"""
	def __init__(self, ship):
		super(BulletCollection, self).__init__()
		self.ship = ship
		self.bullet_list = []
	
	def update(self, scene, pressed):
		ship_z = self.ship.get_position().z
		self.bullet_list = [b for b in self.bullet_list if b.get_position().z - ship_z < 100 ] # TODO cleanup / removes if it gets 100 away from the ship
		for b in self.bullet_list:
			b.update(scene, pressed)
			

	def draw(self, gl, assets, proj, view):
		for b in self.bullet_list:
			b.draw(gl, assets, proj, view)
					

	def add_bullet(self, position, speed):
		self.bullet_list.append(Bullet(position, speed))

	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for a in self.asteroid_list]

class Bullet(object):
	"""docstring for Bullet"""
	def __init__(self, pos, ship_speed):
		super(Bullet, self).__init__()
		self.position = pos
		self.speed = 5 * ship_speed

		self.vao = GLuint(0)
		self.vao_size = 0
	
	def get_position(self):
		return self.position

	def get_sphere(self):
		return [sphere(self.position, 0.25)]
	
	def update(self, scene, pressed):
		self.position = self.position + vec3([0, 0, self.speed])
	
	def draw(self, gl, assets, proj, view):

		# Set up matricies
		#
		model = mat4.scale(0.25,0.25,0.25)
		position = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * position * model

		# Retreive model and shader
		#
		vao, vao_size = assets.get_geometry(tag="bullet")
		prog = assets.get_shader(tag="bullet")

		# Render
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)

		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)

	







class Ship(object):

	"""docstring for Ship"""
	def __init__(self):
		super(Ship, self).__init__()
		self.position = vec3([0, 0, 0])
		self.speed = -0.2
		self.dead = False
		self.bullets = BulletCollection(self)
		self.fired = False
		self.cooldown = 0

		self.vao = GLuint(0)
		self.vao_size = 0
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 0, 15])
		cam_Xrot = -math.pi / 6
		ship_pos =  vec3([0, 0, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			mat4.rotateX(cam_Xrot) *
			mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z))

	def get_sphere_list(self):
		return [sphere(self.position, 1)]
	
		
	def update(self, scene, pressed):

		if not self.dead:
			# Update position
			#
			dx = 0
			dy = 0

			if pressed[K_LEFT]:		dx -= 1.0
			if pressed[K_RIGHT]:	dx += 1.0
			if pressed[K_UP]:		dy += 1.0
			if pressed[K_DOWN]:		dy -= 1.0

			move = vec3([dx, dy, 0])

			if move.mag() != 0:
				move = move.unit() * 0.2 # parameterize screen move speed
				nx = max(min(self.position.x + move.x, 5), -5) # parametirze screen bounds?
				ny = max(min(self.position.y + move.y, 4), -4)
				self.position = vec3([nx, ny, self.position.z])
			

			# Move foward
			#
			self.position = self.position + vec3([0, 0, self.speed])
			self.speed *= 1.001


			# Colision detection
			#
			ship_spheres = self.get_sphere_list()

			all_spheres = [af.get_sphere_list() for af in scene if isinstance(af, AsteroidField)]
			if len(all_spheres) > 0:
				ast_field_sphere = all_spheres[0]

				if any( ship_sphere.sphere_intersection(ast_sphere) <=0 for ship_sphere in ship_spheres for ast_sphere in ast_field_sphere ):
					self.dead = True
					pass
							

			# Update target
			#


			# Update Bullets"
			#
			self.bullets.update(scene, pressed)
			if pressed[K_SPACE]:
				if not self.fired and self.cooldown <= 0:
					self.bullets.add_bullet(self.position + vec3([0.5, 0, 0]), self.speed )
					self.bullets.add_bullet(self.position - vec3([0.5, 0, 0]), self.speed )
					self.cooldown = 5
				self.fired = True
			else:
				self.fired = False
			

			# Update cooldown on weapons
			# 
			self.cooldown -= 1

			


	def draw(self, gl, assets, proj, view):
		# Set up matricies
		#
		model = mat4.rotateY(math.pi) * mat4.scale(0.2,0.2,0.2)
		position = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * position * model

		# Retreive model and shader
		#
		vao, vao_size = assets.get_geometry(tag="ship")
		prog = assets.get_shader(tag="ship")

		# Render
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)

		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


		# TODO render firing target
		# 
        
		# Draw bullets
		#
		self.bullets.draw(gl, assets, proj, view)
	










class AsteroidField(object):

	"""docstring for AsteroidField"""
	def __init__(self, (xbound, ybound) ):
		super(AsteroidField, self).__init__()
		self.asteroid_list = []
		for _ in range(50):
			pos = vec3(((random() - 0.5) * 2 * xbound, (random() - 0.5) * 2 * ybound, randrange(-1000, -5)))
			vel = vec3((random()-0.5, random()-0.5, random()-0.5)).unit() * 0.01


			self.asteroid_list.append(Asteroid(pos, vel) )
			
	def update(self, scene, pressed):
		for a in self.asteroid_list:
			a.update(scene, pressed)
	

	def draw(self, gl, assets, proj, view):
		for a in self.asteroid_list:
			a.draw(gl, assets, proj, view)
	


	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for a in self.asteroid_list]


class Asteroid(object):
	"""docstring for Asteroid"""
	def __init__(self, pos, vel=(0,0,0)):
		super(Asteroid, self).__init__()
		self.position = vec3(pos)
		self.velocity = vec3(vel)
		self.orientation = mat4.rotateY(random() * math.pi * 2) * mat4.rotateX(random() * math.pi - math.pi/2)

		self.vao = GLuint(0)
		self.vao_size = 0
	
	def update(self, scene, pressed):
		self.position = self.position + self.velocity
	
	def draw(self, gl, assets, proj, view):
		# Set up matricies
		#
		model = mat4.scale(2,2,2) * self.orientation
		position = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * position * model

		# Retreive model and shader
		#
		vao, vao_size = assets.get_geometry(tag="asteroid1")
		prog = assets.get_shader(tag="asteroid")

		# Render
		# 
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)

		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, pygloo.c_array(GLfloat, mv.flatten()))
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		gl.glDrawArrays(GL_TRIANGLES, 0, vao_size)


	def get_sphere(self):
		return sphere(self.position, 2.0) #TODO change radius of asteroid
	
	