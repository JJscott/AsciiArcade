
from __future__ import division

import pygame
import ctypes
import itertools
from pygloo import *
from simpleShader import makeProgram

_shader_fullscreen_source = '''

// vertex shader
#ifdef _VERTEX_

flat out int instanceID;

void main() {
	instanceID = gl_InstanceID;
}

#endif

// geometry shader
#ifdef _GEOMETRY_

layout(points) in;
layout(triangle_strip, max_vertices = 3) out;

flat in int instanceID[];

out vec2 fullscreen_tex_coord;
flat out int fullscreen_layer;

void main() {
	// output a single triangle that covers the whole screen
	// if instanced, set layer to instance id
	
	gl_Position = vec4(3.0, 1.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(2.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, 1.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(0.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, -3.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(0.0, -1.0);
	EmitVertex();
	
	EndPrimitive();
	
}

#endif

// fragment shader
#ifdef _FRAGMENT_

in vec2 fullscreen_tex_coord;
flat in int fullscreen_layer;

// main() should be implemented by includer

#endif
'''

_shader_font_source = _shader_fullscreen_source + '''

uniform sampler2D sampler_fontatlas;

#ifdef _FRAGMENT_

out vec4 frag_color;

void main() {
	vec2 uv = mod(vec2(1.0, -1.0) * fullscreen_tex_coord, vec2(1.0));
	int codepoint = fullscreen_layer;
	int ix = codepoint & 0xF;
	int iy = codepoint >> 4;
	frag_color = texture(sampler_fontatlas, (vec2(ix, iy) + uv) / 16.0);
}

#endif
'''

_shader_edge_source = _shader_fullscreen_source + '''

uniform sampler2D sampler_color;
uniform sampler2D sampler_depth;

uniform mat4 proj_inv;

#ifdef _FRAGMENT_

// output is RGB-edge
out vec4 frag_color;

const vec2[] deltas = vec2[](vec2(1, 0), vec2(0, 1), vec2(-1, 0), vec2(0, -1));

float texture_depth(vec2 uv) {
	float d0 = texture(sampler_depth, uv).r;
	d0 = d0 * 2.0 - 1.0;
	vec4 p = proj_inv * vec4(0, 0, d0, 1);
	p /= p.w;
	return -p.z;
}

void main() {
	
	bool edgy = false;
	
	// edges from depth buffer
	float depth = texture_depth(fullscreen_tex_coord);
	float depth_l = -depth;
	for (int i = 0; i < deltas.length(); i++) {
		depth_l += 0.25 * texture_depth(fullscreen_tex_coord + deltas[i] / vec2(textureSize(sampler_color, 0)));
	}
	edgy = edgy || abs(depth_l / depth) > 0.03;
	
	// passthrough color, add edginess
	frag_color = vec4(texture(sampler_color, fullscreen_tex_coord).rgb, mix(0.0, 1.0, edgy));
}

#endif
'''

_shader_ascii_source = _shader_fullscreen_source + '''

uniform ivec2 char_size;
uniform sampler2D sampler_color; // RGB-edge
uniform sampler2D sampler_depth;
uniform sampler1D sampler_lum2ascii;
uniform vec3 fgcolor;

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
	frag_ascii = vec4(fgcolor, (float(codepoint) + 0.5) / 255.0);
}

#endif
'''

_shader_dtext_source = '''

uniform ivec2 viewport_size;

#ifdef _VERTEX_

layout(location = 0) in vec4 pos;

// RGB-ASCII
layout(location = 1) in vec4 color;

out VertexData {
	vec4 color;
} vertex_out;

void main() {
	vec2 origin = pos.zw;
	gl_Position = vec4(mod((pos.xy + 0.5) / vec2(viewport_size) + origin, 1.0) * 2.0 - 1.0, 0.0, 1.0);
	vertex_out.color = color;
}

#endif

#ifdef _FRAGMENT_

in VertexData {
	vec4 color;
} vertex_in;

out vec4 frag_color;

void main() {
	frag_color = vertex_in.color;
}

#endif
'''

