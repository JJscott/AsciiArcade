
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
		self.assets.load_inst_geometry(gl, 	"bullet",		"Assets/Projectiles/ArrowHead.obj")
		self.assets.load_geometry(gl, 		"asteroid1",	"Assets/Asteroids/AsteroidT1.obj", center=True)
		self.assets.load_geometry(gl, 		"asteroid2",	"Assets/Asteroids/AsteroidT2.obj", center=True)
		self.assets.load_geometry(gl, 		"asteroid3",	"Assets/Asteroids/AsteroidT3.obj", center=True)
		self.assets.load_geometry(gl, 		"asteroid4",	"Assets/Asteroids/AsteroidT4.obj", center=True)
		self.assets.load_geometry(gl, 		"asteroid5",	"Assets/Asteroids/AsteroidT5.obj", center=True)
		self.assets.load_geometry(gl, 		"ship",			"Assets/Ship/Ship2.obj")
		self.assets.load_inst_geometry(gl, 	"sphere",		"Assets/Debug/Sphere/sphere.obj")

		# Load shader
		# 
		self.assets.load_shader(gl, "bullet",	open("Assets/Shaders/default_shader.glsl").read())
		self.assets.load_shader(gl, "asteroid",	open("Assets/Shaders/default_shader.glsl").read())
		self.assets.load_shader(gl, "ship",		open("Assets/Shaders/default_shader.glsl").read())
		self.assets.load_shader(gl, "sphere",	open("Assets/Shaders/red_sphere_shader.glsl").read())

		self.reset()

		self.show_spheres = False
			

	def reset(self):
		self.scene = {}
		self.scene["bullet_collection"] = BulletCollection()
		self.scene["ship"] = Ship()
		self.scene["asteroid_field"] = AsteroidField((5,5))
	

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
				self.reset()
						

	# Render logic
	#
	def render(self, gl, w, h):
		zfar = 10000
		znear = 0.1

		# Create view and projection matrix
		#
		proj = mat4.perspectiveProjection(math.pi / 3, float(w)/h, znear, zfar)
		view = self.scene["ship"].get_view_matrix().inverse()

		# Render all objects in the scene
		# 
		for (_, obj) in self.scene.items():
			obj.draw(gl, self.assets, proj, view)


		# Debug colliding spheres
		#
		if self.show_spheres:
			all_spheres = []
			all_spheres.extend( self.scene["ship"].get_sphere_list() )
			all_spheres.extend( self.scene["bullet_collection"].get_sphere_list() )
			all_spheres.extend( self.scene["asteroid_field"].get_sphere_list() )

			if len(all_spheres) > 0 :

				# Retreive model and shader
				#
				vao, vao_size = self.assets.get_geometry(tag="sphere")
				inst_vbo = self.assets.get_inst_vbo(tag="sphere")
				prog = self.assets.get_shader(tag="sphere")

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
	def __init__(self):
		super(BulletCollection, self).__init__()
		self.bullet_list = []
	
	def update(self, scene, pressed):
		ship_z = scene["ship"].get_position().z
		self.bullet_list = [b for b in self.bullet_list if b.power > 0 ] # TODO cleanup / removes if it gets 100 away from the ship
		for b in self.bullet_list:
			b.update(scene, pressed)
			

	def draw(self, gl, assets, proj, view):
		# Retreive model and shader
		#
		vao, vao_size = assets.get_geometry(tag="bullet")
		inst_vbo = assets.get_inst_vbo(tag="bullet")
		prog = assets.get_shader(tag="bullet")

		# Load geometry, shader and projection once
		#
		gl.glUseProgram(prog)
		gl.glBindVertexArray(vao)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, pygloo.c_array(GLfloat, proj.flatten()))

		# Create and buffer the instance data
		# 
		mv_array = []
		model = mat4.scale(0.25,0.25,0.25)

		for b in self.bullet_list:
			# Set up matricies
			#
			position = mat4.translate(b.position.x, b.position.y, b.position.z)
			mv = view * position * model
			mv_array.extend(mv.flatten())

		mv_c_array = pygloo.c_array(GLfloat, mv_array)
		gl.glBindBuffer( GL_ARRAY_BUFFER, inst_vbo )
		gl.glBufferData( GL_ARRAY_BUFFER, sizeof(mv_c_array), mv_c_array, GL_STREAM_DRAW )

		# Render
		# 	
		gl.glDrawArraysInstanced(GL_TRIANGLES, 0, vao_size, len(self.bullet_list))


	def add_bullet(self, position, speed):
		self.bullet_list.append(Bullet(position, speed))

	def get_sphere_list(self):
		# Need t return a generator for all the asteroids
		return [a.get_sphere() for a in self.bullet_list]

