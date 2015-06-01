

from math import *
import random

class vec3(object):
	"""docstring for vec3"""
	def __init__(self, arg):
		super(vec3, self).__init__()
		x, y, z = arg
		self._v = (x, y, z)

	def __getattr__(self, attr):
		if attr is 'x':
			return self[0]
		if attr is 'y':
			return self[1]
		if attr is 'z':
			return self[2]

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

	def add(self, v):
		x, y, z = v;
		return vec3((self[0] + x, self[1] + y, self[2] + z))

	def sub(self, v):
		x, y, z = v;
		return vec3((self[0] - x, self[1] - y, self[2] - z))


	def dot(self, v):
		x, y, z = v;
		return self[0] * x + self[1] * y + self[2] * z

	def cross(self, v):
		x, y, z = v
		return vec3([
			self.y * z - self.z * y,
			self.z * x - self.x * z,
			self.x * y - self.y * x])

	def neg(self):
		return vec3((-self[0], -self[1], -self[2]))

	def unit(self):
		return self.scale(1.0/self.mag())
		

	def mag(self):
		return sqrt(self[0]**2 + self[1]**2 + self[2]**2)

	def scale(self, s):
		return vec3((self[0] * s, self[1] * s, self[2] * s))


	def __add__(self, r):
		return self.add(r)
	def __radd__(self, l):
		return vec3(l).add(self)

	def __sub__(self, r):
		return self.sub(r)
	def __rsub__(self, l):
		return vec3(l).sub(self)

	"""v1 * s will call self.scale(s)"""
	def __mul__(self, r):
		return self.scale(r)
	def __rmul__(self, l):
		return self.scale(l)

	"""v1 ** v2 will call v1.cross(r)"""
	def __pow__(self, r):
		return self.cross(r)
	def __rpow__(self, l):
		return vec3(l).cross(self)



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
		x, y, z, w = arg
		self._v = (x, y, z, w)

	def __getattr__(self, attr):
		if attr is 'x':
			return self[0]
		if attr is 'y':
			return self[1]
		if attr is 'z':
			return self[2]
		if attr is 'w':
			return self[3]
		if attr is 'xyz':
			return vec3((self[0], self[1], self[2]))

		raise AttributeError("%r object has no attribute %r" % (self.__class__, attr))


	def add(self, v):
		x, y, z, w = v;
		return vec4((self[0] + x, self[1] + y, self[2] + z, self[3] + w))

	def sub(self, v):
		x, y, z, w = v;
		return vec4((self[0] - x, self[1] - y, self[2] - z, self[3] - w))


	def dot(self, v):
		x, y, z, w = v;
		return self[0] * x + self[1] * y + self[2] * z + self[3] * w

	def neg(self):
		return vec4((-self[0], -self[1], -self[2], -self[3]))

	def unit(self):
		return scale(self, 1.0/self.mag())
		

	def mag(self):
		return sqrt(self[0]**2 + self[1]**2 + self[2]**2  + self[3]**2)

	def scale(self, s):
		return vec4((self[0] * s, self[1] * s, self[2] * s, self[3] * s))

	def vec3(self, s):
		return vec3((self[0], self[1], self[2]))


	def __add__(self, r):
		return self.add(r)
	def __radd__(self, l):
		return vec3(l).add(self)

	def __sub__(self, r):
		return self.sub(r)
	def __rsub__(self, l):
		return vec3(l).sub(self)

	"""v1 * s will call self.scale(s)"""
	def __mul__(self, r):
		return self.scale(r)
	def __rmul__(self, l):
		return self.scale(l)


	def __iter__(self):
		return iter(self._v)

	def __getitem__(self, i):
		return self._v[i]

	def __str__(self):
		return "(%s, %s, %s, %s)" % (_format_number(self._v[0]), _format_number(self._v[1]), _format_number(self._v[2]), _format_number(self._v[4]))

	def __repr__(self):
		return "Vec3(%s, %s, %s, %s)" % (self._v[0], self._v[1], self._v[2], self._v[3])

