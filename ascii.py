
from __future__ import division

import pygame
import ctypes
from pygloo import *
from simpleShader import makeProgram

_shader_fullscreen_source = '''

// vertex shader
#ifdef _VERTEX_

void main() { }

#endif

// geometry shader
#ifdef _GEOMETRY_

layout(points) in;
layout(triangle_strip, max_vertices = 3) out;

out vec2 texCoord;

void main() {
	// output a single triangle that covers the whole screen
	
	gl_Position = vec4(3.0, 1.0, 0.0, 1.0);
	texCoord = vec2(2.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, 1.0, 0.0, 1.0);
	texCoord = vec2(0.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, -3.0, 0.0, 1.0);
	texCoord = vec2(0.0, -1.0);
	EmitVertex();
	
	EndPrimitive();
	
}

#endif

// fragment shader
#ifdef _FRAGMENT_

in vec2 texCoord;

// main() should be implemented by includer

#endif
'''

_shader_edge_source = _shader_fullscreen_source + '''

#ifdef _FRAGMENT_

void main() {
	
}

#endif
'''

_shader_ascii_source = _shader_fullscreen_source + '''

uniform ivec2 char_size;
uniform sampler2D sampler_color;
uniform sampler2D sampler_depth;
uniform sampler1D sampler_lum2ascii;

#ifdef _FRAGMENT_

out vec4 frag_ascii;

vec3 color_avg() {
	vec3 c;
	for (int i = 0; i < char_size.x; i++) {
		for (int j = 0; j < char_size.y; j++) {
			c += texelFetch(sampler_color, ivec2(floor(gl_FragCoord.xy)) * char_size + ivec2(i, j), 0).rgb;
		}
	}
	return c / float(char_size.x * char_size.y);
}

void main() {
	float lum = dot(vec3(0.2126, 0.7152, 0.0722), color_avg());
	int codepoint = int(floor(texture(sampler_lum2ascii, lum).r * 255.0 + 0.5));
	frag_ascii = vec4(vec3(0.0), (float(codepoint) + 0.5) / 255.0);
}

#endif
'''

_shader_text_source = '''

uniform sampler2D sampler_text;
uniform sampler2D sampler_font;

const vec3 bgcolor = vec3(1.0);

const vec2 char_uvlim = vec2(0.75, 1.0) / 16.0;

#ifdef _VERTEX_

layout(location = 0) in vec2 pos;

out vec2 texCoord;
flat out vec3 textcolor;
flat out int codepoint;

void main() {
	gl_Position = vec4(pos, 0.0, 1.0);
	texCoord = vec2(0.5) + 0.5 * pos;
	vec4 rgba = texelFetch(sampler_text, ivec2(floor(texCoord * vec2(textureSize(sampler_text, 0)))), 0);
	textcolor = rgba.rgb;
	codepoint = int(floor(rgba.a * 255.0));
}


#endif

#ifdef _FRAGMENT_

in vec2 texCoord;
flat in vec3 textcolor;
flat in int codepoint;

out vec4 frag_color;

vec4 textureFont(int c, vec2 uv) {
	vec2 uvmod = mod(vec2(1.0, -1.0) * uv, vec2(1.0));
	int ix = c & 0xF;
	int iy = c >> 4;
	// manual grad to avoid discontinuities from mod()
	// TODO fix inter-char interpolation
	return textureGrad(sampler_font, vec2(ix, iy) / 16.0 + uvmod * char_uvlim, dFdx(uv * char_uvlim), dFdy(uv * char_uvlim));
}

void main() {
	vec2 fontuv = texCoord * vec2(textureSize(sampler_text, 0));
	frag_color = vec4(mix(bgcolor, textcolor, vec3(textureFont(codepoint, fontuv).r)), 1.0);
}

#endif

'''



