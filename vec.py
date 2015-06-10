

from math import *
import random

# HAHAHAHAH
# It's all secretly numpy!!!!
# 
import numpy as np

_EPS = np.finfo(float).eps * 4.0

class vec3(object):
	"""docstring for vec3"""
	def __init__(self, arg):
		super(vec3, self).__init__()
		if isinstance(arg, vec3):
			self._v = arg._v
		else :
			self._v = np.array(arg)

	def __getattr__(self, attr):
		if attr is 'x':
			return self._v[0]
		if attr is 'y':
			return self._v[1]
		if attr is 'z':
			return self._v[2]
		raise AttributeError("%r object has no attribute %r" % (self.__class__, attr))

	@staticmethod
	def i():
		return vec3([1,0,0])

	@staticmethod
	def j():
		return vec3([0,1,0])

	@staticmethod
	def k():
		return vec3([0,0,1])

	@staticmethod
	def random():
		return vec3([random.random()-0.5,random.random()-0.5,random.random()-0.5]).unit()

	@staticmethod
	def clamp(target, min_v, max_v):
		return vec3(map(lambda (x,l,h): max(min(x, h), l), zip(target._v, min_v._v, max_v._v)))

	def add(self, v):
		return vec3(self._v+v._v)

	def sub(self, v):
		return vec3(self._v-v._v)

	def mul(self, v):
		return vec3(self._v*v._v)

	def dot(self, v):
		return np.dot(self._v, v._v)

	def cross(self, v):
		return vec3(np.cross(self._v, v._v))

	def neg(self):
		return vec3(-self._v)

	def unit(self):
		return vec3(self._v * (1/self.mag()))
		
	def mag(self):
		return np.linalg.norm(self._v)

	def scale(self, s):
		return vec3(self._v * s)


	def __add__(self, r):
		return vec3(self._v+r._v)
	def __radd__(self, l):
		return vec3(l._v-self._v)

	def __sub__(self, r):
		return vec3(self._v-r._v)
	def __rsub__(self, l):
		return vec3(l._v-self._v)

	"""v1 * s will call self.scale(s)"""
	def __mul__(self, r):
		return vec3(self._v*r._v)
	def __rmul__(self, l):
		return vec3(l._v*self._v)

	"""v1 ** v2 will call v1.cross(r)"""
	def __pow__(self, r):
		return vec3(np.cross(self._v, r._v))
	def __rpow__(self, l):
		return vec3(np.cross(l._v, self._v,))



	def __iter__(self):
		return iter(self._v)

	def __getitem__(self, i):
		return self._v[i]

	def __str__(self):
		return "(%s, %s, %s)" % (_format_number(self._v[0]), _format_number(self._v[1]), _format_number(self._v[2]))

	def __repr__(self):
		return "Vec3(%s, %s, %s)" % (self._v[0], self._v[1], self._v[2])




class vec4(object):
	"""docstring for vec4"""
	def __init__(self, arg):
		super(vec4, self).__init__()
		if isinstance(arg, vec4):
			self._v = arg._v
		else :
			self._v = np.array(arg)

	def __getattr__(self, attr):
		if attr is 'x':
			return self._v[0]
		if attr is 'y':
			return self._v[1]
		if attr is 'z':
			return self._v[2]
		if attr is 'w':
			return self._v[2]
		if attr is 'xyz':
			return vec3([self._v[0], self._v[1], self._v[2]])
		raise AttributeError("%r object has no attribute %r" % (self.__class__, attr))

	@staticmethod
	def i():
		return vec4([1,0,0,1])

	@staticmethod
	def j():
		return vec4([0,1,0,1])

	@staticmethod
	def k():
		return vec4([0,0,1,1])

	@staticmethod
	def from_vec3(v, w):
		return vec4([v[0], v[1], v[2], w])

	def add(self, v):
		return vec4(self._v+v._v)

	def sub(self, v):
		return vec4(self._v-v._v)

	def mul(self, v):
		return vec4(self._v*v._v)

	def dot(self, v):
		return np.dot(self._v, v._v)

	def neg(self):
		return vec4(-self._v)

	def unit(self):
		return vec4(self._v * (1/self.mag()))
		
	def mag(self):
		return np.linalg.norm(self._v)

	def scale(self, s):
		return vec4(self._v * s)

	def homogenise(self):
		iw = 1.0/self._v[3]
		return vec4.from_vec3(self._v[0:3] * iw, 1)

	def vec3(self):
		return self.homogenise().xyz


	def __add__(self, r):
		return vec4(self._v+r._v)
	def __radd__(self, l):
		return vec4(l._v-self._v)

	def __sub__(self, r):
		return vec4(self._v-r._v)
	def __rsub__(self, l):
		return vec4(l._v-self._v)

	"""v1 * s will call self.scale(s)"""
	def __mul__(self, r):
		return vec4(self._v*r._v)
	def __rmul__(self, l):
		return vec4(l._v*self._v)

	"""v1 ** v2 will call v1.cross(r)"""
	def __pow__(self, r):
		return vec4(np.cross(self._v, r._v))
	def __rpow__(self, l):
		return vec4(np.cross(l._v, self._v,))



	def __iter__(self):
		return iter(self._v)

	def __getitem__(self, i):
		return self._v[i]

	def __str__(self):
		return "(%s, %s, %s, %s)" % (_format_number(self._v[0]), _format_number(self._v[1]), _format_number(self._v[2]),  _format_number(self._v[3]))

	def __repr__(self):
		return "Vec4(%s, %s, %s, %s)" % (self._v[0], self._v[1], self._v[2], self._v[3])