_shader_text_source = '''

uniform sampler2D sampler_text;
uniform sampler2DArray sampler_font;

// passthrough for testing
uniform sampler2D sampler_color;

uniform vec3 bgcolor;

const vec2 char_uvlim = vec2(0.75, 1.0);

#ifdef _VERTEX_

layout(location = 0) in vec2 pos;

out vec2 fullscreen_tex_coord;
flat out vec3 textcolor;
flat out ivec2 textpos;
flat out int codepoint;

void main() {
	gl_Position = vec4(pos, 0.0, 1.0);
	fullscreen_tex_coord = vec2(0.5) + 0.5 * pos;
	textpos = ivec2(floor(fullscreen_tex_coord * vec2(textureSize(sampler_text, 0)) + 0.5));
	vec4 rgba = texelFetch(sampler_text, textpos, 0);
	textcolor = rgba.rgb;
	codepoint = int(floor(rgba.a * 255.0));
}

#endif

#ifdef _FRAGMENT_

in vec2 fullscreen_tex_coord;
flat in vec3 textcolor;
flat in ivec2 textpos;
flat in int codepoint;

out vec4 frag_color;

void main() {
	vec2 fsuv = fullscreen_tex_coord * vec2(textureSize(sampler_text, 0));
	// if fragment real position is outside this 'cell', we need to deal with it
	vec2 uv = clamp(fsuv - vec2(textpos), vec2(0.0), vec2(1.0));
	// manual grad to avoid discontinuities
	float f = textureGrad(sampler_font, vec3(uv * char_uvlim, codepoint), dFdx(fsuv * char_uvlim), dFdy(fsuv * char_uvlim)).r;
	// use font texture to interpolate between bg and fg
	frag_color = vec4(mix(bgcolor, textcolor, vec3(f)), 1.0);
	//frag_color = vec4(vec3(texture(sampler_color, fullscreen_tex_coord).a), 1.0);
}

#endif

'''



