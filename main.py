from math import radians 

# Pygloo imports
# 
import pygloo
from pygloo import *
from ctypes import *
from simpleShader import makeProgram

# Pygame
# 
import pygame
from pygame.locals import *


# Sort of useful mat libs
# 
from vec import *
import math

# The actual game
#
import stars
import ascii

asciirenderer = None


gl = None
game = None

def render_normal(w, h):

	gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
	
	# Clear the screen, and z-buffer
	gl.glClearColor(1.0, 1.0, 1.0, 1.0)
	gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	gl.glEnable(GL_DEPTH_TEST);
	gl.glDepthFunc(GL_LESS);
	gl.glViewport(0, 0, w, h);

	# Forward rendering
	game.render(gl, w, h)

	gl.glFinish();

# }

def render_ascii(w, h):
	asciirenderer.render(w, h, game)
# }

render = render_normal


def run():
	width = 800
	height = 600
	
	# Initilise pyGame and create window
	# 
	pygame.init()
	clock = pygame.time.Clock()
	screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)
	
	global gl
	gl = pygloo.init()

	global game
	game = stars.StarsGame(gl)
	
	global asciirenderer
	asciirenderer = ascii.AsciiRenderer(gl)
	
	# Enter game loop
	#
	while True:
		
		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return
			if event.type == VIDEORESIZE:
				width, height = event.size
				# this destroys and recreates the GL context; undesirable
				#screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)
			if event.type == KEYDOWN:
				if event.key == K_BACKSPACE:
					global render
					render = { render_normal : render_ascii, render_ascii : render_normal }[render]
				# }
			# }
		# }

		# Update the clock
		# 
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.
		
		# Get key presses and update
		# 
		pressed = pygame.key.get_pressed()
		game.tick(pressed)
		
		
		# Render
		# 
		if width > 0 and height > 0:
			render(width, height)

		# Flip the double buffer
		#
		pygame.display.flip()
	# }
# }



if __name__ == "__main__":
	run()