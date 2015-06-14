

# Pygame
# 
import pygame
from pygame.locals import *



C_POS_X = '+x'
C_NEG_X = '-x'
C_POS_Y = '+y'
C_NEG_Y = '-y'
C_TRIGGER = 'trigger'

class Controller(object):

	"""docstring for Controller"""
	def __init__(self):
		super(Controller, self).__init__()
		pygame.init()

		self.down = pygame.key.get_pressed()
		self.pressed = [False for _ in self.down]
		self.released = [False for _ in self.down]

		self.c_values = [C_POS_X, C_NEG_X, C_POS_Y, C_NEG_Y, C_TRIGGER]
		self.c_down = {k:False for k in self.c_values}
		self.c_pressed = {k:False for k in self.c_down}
		self.c_released = {k:False for k in self.c_down}

		self._x_axis = 0
		self._y_axis = 0

		self.threshold = 0.5

		# Get joystick controls
		self.joystick = None
		if pygame.joystick.get_count():
			self.joystick = pygame.joystick.Joystick(0)
			self.joystick.init()

	def tick(self):
		# Keyboard 
		#
		new_down = pygame.key.get_pressed()
		self.pressed = [(n and not o) for (n, o) in zip(new_down, self.down)]
		self.released = [(not n and o) for (n, o) in zip(new_down, self.down)]
		self.down = new_down

		t = self.threshold
		if self.joystick is not None:
			x = self.joystick.get_axis( 0 )
			y = self.joystick.get_axis( 1 )
			s = self.joystick.get_button( 0 )
		else :
			x=0; y=0; s=0

		new_c_down = {	C_POS_X : x>t  or self.down[K_RIGHT],
						C_NEG_X : x<-t or self.down[K_LEFT],
						C_POS_Y : y>t  or self.down[K_DOWN],
						C_NEG_Y : y<-t or self.down[K_UP],
						C_TRIGGER : s>t or self.down[K_SPACE]}
		self.c_pressed = {k: (v and not self.c_down[k]) for (k, v) in new_c_down.items()}
		self.c_released = {k: (not v and self.c_down[k]) for (k, v) in new_c_down.items()}
		self.c_down = new_c_down

		self._x_axis = x + (1.0 if self.down[K_RIGHT] else 0.0) - (1.0 if self.down[K_LEFT] else 0.0)
		self._y_axis = y + (1.0 if self.down[K_DOWN] else 0.0) - (1.0 if self.down[K_UP] else 0.0)


	def key_pressed(self, key):
		if key in self.c_values:
			return self.c_pressed[key]
		return self.pressed[key]

	def key_released(self, key):
		if key in self.c_values:
			return self.c_released[key]
		return self.released[key]

	def key_down(self, key):
		if key in self.c_values:
			return self.c_down[key]
		return self.down[key]

	def x_axis(self):
		return self._x_axis

	def y_axis(self):
		return self._y_axis