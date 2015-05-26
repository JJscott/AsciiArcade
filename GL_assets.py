
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



class GL_assets(object):
	"""docstring for GL_assets"""
	def __init__(self):
		super(GL_assets, self).__init__()

		self.geo_dict = {}
		self.shader_dict = {}

		# TODO load default geo and stuff


	def load_geometry(self, gl, tag, filename):
		vao, size = _load_geometry(gl, filename)
		self.geo_dict[tag] = (vao, size)
		print "Added Shader Asset {f} :: tag={t} vao={v} polycount={p}".format(f=filename, t=tag, v=vao, p=size)

	def load_shader(self, gl, tag, source):
		prog = makeProgram(gl, "330 core", { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER }, source)
		self.shader_dict[tag] = prog
		print "Added Shader Asset :: tag={t} prog={p}".format(t=tag, p=prog)


	def get_geometry(self, tag=None):
		if tag: return self.geo_dict[tag]
		return None # Change to default


	def get_shader(self, tag=None):
		if tag: return self.shader_dict[tag]
		return None # Change to default



def _load_geometry(gl, filename):
	verts = [[0.0, 0.0, 0.0]]
	texts = [[0.0, 0.0]]
	norms = [[0.0, 0.0, 0.0]]

	vertsOut = []
	textsOut = []
	normsOut = []

	for line in open(filename, "r"):
		vals = line.split()
		if len(vals) > 0:
			if vals[0] == "v":
				v = map(float, vals[1:4])
				verts.append(v)
			elif vals[0] == "vn":
				n = map(float, vals[1:4])
				norms.append(n)
			elif vals[0] == "vt":
				t = map(float, vals[1:3])
				texts.append(t)
			elif vals[0] == "f":
				for f in vals[1:4]: # Assume triangluation
					w = f.split("/")
					vertsOut.append(list(verts[int(w[0])]))
					if len(w) == 2 or w[1]: textsOut.append(list(texts[int(w[1])]))
					else: textsOut.append([0.0,0.0])
					if len(w) == 3: normsOut.append(list(norms[int(w[2])]))
					else: normsOut.append([0.0, 0.0, 1.0]); # Fuck you for not providing normals, it'll just point toward some direction then

	return _createVAO(gl, vertsOut, normsOut, textsOut), len(vertsOut)


def _createVAO(gl, vert, norm, tex):

	# Converting to GL friendly format
	# 
	vert_array = pygloo.c_array(GLfloat, _flatten_list(vert))
	norm_array = pygloo.c_array(GLfloat, _flatten_list(norm))
	tex_array = pygloo.c_array(GLfloat, _flatten_list(tex))

	# Creating the VAO
	# 
	vao = GLuint(0)
	gl.glGenVertexArrays(1, vao)
	gl.glBindVertexArray(vao)

	# Vertex Position VBO  (pos 0)
	# 
	vbo_pos = GLuint(0)
	gl.glGenBuffers(1, vbo_pos)
	gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_pos)
	gl.glBufferData(GL_ARRAY_BUFFER, sizeof(vert_array), vert_array, GL_STATIC_DRAW)
	gl.glEnableVertexAttribArray(0)
	gl.glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0)
	
	# Vertex Normal VBO  (pos 1)
	# 
	vbo_norm = GLuint(0)
	gl.glGenBuffers(1, vbo_norm)
	gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_norm)
	gl.glBufferData(GL_ARRAY_BUFFER, sizeof(norm_array), norm_array, GL_STATIC_DRAW)
	gl.glEnableVertexAttribArray(1)
	gl.glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, 0)

	# Vertex Texture Coordinate VBO  (pos 2)
	# 
	vbo_tex = GLuint(0)
	gl.glGenBuffers(1, vbo_tex)
	gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_tex)
	gl.glBufferData(GL_ARRAY_BUFFER, sizeof(tex_array), tex_array, GL_STATIC_DRAW)
	gl.glEnableVertexAttribArray(2)
	gl.glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)


	# Cleanup
	# 
	gl.glBindBuffer(GL_ARRAY_BUFFER, 0)
	gl.glBindVertexArray(0)

	return vao

def _flatten_list(l):
	return [e for row in l for e in row]
