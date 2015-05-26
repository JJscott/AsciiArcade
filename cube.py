
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