class mat4(object):
	"""docstring for mat4"""
	def __init__(self, arg):
		super(mat4, self).__init__()
		e00, e01, e02, e03, e10, e11, e12, e13, e20, e21, e22, e23, e30, e31, e32, e33 = arg
		self._v = (
			(e00, e01, e02, e03),
			(e10, e11, e12, e13),
			(e20, e21, e22, e23),
			(e30, e31, e32, e33))
	
	@staticmethod
	def identity():
		return mat4([
			1, 0, 0, 0,
			0, 1, 0, 0,
			0, 0, 1, 0,
			0, 0, 0, 1])

	@staticmethod
	def translate(tx, ty, tz):
		return mat4([
			1, 0, 0, tx,
			0, 1, 0, ty,
			0, 0, 1, tz,
			0, 0, 0, 1])

	@staticmethod
	def scale(sx, sy, sz):
		return mat4([
			sx, 0, 0, 0,
			0, sy, 0, 0,
			0, 0, sz, 0,
			0, 0, 0, 1])

	@staticmethod
	def rotateX(a):
		return mat4([
			1,		0,		0,		0,
			0,		cos(a),	-sin(a),0,
			0,		sin(a),	cos(a),	0,
			0,		0,		0,		1])

	@staticmethod
	def rotateY(a):
		return mat4([
			cos(a),	0,		sin(a),	0,
			0,		1,		0,		0,
			-sin(a),0,		cos(a),	0,
			0,		0,		0,		1])

	@staticmethod
	def rotateZ(a):
		return mat4([
			cos(a),	-sin(a),0,		0,
			sin(a),	cos(a),	0,		0,
			0,		0,		1,		0,
			0,		0,		0,		1])

	@staticmethod
	def rotateFromQuat(q):
		w = q.w
		x = q.x
		y = q.y
		z = q.y

		return mat4([
			w * w + x * x - y * y - z * z,
			2 * x * y - 2 * w * z,
			2 * x * z + 2 * w * y,
			0,
			2 * x * y + 2 * w * z,
			w * w - x * x + y * y - z * z,
			2 * y * z - 2 * w * x,
			0,
			2 * x * z - 2 * w * y,
			2 * y * z + 2 * w * x,
			w * w - x * x - y * y + z * z,
			0,
			0,
			0,
			0,
			w * w + x * x + y * y + z * z])

	@staticmethod
	def perspectiveProjection(fovy, aspect, zNear, zFar):
		f = cos(fovy / 2) / sin(fovy / 2);

		return mat4([
			f / aspect,	0,		0,		0,
			0,			f,		0,		0,
			0,			0,		(zFar + zNear) / (zNear - zFar),	(2 * zFar * zNear) / (zNear - zFar),
			0,			0,		-1,		0])

	@staticmethod
	def lookAt(eye, at, up):
		"""Provides an world to view matrix (the inverse of a view matrix)"""
		e = vec3(eye)
		a = vec3(at)
		u = vec3(up)
		zaxis = (a - e).unit()
		xaxis = u.cross(zaxis).unit()
		yaxis = zaxis.cross(xaxis).unit()

		ne = e.neg()

		return mat4([
			xaxis.x,		yaxis.x,		zaxis.x,		0,
			xaxis.y,		yaxis.y,		zaxis.y,		0,
			xaxis.z,		yaxis.z,		zaxis.z,		0,
			xaxis.dot(ne),	yaxis.dot(ne),	zaxis.dot(ne),	1]);



	def multiply_mat4(self, rhs):
		lpt = self.flatten()
		rpt = rhs.flatten()
		return mat4([
			lpt[0] * rpt[0] + lpt[1] * rpt[4] + lpt[2] * rpt[8] + lpt[3] * rpt[12],
			lpt[0] * rpt[1] + lpt[1] * rpt[5] + lpt[2] * rpt[9] + lpt[3] * rpt[13],
			lpt[0] * rpt[2] + lpt[1] * rpt[6] + lpt[2] * rpt[10] + lpt[3] * rpt[14],
			lpt[0] * rpt[3] + lpt[1] * rpt[7] + lpt[2] * rpt[11] + lpt[3] * rpt[15],
			lpt[4] * rpt[0] + lpt[5] * rpt[4] + lpt[6] * rpt[8] + lpt[7] * rpt[12],
			lpt[4] * rpt[1] + lpt[5] * rpt[5] + lpt[6] * rpt[9] + lpt[7] * rpt[13],
			lpt[4] * rpt[2] + lpt[5] * rpt[6] + lpt[6] * rpt[10] + lpt[7] * rpt[14],
			lpt[4] * rpt[3] + lpt[5] * rpt[7] + lpt[6] * rpt[11] + lpt[7] * rpt[15],
			lpt[8] * rpt[0] + lpt[9] * rpt[4] + lpt[10] * rpt[8] + lpt[11] * rpt[12],
			lpt[8] * rpt[1] + lpt[9] * rpt[5] + lpt[10] * rpt[9] + lpt[11] * rpt[13],
			lpt[8] * rpt[2] + lpt[9] * rpt[6] + lpt[10] * rpt[10] + lpt[11] * rpt[14],
			lpt[8] * rpt[3] + lpt[9] * rpt[7] + lpt[10] * rpt[11] + lpt[11] * rpt[15],
			lpt[12] * rpt[0] + lpt[13] * rpt[4] + lpt[14] * rpt[8] + lpt[15] * rpt[12],
			lpt[12] * rpt[1] + lpt[13] * rpt[5] + lpt[14] * rpt[9] + lpt[15] * rpt[13],
			lpt[12] * rpt[2] + lpt[13] * rpt[6] + lpt[14] * rpt[10] + lpt[15] * rpt[14],
			lpt[12] * rpt[3] + lpt[13] * rpt[7] + lpt[14] * rpt[11] + lpt[15] * rpt[15]])


	def multiply_vec4(self, rhs):
		pt = self.flatten()
		return vec4([
			pt[0] * rhs.x + pt[1] * rhs.y + pt[2] * rhs.z + pt[3] * rhs.w,
			pt[4] * rhs.x + pt[5] * rhs.y + pt[6] * rhs.z + pt[7] * rhs.w,
			pt[8] * rhs.x + pt[9] * rhs.y + pt[10] * rhs.z + pt[11] * rhs.w,
			pt[12] * rhs.x + pt[13] * rhs.y + pt[14] * rhs.z + pt[15] * rhs.w])


	@staticmethod
	def _det3x3(e00, e01, e02, e10, e11, e12, e20, e21, e22):
		d = 0
		d += e00 * e11 * e22;
		d += e01 * e12 * e20;
		d += e02 * e10 * e21;
		d -= e00 * e12 * e21;
		d -= e01 * e10 * e22;
		d -= e02 * e11 * e20;
		return d;


	def inverse(self):
		pt = self.flatten()
		mpt = [0] * 16
		
		# first row of cofactors, can use for determinant
		c00 = mat4._det3x3(pt[5], pt[6], pt[7], pt[9], pt[10], pt[11], pt[13], pt[14], pt[15]);
		c01 = -mat4._det3x3(pt[4], pt[6], pt[7], pt[8], pt[10], pt[11], pt[12], pt[14], pt[15]);
		c02 = mat4._det3x3(pt[4], pt[5], pt[7], pt[8], pt[9], pt[11], pt[12], pt[13], pt[15]);
		c03 = -mat4._det3x3(pt[4], pt[5], pt[6], pt[8], pt[9], pt[10], pt[12], pt[13], pt[14]);
		# get determinant by expanding about first row
		invdet = 1 / (pt[0] * c00 + pt[1] * c01 + pt[2] * c02 + pt[3] * c03);
		# FIXME proper detect infinite determinant
		# if (math::isinf(invdet) || invdet != invdet || invdet == 0)
		# 	throw std::runtime_error("Non-invertible matrix.");
		# transpose of cofactor matrix * (1 / det)
		mpt[0] = c00 * invdet;
		mpt[4] = c01 * invdet;
		mpt[8] = c02 * invdet;
		mpt[12] = c03 * invdet;
		mpt[1] = -mat4._det3x3(pt[1], pt[2], pt[3], pt[9], pt[10], pt[11], pt[13], pt[14], pt[15]) * invdet;
		mpt[5] = mat4._det3x3(pt[0], pt[2], pt[3], pt[8], pt[10], pt[11], pt[12], pt[14], pt[15]) * invdet;
		mpt[9] = -mat4._det3x3(pt[0], pt[1], pt[3], pt[8], pt[9], pt[11], pt[12], pt[13], pt[15]) * invdet;
		mpt[13] = mat4._det3x3(pt[0], pt[1], pt[2], pt[8], pt[9], pt[10], pt[12], pt[13], pt[14]) * invdet;
		mpt[2] = mat4._det3x3(pt[1], pt[2], pt[3], pt[5], pt[6], pt[7], pt[13], pt[14], pt[15]) * invdet;
		mpt[6] = -mat4._det3x3(pt[0], pt[2], pt[3], pt[4], pt[6], pt[7], pt[12], pt[14], pt[15]) * invdet;
		mpt[10] = mat4._det3x3(pt[0], pt[1], pt[3], pt[4], pt[5], pt[7], pt[12], pt[13], pt[15]) * invdet;
		mpt[14] = -mat4._det3x3(pt[0], pt[1], pt[2], pt[4], pt[5], pt[6], pt[12], pt[13], pt[14]) * invdet;
		mpt[3] = -mat4._det3x3(pt[1], pt[2], pt[3], pt[5], pt[6], pt[7], pt[9], pt[10], pt[11]) * invdet;
		mpt[7] = mat4._det3x3(pt[0], pt[2], pt[3], pt[4], pt[6], pt[7], pt[8], pt[10], pt[11]) * invdet;
		mpt[11] = -mat4._det3x3(pt[0], pt[1], pt[3], pt[4], pt[5], pt[7], pt[8], pt[9], pt[11]) * invdet;
		mpt[15] = mat4._det3x3(pt[0], pt[1], pt[2], pt[4], pt[5], pt[6], pt[8], pt[9], pt[10]) * invdet;
		return mat4(mpt);

	def transpose(self):
		return mat4([e for row in zip(*self._v) for e in row])

	"""m1 * m2 will call self.multiply_mat4(m2)"""
	def __mul__(self, r):
		return self.multiply_mat4(r)
	def __rmul__(self, l):
		return l.multiply_mat4(self)


	def flatten(self):
		return [e for row in self._v for e in row]

	def row(self, i):
		return list(self._v[i])

	def __iter__(self):
		return iter(self.flatten())

	def __getitem__(self, i):
		return self._v[i//4][i%4]

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
		w, x, y, z = arg
		self._v = (w, x, y, z)
	
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
		return quat(self[0], -self[1], -self[2], -self[3])

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
			return self[0]
		if attr is 'x':
			return self[1]
		if attr is 'y':
			return self[2]
		if attr is 'z':
			return self[3]

		raise AttributeError("%r object has no attribute %r" % (self.__class__, attr))

	def __iter__(self):
		return iter(self._v)

	def __getitem__(self, i):
		return self._v[i]



class sphere(object):
	"""docstring for sphere"""
	def __init__(self, pos, rad):
		super(sphere, self).__init__()
		self.center = vec3(pos)
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
		return "sphere(" + self.center + ", r=" + str(self.radius) + ")"


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