class AsciiRenderer:
	
	def __init__(self, gl):
		self.gl = gl
		
		self._img_size = (1, 1)
		
		# text screen buffer (w, h)
		self._text_size = (0, 50)
		
		# char size in pixels (w, h)
		self._char_size = (6, 8)
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# font texture
		fontimg = pygame.image.load('./res/font.png')
		self._tex_font = GLuint(0)
		gl.glGenTextures(1, self._tex_font)
		
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_font)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LOD, 6) # TODO dont hardcode this
		# this feels disgusting
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, fontimg.get_width(), fontimg.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.create_string_buffer(pygame.image.tostring(fontimg, 'RGB')))
		gl.glGenerateMipmap(GL_TEXTURE_2D)
		
		# luminance to ASCII texture (1D)
		lumstr = '#BXOI*eoc:. '
		self._tex_lum2ascii = GLuint(0)
		gl.glGenTextures(1, self._tex_lum2ascii)
		
		gl.glBindTexture(GL_TEXTURE_1D, self._tex_lum2ascii)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage1D(GL_TEXTURE_1D, 0, GL_R8, len(lumstr), 0, GL_RED, GL_UNSIGNED_BYTE, ctypes.create_string_buffer(lumstr))
		
		# main FBO
		self._fbo_main = GLuint(0)
		self._tex_color = GLuint(0)
		self._tex_depth = GLuint(0)
		
		gl.glGenFramebuffers(1, self._fbo_main)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_main)
		
		gl.glGenTextures(1, self._tex_color)
		gl.glGenTextures(1, self._tex_depth)
		
		# color texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_color, 0)
		
		# depth texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, 1, 1, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self._tex_depth, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# edge detection FBO
		self._fbo_edge = GLuint(0)
		self._tex_edge = GLuint(0)
		
		gl.glGenFramebuffers(1, self._fbo_edge)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_edge)
		
		gl.glGenTextures(1, self._tex_edge)
		
		# edge texture - RGB-EDGE
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_edge, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# text FBO
		self._fbo_text = GLuint(0)
		self._tex_text = GLuint(0) # RGB-ASCII
		
		gl.glGenFramebuffers(1, self._fbo_text)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_text)
		
		gl.glGenTextures(1, self._tex_text)
		
		# RGB-ASCII texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_text, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# clean up
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		gl.glBindTexture(GL_TEXTURE_2D, 0)
		
		# pending direct text
		# (row, col, color, text)
		self._direct_text = []
	# }
	
	def _resize(self, w, h, _last = [(1, 1)]):
		if (w, h) == _last[0]: return
		_last[0] = (w, h)
		print 'resize motherfucker!'
		
		gl = self.gl
		
		self._text_size = (int(self._text_size[1] * w / h * self._char_size[1] / self._char_size[0]), self._text_size[1])
		self._img_size = tuple(a * b for a, b in zip(self._text_size, self._char_size))
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# color texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, self._img_size[0], self._img_size[1], 0, GL_RGB, GL_FLOAT, None)
		
		# depth texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, self._img_size[0], self._img_size[1], 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		
		# edge texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._img_size[0], self._img_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
		# RGB-ASCII texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._text_size[0], self._text_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
	# }
	
	def _draw_dummy(self, instances = 1, _vao = GLuint(0)):
		gl = self.gl
		if not _vao.value:
			gl.glGenVertexArrays(1, _vao)
		# }
		gl.glBindVertexArray(_vao);
		gl.glDrawArraysInstanced(GL_POINTS, 0, 1, instances);
		gl.glBindVertexArray(0);
	# }
	
	def _draw_ascii_grid(self, w, h, _cache = {}):
		# w, h are quads
		gl = self.gl
		vao = _cache.get((w, h), None)
		if not vao:
			vao = GLuint(0)
			gl.glGenVertexArrays(1, vao)
			
			ibo = GLuint(0)
			vbo_pos = GLuint(0)
			
			gl.glGenBuffers(1, ibo)
			gl.glGenBuffers(1, vbo_pos)
			
			idx = []
			pos = []
			
			for y in xrange(h + 1):
				for x in xrange(w + 1):
					pos.append(2 * x / w - 1)
					pos.append(2 * y / h - 1)
					# only 2D!
				# }
			# }
			
			def get_index(x, y):
				if x < 0 or x > w: return 0
				if y < 0 or y > h: return 0
				return (w + 1) * y + x
			# }
			
			for y in xrange(h):
				for x in xrange(w):
					# 3---2 //
					# | /   //
					# 1     //
					idx.append(get_index(x, y))
					idx.append(get_index(x + 1, y + 1))
					idx.append(get_index(x, y + 1))
					#     3 //
					#   / | //
					# 1---2 //
					idx.append(get_index(x, y))
					idx.append(get_index(x + 1, y))
					idx.append(get_index(x + 1, y + 1))
				# }
			# }
			
			gl.glBindVertexArray(vao)
			
			# upload indices
			gl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
			gl.glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(idx) * ctypes.sizeof(GLuint), c_array(GLuint, idx), GL_STATIC_DRAW)
			
			# upload positions
			gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_pos)
			gl.glBufferData(GL_ARRAY_BUFFER, len(pos) * ctypes.sizeof(GLfloat), c_array(GLfloat, pos), GL_STATIC_DRAW)
			gl.glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
			gl.glEnableVertexAttribArray(0)
			
			_cache[(w, h)] = vao
		# }
		
		gl.glBindVertexArray(vao)
		gl.glProvokingVertex(GL_FIRST_VERTEX_CONVENTION)
		gl.glDrawElements(GL_TRIANGLES, 6 * w * h, GL_UNSIGNED_INT, None)
		gl.glBindVertexArray(0)
	# }
	
	def render(self, w, h, game, _cache = {}):
		gl = self.gl
		
		if (w, h) == (0, 0): return
		
		self._resize(w, h)
		
		# render game to color + depth framebuffer
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_main)
		gl.glClearColor(1.0, 1.0, 1.0, 1.0)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		gl.glEnable(GL_DEPTH_TEST)
		gl.glDepthFunc(GL_LESS)
		gl.glViewport(0, 0, *self._img_size)
		
		game.render(gl, *self._img_size)
		
		gl.glDisable(GL_DEPTH_TEST)
		
		# TODO do edge detection
		# output texture is (original) color + edginess
		
		# ASCII conversion
		# output texture is (new) color + ascii code
		
		prog_ascii = _cache.get('prog_ascii', None)
		if not prog_ascii: 
			prog_ascii = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_ascii_source)
			_cache['prog_ascii'] = prog_ascii
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color) # TODO edge
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glActiveTexture(GL_TEXTURE2)
		gl.glBindTexture(GL_TEXTURE_1D, self._tex_lum2ascii)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_text)
		gl.glViewport(0, 0, *self._text_size)
		
		gl.glUseProgram(prog_ascii)
		gl.glUniform2i(gl.glGetUniformLocation(prog_ascii, 'char_size'), *self._char_size)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_color'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_depth'), 1)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_lum2ascii'), 2)
		
		self._draw_dummy()
		
		# TODO render strings into ascii texture (glTexSubImage2D?)
		
		# real output: convert ASCII codes to text via font atlas
		
		prog_text = _cache.get('prog_text', None)
		if not prog_text:
			prog_text = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER), _shader_text_source)
			_cache['prog_text'] = prog_text
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_font)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		gl.glViewport(0, 0, w, h)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		gl.glUseProgram(prog_text)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_text'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_font'), 1)
		
		self._draw_ascii_grid(*self._text_size)
		
		gl.glUseProgram(0)
	# }
	
	def draw_text(self, row, col, text, color = (0.0, 0.0, 0.0)):
		pass
	# }
	
# }






