class mat4(object):
	"""docstring for mat4"""
	def __init__(self, arg):
		super(mat4, self).__init__()
		if isinstance(arg, mat4):
			self._v = arg._v
		else :
			self._v = np.array(arg)
	
	@staticmethod
	def identity():
		return mat4([
			[1, 0, 0, 0,],
			[0, 1, 0, 0,],
			[0, 0, 1, 0,],
			[0, 0, 0, 1]])

	@staticmethod
	def translate(tx, ty, tz):
		return mat4([
			[1, 0, 0, tx,],
			[0, 1, 0, ty,],
			[0, 0, 1, tz,],
			[0, 0, 0, 1]])

	@staticmethod
	def scale(sx, sy, sz):
		return mat4([
			[sx, 0, 0, 0,],
			[0, sy, 0, 0,],
			[0, 0, sz, 0,],
			[0, 0, 0, 1]])

	@staticmethod
	def rotateX(a):
		return mat4([
			[1,		0,		0,		0,],
			[0,		cos(a),	-sin(a),0,],
			[0,		sin(a),	cos(a),	0,],
			[0,		0,		0,		1]])

	@staticmethod
	def rotateY(a):
		return mat4([
			[cos(a),0,		sin(a),	0,],
			[0,		1,		0,		0,],
			[-sin(a),0,		cos(a),	0,],
			[0,		0,		0,		1]])

	@staticmethod
	def rotateZ(a):
		return mat4([
			[cos(a),	-sin(a),0,		0,],
			[sin(a),	cos(a),	0,		0,],
			[0,		0,		1,		0,],
			[0,		0,		0,		1]])

	@staticmethod
	def rotateFromQuat(qu):
		q = qu._v
		n = np.dot(q, q)
		if n < _EPS:
			return np.identity(4)
		q *= sqrt(2.0 / n)
		q = np.outer(q, q)
		return mat4([
			[1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
			[    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
			[    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
			[                0.0,                 0.0,                 0.0, 1.0]])

	@staticmethod
	def perspectiveProjection(fovy, aspect, zNear, zFar):
		f = cos(fovy / 2) / sin(fovy / 2);

		return mat4([
			[f / aspect,0,		0,		0,],
			[0,			f,		0,		0,],
			[0,			0,		(zFar + zNear) / (zNear - zFar),	(2 * zFar * zNear) / (zNear - zFar),],
			[0,			0,		-1,		0]])

	# @staticmethod
	# def lookAt(eye, at, up):
	# 	"""Provides an world to view matrix (the inverse of a view matrix)"""
	# 	e = vec3(eye)
	# 	a = vec3(at)
	# 	u = vec3(up)
	# 	zaxis = (a - e).unit()
	# 	xaxis = u.cross(zaxis).unit()
	# 	yaxis = zaxis.cross(xaxis).unit()

	# 	ne = e.neg()

	# 	return mat4([
	# 		xaxis.x,		yaxis.x,		zaxis.x,		0,
	# 		xaxis.y,		yaxis.y,		zaxis.y,		0,
	# 		xaxis.z,		yaxis.z,		zaxis.z,		0,
	# 		xaxis.dot(ne),	yaxis.dot(ne),	zaxis.dot(ne),	1]);



	def multiply_mat4(self, rhs):
		return mat4(np.dot(self._v, rhs._v))

	def multiply_vec4(self, rhs):
		return vec4(np.dot(self._v, rhs._v))

	def inverse(self):
		return mat4(np.linalg.inv(self._v))

	def transpose(self):
		return mat4(self._v.transpose())

	"""m1 * m2 will call self.multiply_mat4(m2)"""
	def __mul__(self, r):
		return mat4(np.dot(self._v, r._v))

	def __rmul__(self, l):
		return mat4(np.dot(l._v, self._v))


	def flatten(self):
		return self._v.flatten()

	def row(self, i):
		return list(self._v[i])

	def __iter__(self):
		return iter(self.f_v)

	def __getitem__(self, i):
		return self._v[i//4, i%4]

	def __str__(self):
		"""'Pretty' formatting of the Mat4."""

		max_len = max( len(_format_number(v)) for v in self.flatten() )

		def format_row(row):            
			return "%s" % " ".join( _format_number(value).ljust(max_len) for value in row )

		rows = [ format_row(row).rstrip() for row in self._v ]
		max_row_len = max(len(row) for row in rows)
		return "\n".join( "[ %s ]" % row.ljust(max_row_len) for row in rows )


	def __repr__(self):

		def format_row(row):            
			return "(%s)" % ", ".join( _format_number(value) for value in row )

		return "mat4(%s)" % ", ".join(format_row(row) for row in self._v)


class quat(object):
	"""docstring for quat"""
	def __init__(self, arg):
		super(quat, self).__init__()
		if isinstance(arg, quat):
			self._v = arg._v
		else :
			self._v = np.array(arg)
	
	@staticmethod
	def axisangle(axis, angle):
		axis_u = vec3(axis).unit();
		sin_a = sin(angle * 0.5);
		w = cos(angle * 0.5)
		x = axis_u.x * sin_a
		y = axis_u.y * sin_a
		z = axis_u.z * sin_a
		return quat([w, x, y, z])

	def conjugate(self):
		return quat(self._v[0], -self._v[1], -self._v[2], -self._v[3])

	def norm(self):
		return sqrt(self[0]**2 + self[1]**2 + self[2]**2)

	def unit(self):
		return quat(map(lambda x : x * self.norm(), self._v))

	def multiply(self, q):
		return quat([
			self[0] * q[0] - self[1] * q[1] - self[2] * q[2] - self[3] * q[3],
			self[0] * q[1] + self[1] * q[0] + self[2] * q[3] - self[3] * q[2],
			self[0] * q[2] - self[1] * q[3] + self[2] * q[0] + self[3] * q[1],
			self[0] * q[3] + self[1] * q[2] - self[2] * q[1] + self[3] * q[0] ])

	def __getattr__(self, attr):
		if attr is 'w':
			return self._v[0]
		if attr is 'x':
			return self._v[1]
		if attr is 'y':
			return self._v[2]
		if attr is 'z':
			return self._v[3]

		raise AttributeError("%r object has no attribute %r" % (self.__class__, attr))

	def __iter__(self):
		return iter(self._v)

	def __getitem__(self, i):
		return self._v[i]



class sphere(object):
	"""docstring for sphere"""
	def __init__(self, pos, rad):
		super(sphere, self).__init__()
		self.center = pos
		self.radius = rad

	def ray_intersection(self, (o, d)):
		"""
		calcualtes the distance from the origin along the ray to the sphere
		returns a positive number if the ray hits the sphere
		returns -1 if the ray does not intersect the sphere
		"""
		origin = vec3(o)
		direction = vec3(d).unit()
		os = origin - self.center

		a = direction.dot(direction)
		b = 2 * direction.dot(os)
		c = os.dot(os) - (self.radius * self.radius)

		disc = b * b - 4 * a * c
		if disc > 0:
			distSqrt = sqrt(disc)
			q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
			t0 = q / a
			t1 = c / q
			t0, t1 = min(t0, t1), max(t0, t1)
			if t1 >= 0:
				return t1 if t0 < 0 else t0
		return -1

	def sphere_intersection(self, s):
		"""
		calculates the distance between the surfaces of the sphere
		returns negitive distance if the spheres are overlapping
		returns 0 if the surfaces of the spheres are touching
		otherwise returns the positive diatance between the surfaces of the spheres
		"""
		return (self.center - s.center).mag() - (self.radius + s.radius)

	def __str__(self):
		return "(" + str(self.center) + ", " + str(self.radius) + ")"

	def __repr__(self):
		return "sphere(" + str(self.center) + ", r=" + str(self.radius) + ")"


def _format_number(n, accuracy=6):
    """Formats a number in a friendly manner (removes trailing zeros and unneccesary point."""
    
    fs = "%."+str(accuracy)+"f"
    str_n = fs%float(n)
    if '.' in str_n:
        str_n = str_n.rstrip('0').rstrip('.')
    if str_n == "-0":
        str_n = "0"
    #str_n = str_n.replace("-0", "0")
    return str_n

