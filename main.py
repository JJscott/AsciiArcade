from math import radians 
import os

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
import game as ArcadeGame
from arcade_menu import ArcadeMenuState
import ascii

asciirenderer = None


gl = None
game = None

def render_normal(w, h):

	gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
	
	# Clear the screen, and z-buffer
	gl.glClearColor(0.0, 0.0, 0.0, 1.0)
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
	width = 1278
	height = 800
	tick = 16		#milliseconds
	
	# Initilise pyGame and create window
	# 
	pygame.init()
	clock = pygame.time.Clock()
	screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)

	global gl
	gl = pygloo.init()
	# gl._begin = True

	# Load geometry
	# 
	ArcadeGame.Assets.load_inst_geometry(gl, 	"bullet",		"Assets/Projectiles/ArrowHead.obj")
	ArcadeGame.Assets.load_inst_geometry(gl, 	"mine",			"Assets/Mine/Mine.obj")
	ArcadeGame.Assets.load_inst_geometry(gl, 	"minesphere",	"Assets/Mine/Sphere.obj")
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid1",	"Assets/Asteroids/Asteroid1.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid2",	"Assets/Asteroids/Asteroid2.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid3",	"Assets/Asteroids/Asteroid3.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid4",	"Assets/Asteroids/Asteroid4.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid5",	"Assets/Asteroids/Asteroid5.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid6",	"Assets/Asteroids/Asteroid6.obj", center=True)
	ArcadeGame.Assets.load_inst_geometry(gl, 	"asteroid7",	"Assets/Asteroids/Asteroid7.obj", center=True)
	ArcadeGame.Assets.load_geometry(gl, 		"ship",			"Assets/Ship/SHIP.obj")
	ArcadeGame.Assets.load_geometry(gl, 		"enemyship",	"Assets/EnemyShip/EnemyShip.obj")
	ArcadeGame.Assets.load_inst_geometry(gl, 	"sphere",		"Assets/Debug/Sphere/sphere.obj")

	# Load shader
	# 
	ArcadeGame.Assets.load_shader(gl, "bullet",		open("Assets/Shaders/bullet_shader.glsl").read())
	ArcadeGame.Assets.load_shader(gl, "mine",		open("Assets/Shaders/mine_shader.glsl").read())
	ArcadeGame.Assets.load_shader(gl, "asteroid",	open("Assets/Shaders/asteroid_shader.glsl").read())
	ArcadeGame.Assets.load_shader(gl, "ship",		open("Assets/Shaders/default_shader.glsl").read())
	ArcadeGame.Assets.load_shader(gl, "sphere",		open("Assets/Shaders/red_sphere_shader.glsl").read())


	# Load Sound
	# 
	# ArcadeGame.Assets.load_sound("tag", "Assets/Audio/Effects/something.wav")

	global game
	game = ArcadeMenuState()

	global asciirenderer
	asciirenderer = ascii.AsciiRenderer(gl)
	
	old_time = clock.tick()

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
				# this destroys and recreates the GL context on windows; undesirable
				if os.name != 'nt': screen = pygame.display.set_mode((width, height), HWSURFACE|OPENGL|DOUBLEBUF|RESIZABLE)
			if event.type == KEYDOWN:
				if event.key == K_BACKSPACE:
					global render
					render = { render_normal : render_ascii, render_ascii : render_normal }[render]
				# }
			# }
		# }
		
		# Get key presses and update
		# 
		pressed = pygame.key.get_pressed()
		ngame = game.tick(pressed)
		if ngame: game = ngame
		
		
		# Render
		# 
		if width > 0 and height > 0:
			render(width, height)

		# Flip the double buffer
		#
		pygame.display.flip()


		# Update the clock to keep constant time
		# 
		new_time = clock.tick()
		if old_time + tick > new_time:
			pygame.time.wait(new_time - (old_time + tick))
		old_time = new_time
	# }
# }



if __name__ == "__main__":
	run()