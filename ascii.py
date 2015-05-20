
from pygloo import *
import simpleShader

class AsciiRenderer:
	
	def __init__(self, gl):
		self.gl = gl
		
		self.image_size = (0,0)
		
		# main FBO
		self.fbo_main = GLuint(0)
		self.tex_color = GLuint(0)
		self.tex_depth = GLuint(0)
		
		# edge detection FBO
		self.fbo_edge = GLuint(0)
		self.tex_edge = GLuint(0)
		
		# ascii FBO
		self.fbo_ascii = GLuint(0)
		self.tex_ascii = GLuint(0)
		
	# }
	
	def render(self, w, h, game):
		gl = self.gl
		
		if (w, h) == (0, 0): return
		
		
		
		
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








