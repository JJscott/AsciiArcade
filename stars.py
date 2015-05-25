
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


class Stars(object):
	"""Stars"""
	def __init__(self):
		super(Stars, self).__init__()
		self.reset()
		

	def reset(self):
		self.scene = []
		self.ship = Ship()
		self.scene.append(self.ship)

		for _ in range(50):
			self.scene.append(Astroid( (
				randrange(-5, 5),
				randrange(-5, 5),
				randrange(-1000, -5)
				) ))


	# Game logic
	#
	def tick(self, pressed):
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
			obj.draw(gl, proj, view)
		
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




class Ship(object):
	"""docstring for Ship"""
	def __init__(self):
		super(Ship, self).__init__()
		self.position = vec3([0, 0, 0])
		self.speed = 0.1
		self.dead = False

	def get_view_matrix(self):
		cam_pos = vec3([0, 0, 15])
		cam_Xrot = -math.pi / 6
		ship_pos =  vec3([0, 0, self.position.z])
		return (mat4.translate(ship_pos.x, ship_pos.y, ship_pos.z) *
			mat4.rotateX(cam_Xrot) *
			mat4.translate(cam_pos.x, cam_pos.y, cam_pos.z))

		
	def update(self, scene, pressed):

		if not self.dead:
			# Update target
			#

			# Check "shots fired"
			#

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
			self.position = self.position + vec3([0, 0, -self.speed])
			self.speed *= 1.001


			# Colision detection
			#
			my_s = sphere(self.position, 1) # my sphere
			ss = [obj.get_sphere() for obj in scene if isinstance(obj, Astroid)]
			for s in ss:
				if my_s.sphere_intersection(s) < 0 :
					self.dead = True
					break;
				# } 
			# }
		# }




	def draw(self, gl, proj, view):
		if not cube_init:
			initCube(gl)

		model = mat4.translate(self.position.x, self.position.y, self.position.z)
		mv = view * model

		# Render
		# 
		renderCube(
			gl,
			pygloo.c_array(GLfloat, proj.flatten()),
			pygloo.c_array(GLfloat, mv.flatten()) );

		# TODO render firing target


class Astroid(object):
	"""docstring for Astroid"""
	def __init__(self, pos, vel=(0,0,0)):
		super(Astroid, self).__init__()
		self.position = vec3(pos)
		self.velocity = vec3(vel)
		self.orientation = mat4.rotateY(random() * math.pi * 2) * mat4.rotateX(random() * math.pi - math.pi/2)
	
	def update(self, scene, pressed):
		self.position = self.position + self.velocity

	def draw(self, gl, proj, view):
		if not cube_init:
			initCube(gl)
		scale = mat4.scale(2.5,2.5,2.5)
		trans = mat4.translate(self.position.x, self.position.y, self.position.z)
		rotate = self.orientation
		mv = view * trans * rotate * scale

		# Render
		# 
		renderCube(
			gl,
			pygloo.c_array(GLfloat, proj.flatten()),
			pygloo.c_array(GLfloat, mv.flatten()) );


	def get_sphere(self):
		return sphere(self.position, 2.5) #TODO change radius of astroid











prog = GLuint(0)
vao = GLuint(0)
cube_init = False;