class AsciiRenderer:
	
	def __init__(self, gl):
		self.gl = gl
		
		self._img_size = (1, 1)
		
		# text screen buffer (w, h)
		self._text_size = (0, 80)
		
		# colors
		self.fgcolor = (0, 0, 0)
		self.bgcolor = (1, 1, 1)
		
		# char size in pixels (w, h)
		self._char_size = (6, 8)
		
		# font texture
		self._init_font()
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# luminance to ASCII texture (1D)
		lumstr = '#BXEOCxeoc::..  '
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
		self._dtext_pos = [] # x, y, screen origin
		self._dtext_color = [] # r, g, b, ascii
		
		self._vao_dtext = GLuint(0)
		self._vbo_dtext_pos = GLuint(0) # x, y, screen origin
		self._vbo_dtext_color = GLuint(0) # r, g, b, ascii
		
		gl.glGenVertexArrays(1, self._vao_dtext)
		gl.glGenBuffers(1, self._vbo_dtext_pos)
		gl.glGenBuffers(1, self._vbo_dtext_color)
		
		gl.glBindVertexArray(self._vao_dtext)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_pos)
		gl.glBufferData(GL_ARRAY_BUFFER, 4 * ctypes.sizeof(GLfloat), c_array(GLfloat, (0, 0, 0, 0)), GL_STREAM_DRAW)
		gl.glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)
		gl.glEnableVertexAttribArray(0)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_color)
		gl.glBufferData(GL_ARRAY_BUFFER, 4 * ctypes.sizeof(GLfloat), c_array(GLfloat, (0, 0, 0, 0)), GL_STREAM_DRAW)
		gl.glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
		gl.glEnableVertexAttribArray(1)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, 0)
		gl.glBindVertexArray(0)
		
	# }
	
	def _init_font(self):
		gl = self.gl
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# setup fbo to draw font into array texture
		fbo = GLuint(0)
		tex_font = GLuint(0)
		
		gl.glGenFramebuffers(1, fbo)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo)
		
		gl.glGenTextures(1, tex_font)
		
		gl.glBindTexture(GL_TEXTURE_2D_ARRAY, tex_font)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_R8, 64, 64, 256, 0, GL_RED, GL_FLOAT, None)
		gl.glFramebufferTexture(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex_font, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# load font atlas
		fontimg = pygame.image.load('./res/font.png')
		tex_font_atlas = GLuint(0)
		gl.glGenTextures(1, tex_font_atlas)
		
		gl.glBindTexture(GL_TEXTURE_2D, tex_font_atlas)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST) # we won't be downscaling
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		# this feels disgusting
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, fontimg.get_width(), fontimg.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.create_string_buffer(pygame.image.tostring(fontimg, 'RGB')))
		
		# render the atlas into a texture array
		prog = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_font_source)
		
		gl.glViewport(0, 0, 64, 64)
		gl.glDisable(GL_DEPTH_TEST)
		
		gl.glUseProgram(prog)
		gl.glUniform1i(gl.glGetUniformLocation(prog, 'sampler_fontatlas'), 0)
		
		self._draw_dummy(instances=256)
		
		gl.glUseProgram(0)
		gl.glDeleteFramebuffers(1, fbo)
		gl.glDeleteTextures(1, tex_font_atlas)
		
		gl.glGenerateMipmap(GL_TEXTURE_2D_ARRAY)
		self._tex_font = tex_font
		
	# }
	
	def resize(self, w, h, _last = [(1, 1)]):
		'''
		Resize internal textures for a specific screen size.
		'''
		if (w, h) == _last[0]: return
		_last[0] = (w, h)
		#print 'resize motherfucker!'
		
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
	
	def _draw_direct_text(self, _cache = {}):
		gl = self.gl
		
		# if no text, do nothing
		if not len(self._dtext_pos): return
		
		#print self._dtext_pos
		#print self._dtext_color
		
		# upload new text data
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_pos)
		gl.glBufferData(GL_ARRAY_BUFFER, len(self._dtext_pos) * ctypes.sizeof(GLfloat), c_array(GLfloat, self._dtext_pos), GL_STREAM_DRAW)
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_color)
		gl.glBufferData(GL_ARRAY_BUFFER, len(self._dtext_color) * ctypes.sizeof(GLfloat), c_array(GLfloat, self._dtext_color), GL_STREAM_DRAW)
		
		prog_dtext = _cache.get('prog_dtext', None)
		if not prog_dtext:
			prog_dtext = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER), _shader_dtext_source)
			_cache['prog_dtext'] = prog_dtext
		# }
		
		gl.glUseProgram(prog_dtext)
		
		gl.glUniform2i(gl.glGetUniformLocation(prog_dtext, 'viewport_size'), *self._text_size)
		
		gl.glBindVertexArray(self._vao_dtext)
		gl.glDrawArrays(GL_POINTS, 0, len(self._dtext_pos) // 2)
		gl.glBindVertexArray(0)
		
		# clear text after drawing
		self._dtext_pos = []
		self._dtext_color = []
	# }
	
	def render(self, w, h, game, _cache = {}):
		gl = self.gl
		
		# temp
		self.draw_text(0, 0, 'Hello World!\nBastards, the lot of you.', color = (0.5, 0, 1), screenorigin = (0.5, 0.5), textorigin = (0.5, 0.5), align = 'c')
		
		if (w, h) == (0, 0): return
		
		self.resize(w, h)
		
		# render game to color + depth framebuffer
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_main)
		gl.glClearColor(1.0, 1.0, 1.0, 1.0)
		gl.glClearDepth(1.0)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		gl.glEnable(GL_DEPTH_TEST)
		gl.glDepthFunc(GL_LESS)
		gl.glViewport(0, 0, *self._img_size)
		
		proj = game.render(gl, *self._img_size)
		
		gl.glDisable(GL_DEPTH_TEST)
		
		# edge detection
		# output texture is (original) color + edginess
		
		prog_edge = _cache.get('prog_edge', None)
		if not prog_edge:
			prog_edge = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_edge_source)
			_cache['prog_edge'] = prog_edge
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_edge)
		gl.glViewport(0, 0, *self._img_size)
		
		gl.glUseProgram(prog_edge)
		gl.glUniform1i(gl.glGetUniformLocation(prog_edge, 'sampler_color'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_edge, 'sampler_depth'), 1)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog_edge, 'proj_inv'), 1, True, c_array(GLfloat, proj.inverse().flatten()))
		
		self._draw_dummy()
		
		# ASCII conversion
		# output texture is (new) color + ascii code
		
		prog_ascii = _cache.get('prog_ascii', None)
		if not prog_ascii: 
			prog_ascii = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_ascii_source)
			_cache['prog_ascii'] = prog_ascii
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
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
		gl.glUniform3f(gl.glGetUniformLocation(prog_ascii, 'fgcolor'), *self.fgcolor)
		
		self._draw_dummy()
		
		# render strings into ascii texture
		self._draw_direct_text()
		
		# real output: convert ASCII codes to text via font atlas
		
		prog_text = _cache.get('prog_text', None)
		if not prog_text:
			prog_text = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER), _shader_text_source)
			_cache['prog_text'] = prog_text
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D_ARRAY, self._tex_font)
		gl.glActiveTexture(GL_TEXTURE2)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		gl.glViewport(0, 0, w, h)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		gl.glUseProgram(prog_text)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_text'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_font'), 1)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_color'), 2) # passthrough for testing
		gl.glUniform3f(gl.glGetUniformLocation(prog_text, 'bgcolor'), *self.bgcolor)
		
		self._draw_ascii_grid(*self._text_size)
		
		gl.glUseProgram(0)
	# }
	
	def draw_text(self, x, y, text, chardelta = (1, 0), linedelta = (0, -1), align = 'l', textorigin = (0, 0), screenorigin = (0, 0), color = None):
		'''
		Draw some (coloured) text. Align text region origin with screen origin, then offset text position by x,y
		
		Parameters:
			x, y           Offset from aligned origins, in characters
			text           Text to draw (str)
			chardelta      Position delta between characters within a line of text (units are characters); default is (1,0)
			linedelta      Position delta between lines of text (units are characters); default is (0,-1)
			align          Alignment within lines; one of 'l' (left / line start), 'c' (centre), 'r' (right / line end); default is 'l'
			textorigin     Origin point within text region; range is [0,1]; default is (0,0)
			screenorigin   Origin point on screen; range is [0,1]; default is (0,0)
			color          Text colour; default is current foreground colour
			
		'''
		color = self.fgcolor if color is None else color
		color = tuple(color)[:3]
		chardelta = tuple(chardelta)[:2]
		linedelta = tuple(linedelta)[:2]
		textorigin = tuple(textorigin)[:2]
		screenorigin = tuple(screenorigin)[:2]
		lines = str(text).split('\n')
		# width and height of text
		tw = max(map(len, lines))
		th = len(lines)
		# prepare alignment
		padfactor = { 'c' : 0.5, 'r' : 1.0 }.get(align, 0.0)
		padsizes = [padfactor * (tw - len(line)) for line in lines]
		# text origin
		x -= tw * textorigin[0]
		y -= th * textorigin[1]
		# process lines...
		from itertools import chain, izip, imap, repeat
		for line, psize in izip(lines, padsizes):
			# align
			x0 = x + chardelta[0] * psize
			y0 = y + chardelta[1] * psize
			# write buffers
			self._dtext_pos.extend(chain.from_iterable(izip(*([(x0 + chardelta[0] * f for f in xrange(len(line))), (y0 + chardelta[1] * f for f in xrange(len(line)))] + [repeat(f) for f in screenorigin]))))
			self._dtext_color.extend(chain.from_iterable(izip(*([repeat(f, len(line)) for f in color] + [imap(lambda c: (ord(c) + 0.5) / 255.0, line)]))))
			# newline
			x += linedelta[0]
			y += linedelta[1]
		# }
		
	# }
	
# }






















