# Pygame
# 
from pygame.locals import *
import pygame
import ascii

from arcade_menu import ArcadeMenuState

import re

class CreditsState(object):
	"""docstring for CreditsState"""
	def __init__(self):
		super(CreditsState, self).__init__()
		self.pause = 0
		self.path = 'CREDITS.txt'
		f = open(self.path,'r')
		self.entries = []
		for line in f:
			line = re.sub('\n','',line)
			string = re.split('\t', line)
			self.entries.append(string)
		f.close
	
	def tick(self, pressed):
		self.pause +=1
		if self.pause > 50:
			if pressed[K_SPACE]:
				return ArcadeMenuState()
		
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r:
			titleArt = ascii.wordart('CREDITS', 'big')
			ascii_r.draw_text(titleArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5), align = 'c')
			
			for entry in self.entries:
				nameArt = ascii.wordart(entry[0],'big')
				ascii_r.draw_text(nameArt, color = (1, 0.333, 1), screenorigin = (0.25, 0.7-(0.1*count)), textorigin = (0.5, 0.5), align = 'l')
				
			
			
		
	