def initCube(gl):
	global prog
	global vao
	global cube_init

	cube_shader_source = """
	/*
	 *
	 * Default shader program for writing to scene buffer using GL_TRIANGLES
	 *
	 */

	uniform mat4 modelViewMatrix;
	uniform mat4 projectionMatrix;

	#ifdef _VERTEX_

	layout(location = 0) in vec3 vertexPosition_modelspace;
	layout(location = 1) in vec3 vertexColor;

	out vec3 fragmentColor;

	void main() {
		vec3 pos_v = (modelViewMatrix * vec4(vertexPosition_modelspace, 1.0)).xyz;
		gl_Position = projectionMatrix * vec4(pos_v, 1.0);
		fragmentColor = vertexColor;
	}

	#endif


	#ifdef _FRAGMENT_

	in vec3 fragmentColor;
	out vec3 color;

	void main(){
	    color = fragmentColor;
	}

	#endif
	"""
	prog = makeProgram(gl, "330 core", { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER }, cube_shader_source)



	# vertex positions
	# 
	pos_array = pygloo.c_array(GLfloat, [
		-1.0, -1.0, -1.0,
		-1.0, -1.0, 1.0,
		-1.0, 1.0, 1.0,
		1.0, 1.0, -1.0,
		-1.0, -1.0, -1.0,
		-1.0, 1.0, -1.0,
		1.0, -1.0, 1.0,
		-1.0, -1.0, -1.0,
		1.0, -1.0, -1.0,
		1.0, 1.0, -1.0,
		1.0, -1.0, -1.0,
		-1.0, -1.0, -1.0,
		-1.0, -1.0, -1.0,
		-1.0, 1.0, 1.0,
		-1.0, 1.0, -1.0,
		1.0, -1.0, 1.0,
		-1.0, -1.0, 1.0,
		-1.0, -1.0, -1.0,
		-1.0, 1.0, 1.0,
		-1.0, -1.0, 1.0,
		1.0, -1.0, 1.0,
		1.0, 1.0, 1.0,
		1.0, -1.0, -1.0,
		1.0, 1.0, -1.0,
		1.0, -1.0, -1.0,
		1.0, 1.0, 1.0,
		1.0, -1.0, 1.0,
		1.0, 1.0, 1.0,
		1.0, 1.0, -1.0,
		-1.0, 1.0, -1.0,
		1.0, 1.0, 1.0,
		-1.0, 1.0, -1.0,
		-1.0, 1.0, 1.0,
		1.0, 1.0, 1.0,
		-1.0, 1.0, 1.0,
		1.0, -1.0, 1.0])

	# color positions
	# 
	col_array = pygloo.c_array(GLfloat, [
		0.583, 0.771, 0.014,
		0.609, 0.115, 0.436,
		0.327, 0.483, 0.844,
		0.822, 0.569, 0.201,
		0.435, 0.602, 0.223,
		0.310, 0.747, 0.185,
		0.597, 0.770, 0.761,
		0.559, 0.436, 0.730,
		0.359, 0.583, 0.152,
		0.483, 0.596, 0.789,
		0.559, 0.861, 0.639,
		0.195, 0.548, 0.859,
		0.014, 0.184, 0.576,
		0.771, 0.328, 0.970,
		0.406, 0.615, 0.116,
		0.676, 0.977, 0.133,
		0.971, 0.572, 0.833,
		0.140, 0.616, 0.489,
		0.997, 0.513, 0.064,
		0.945, 0.719, 0.592,
		0.543, 0.021, 0.978,
		0.279, 0.317, 0.505,
		0.167, 0.620, 0.077,
		0.347, 0.857, 0.137,
		0.055, 0.953, 0.042,
		0.714, 0.505, 0.345,
		0.783, 0.290, 0.734,
		0.722, 0.645, 0.174,
		0.302, 0.455, 0.848,
		0.225, 0.587, 0.040,
		0.517, 0.713, 0.338,
		0.053, 0.959, 0.120,
		0.393, 0.621, 0.362,
		0.673, 0.211, 0.457,
		0.820, 0.883, 0.371,
		0.982, 0.099, 0.879])

	gl.glGenVertexArrays(1, vao)
	gl.glBindVertexArray(vao)

	vbo_pos = GLuint(0)
	gl.glGenBuffers(1, vbo_pos)
	gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_pos)
	gl.glBufferData(GL_ARRAY_BUFFER, sizeof(pos_array), pos_array, GL_STATIC_DRAW)
	gl.glEnableVertexAttribArray(0)
	gl.glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0)

	# //glBindBuffer(GL_ARRAY_BUFFER, 0);

	vbo_col = GLuint(0)
	gl.glGenBuffers(1, vbo_col)

	gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_col)
	gl.glBufferData(GL_ARRAY_BUFFER, sizeof(col_array), col_array, GL_STATIC_DRAW)
	gl.glEnableVertexAttribArray(1)
	gl.glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, 0)

	gl.glBindBuffer(GL_ARRAY_BUFFER, 0)

	gl.glBindVertexArray(0)
	cube_init = True


def renderCube(gl, proj, view):
	gl.glUseProgram(prog)

	gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "modelViewMatrix"), 1, True, view)
	gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog, "projectionMatrix"), 1, True, proj)

	gl.glBindVertexArray(vao)
	gl.glDrawArrays(GL_TRIANGLES, 0, 36)