class Bullet(object):
	"""docstring for Bullet"""
	def __init__(self, pos, ship_speed):
		super(Bullet, self).__init__()
		self.position = pos
		self.speed = 5 * ship_speed
		self.power = 60				# Live for 500 "ticks"
	
	def get_position(self):
		return self.position

	def get_sphere(self):
		return sphere(self.position, 0.25)
	
	def update(self, scene, pressed):
		self.position = self.position + vec3([0, 0, self.speed])
		self.power -= 1












class Ship(object):

	"""docstring for Ship"""
	def __init__(self):
		super(Ship, self).__init__()
		self.position = vec3([0, 0, 0])
		self.speed = -0.2
		self.dead = False
		self.fired = False
		self.cooldown = 0
	
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		cam_pos = vec3([0, 0, 6])
		cam_Xrot = -math.pi / 9
		# cam_Xrot = -math.pi / 6
		# cam_Xrot = -math.pi / 3
		# ship_pos =  vec3([0, 0, self.position.z])
		ship_pos = vec3([self.position.x * 0.9, self.position.y * 0.9, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			mat4.rotateX(cam_Xrot) *
			mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z))

	def get_sphere_list(self):
		all_spheres = [sphere(self.position + vec3([0, 0, -1.0]), 0.5)]
		wing_offset = [ 
			(0.5, 0, 0),
			(1.3, 0, 0.2),
			(1.8, 0, 0.5) ]
		wing_radii = [0.6, 0.3, 0.2]

		pos = mat4.translate(self.position.x, self.position.y, self.position.z)

		all_spheres.extend( [ sphere(pos.multiply_vec4(vec4([ x, y, z, 1])).xyz, r) for ((x, y, z),r) in zip(wing_offset, wing_radii) ] ) # Right wing
		all_spheres.extend( [ sphere(pos.multiply_vec4(vec4([-x, y, z, 1])).xyz, r) for ((x, y, z),r) in zip(wing_offset, wing_radii) ] ) # Left wing

		return all_spheres
	
		
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
			if any( ship_sphere.sphere_intersection(ast_sphere) <=0 for ship_sphere in ship_spheres for ast_sphere in scene["asteroid_field"].get_sphere_list() ):
				self.dead = True
				# pass
							

			# Update target
			#


			# Update Bullets"
			#
			if pressed[K_SPACE]:
				if not self.fired and self.cooldown <= 0:
					scene["bullet_collection"].add_bullet(self.position + vec3([0.5, 0, 0]), self.speed )
					scene["bullet_collection"].add_bullet(self.position - vec3([0.5, 0, 0]), self.speed )
					self.cooldown = 5
				self.fired = True
			else:
				self.fired = False
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







class AsteroidField(object):

	"""docstring for AsteroidField"""
	def __init__(self, (xbound, ybound) ):
		super(AsteroidField, self).__init__()
		self.asteroid_list = []
		for _ in range(50):
			pos = vec3(((random() - 0.5) * 2 * xbound, (random() - 0.5) * 2 * ybound, randrange(-1000, -5)))
			v = vec3.random() * random() * 0.01
			r = vec3.random() * math.pi * random() * 0.01

			self.asteroid_list.append(Asteroid(pos, vel=v, rot=r) )
			
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
	def __init__(self, pos, vel=(0,0,0), rot=(0,0,0)):
		super(Asteroid, self).__init__()
		self.position = vec3(pos) 
		self.velocity = vec3(vel)
		self.rotation = vec3(rot)
		self.orientation = quat.axisangle(vec3.random(), 2 * math.pi * random()).unit()

		self.vao = GLuint(0)
		self.vao_size = 0

		self.sph = sphere([0,0,0],0)
	
	def update(self, scene, pressed):
		self.position = self.position + self.velocity
		self.orientation = self.orientation.multiply(quat.axisangle(self.rotation, self.rotation.mag()).unit())
	
	def draw(self, gl, assets, proj, view):
		# HACK
		# 
		self.sph = assets.get_geometry_sphere(tag="asteroid1")

		# Set up matricies
		#
		model = mat4.scale(2,2,2) * mat4.rotateFromQuat(self.orientation)
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
		return sphere(self.sph.center + self.position, self.sph.radius * 1.5) #TODO change radius of asteroid
	
	