# Pygame
# 
from pygame.locals import *
from controller import *
import pygame
import ascii

import arcade_menu


class CreditsState(object):
	"""docstring for CreditsState"""
	def __init__(self):
		super(CreditsState, self).__init__()
		self.textarea = ascii.TextArea((120,80), 'small')
		self.textarea.scroll = -20
		self.textarea.align = 'c'
		self.textarea.showcursor = False
		with open('./CREDITS!.txt') as file:
			self.textarea.text = file.read()
		# }
	
	def tick(self, controller):
		if controller.key_pressed(C_TRIGGER):
			return arcade_menu.ArcadeMenuState()
		self.textarea.scroll += 0.19
		if self.textarea.scroll > self.textarea.line_count():
			self.textarea.scroll = -20
		# }
		self.textarea.invalidate()
		
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r:
			titleArt = ascii.wordart('CREDITS', 'big')
			ascii_r.draw_text(titleArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5))
			
			ascii_r.draw_text(self.textarea, textorigin=(0.5,0.5), screenorigin=(0.5,0.5))
			
			
			
		
	