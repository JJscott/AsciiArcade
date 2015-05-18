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



gl = pygloo.init()
game = stars.Stars()


def render(w, h):

	# Clear the screen, and z-buffer
	# 
	gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	gl.glClearColor(1.0, 1.0, 1.0, 0.0)
	gl.glEnable(GL_DEPTH_TEST);
	gl.glDepthFunc(GL_LESS);
	gl.glViewport(0, 0, w, h);

	# Forward rendering
	# 
	gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);

	game.render(gl, w, h)

	gl.glFinish();

# }


def run():
	width = 800
	height = 600
	
	# Initilise pyGame and create window
	# 
	pygame.init()
	clock = pygame.time.Clock()
	screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)

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
				screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)
		# }

		# Update the clock
		# 
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.
		
		# Get key presses and update
		# 
		pressed = pygame.key.get_pressed()
		game.tick(pressed)
		
		# if pressed[K_LEFT]:
		# 	rotation_direction.y = +1.0
		# elif pressed[K_RIGHT]:
		# 	rotation_direction.y = -1.0
				
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