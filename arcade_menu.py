# Pygame
# 
from pygame.locals import *



import ascii
import game
from vec import *
import math


class ArcadeMenuState(object):
	"""docstring for ArcadeMenuState"""
	def __init__(self):
		super(ArcadeMenuState, self).__init__()
		self.reset()
		self.pause = 0

	def reset(self):
		self.scene = {}
		self.scene["ship"] = DummyShip()
		self.scene["asteroid_field"] = game.AsteroidField()
		

	# Game logic
	#
	def tick(self, pressed):
		# Update all objects in the scene
		#
		scene_itr = self.scene.copy()
		for (_, obj) in scene_itr.items():
			obj.update(self.scene, pressed)

		self.pause +=1
		if self.pause > 50:
			if pressed[K_SPACE]:
				return game.GameState()


	# Render logic
	#
	def render(self, gl, w, h, ascii_r=None):

		zfar = 1000
		znear = 0.1

		# Create view and projection matrix
		#
		proj = mat4.perspectiveProjection(math.pi / 3, float(w)/h, znear, zfar)
		view = self.scene["ship"].get_view_matrix()

		# Render all objects in the scene
		# 
		for (_, obj) in self.scene.items():
			obj.draw(gl, proj, view)



		if ascii_r:
			art1 = ascii.wordart('ASCII', 'big')
			art2 = ascii.wordart('ARCADE', 'big')

			# temp
			ascii_r.draw_text(art1, color = (0.333, 1, 1), screenorigin = (0.2, 0.667), textorigin = (0, 0.5), align = 'l')
			ascii_r.draw_text(art2, color = (1, 0.333, 1), screenorigin = (0.8, 0.333), textorigin = (1, 0.5), align = 'l')

			ascii_r.draw_text("Pres Start", color = (1, 1, 1), screenorigin = (0.5, 0.5), textorigin = (0.5, 0.5), align = 'c')
		



class DummyShip(object):

	"""docstring for DummyShip"""
	def __init__(self):
		super(DummyShip, self).__init__()
		self.position = vec3([0, 0, 0])
		self.x_time = 0
		self.y_time = 0
		
	def get_position(self):
		return self.position
	
	def get_view_matrix(self):
		return mat4.translate(self.position.x, self.position.y, self.position.z).inverse()

	# Spheres suited to ship model
	# 	approx sphere 0,0,0 radius 4
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

		x_period = 1000.0
		y_period = 1333.0

		x = 50 * math.sin((2*math.pi) * (self.x_time / x_period) )
		y = 50 * math.sin((2*math.pi) * (self.y_time / y_period) )

		self.position = vec3([x, y, self.position.z-1])

		self.x_time += 1
		self.y_time += 1



	def draw(self, gl, proj, view):
		pass