
from __future__ import division

import pygame
import ctypes
from pygloo import *
import simpleShader

class AsciiRenderer:
	
	def __init__(self, gl):
		self.gl = gl
		
		self._img_size = (1, 1)
		
		# text screen buffer (w, h)
		self._text_size = (0, 100)
		
		# char size in pixels (w, h)
		self._char_size = (6, 8)
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# font texture
		self._tex_font = GLuint(0)
		
		# this feels disgusting
		buf = ctypes.create_string_buffer(pygame.image.tostring(pygame.image.load('./res/font.png'), 'RGB'))
		
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_font)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_UNSIGNED_BYTE, buf)
		gl.glGenerateMipmap(GL_TEXTURE_2D)
		
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
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_color, 0)
		
		# depth texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, 1, 1, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self._tex_depth, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# edge detection FBO
		self._fbo_edge = GLuint(0)
		self._tex_edge = GLuint(0)
		
		gl.glGenFramebuffers(1, self._fbo_edge)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_edge)
		
		gl.glGenTextures(1, self._tex_edge)
		
		# edge texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_edge, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# ascii FBO
		self._fbo_ascii = GLuint(0)
		self._tex_ascii = GLuint(0) # RGB-ASCII
		
		gl.glGenFramebuffers(1, self._fbo_ascii)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_ascii)
		
		gl.glGenTextures(1, self._tex_ascii)
		
		# RGB-ASCII texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_ascii)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_ascii, 0)
		
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
		
		self._text_size = (int(self._text_size[1] * w / h), self._text_size[1])
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
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_ascii)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._text_size[0], self._text_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
	# }
	
	def render(self, w, h, game):
		gl = self.gl
		
		if (w, h) == (0, 0): return
		
		self._resize(w, h)
		
		
		# proper display
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
		gl.glClearColor(1.0, 1.0, 1.0, 1.0)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		gl.glEnable(GL_DEPTH_TEST);
		gl.glDepthFunc(GL_LESS);
		gl.glViewport(0, 0, w, h);
		
		
		
		
	# }
	
	def draw_text(self, row, col, text, color = (0.0, 0.0, 0.0)):
		pass
	# }
	
# }








