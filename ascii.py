
from pygloo import *
import simpleShader

class AsciiRenderer:
	
	def __init__(self, gl):
		self.gl = gl
	# }
	
	def render(self, w, h, game):
		gl = self.gl
		
		# Clear the screen, and z-buffer
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		gl.glClearColor(1.0, 1.0, 1.0, 1.0)
		gl.glEnable(GL_DEPTH_TEST);
		gl.glDepthFunc(GL_LESS);
		gl.glViewport(0, 0, w, h);
		
		
		
	# }
	
# }








