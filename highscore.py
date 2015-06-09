




# Pygame
# 
from pygame.locals import *
import ascii




import ascii
from arcade_menu import ArcadeMenuState

import re




class HighScoreState(object):
	"""docstring for HighScoreState"""
	def __init__(self,):
		super(HighScoreState, self).__init__()
		self.pause = 0
		self.path = 'Highscore.txt'
		f = open(self.path,'r')
		self.entries = []
		for line in f:
			line = re.sub('\n','',line)
			print "line", line
			string = re.split('\t', line)
			print "string: ", string
			self.entries.append(string)
		f.close



	# Game logic
	#
	def tick(self, pressed):
		self.pause +=1
		if self.pause > 50:
			if pressed[K_SPACE]:
				return ArcadeMenuState()




	# Render logic
	#
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r:
			#ascii_r.draw_text("Highscorse har plz!", color = (1, 1, 1), screenorigin = (0.5, 0.5), textorigin = (0.5, 0.5), align = 'c')
			
			art1 = ascii.wordart('HIGHSCORE', 'big')
			ascii_r.draw_text(art1, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5), align = 'c')
			
			count = 0
			for entry in self.entries:
				nameArt = ascii.wordart(entry[0],'big')
				ascii_r.draw_text(nameArt, color = (1, 0.333, 1), screenorigin = (0.25, 0.7-(0.1*count)), textorigin = (0.5, 0.5), align = 'l')
				
				scoreArt = ascii.wordart(entry[1],'big')
				ascii_r.draw_text(scoreArt, color = (1, 0.333, 1), screenorigin = (0.75, 0.7-(0.1*count)), textorigin = (0.5, 0.5), align = 'r')
				count+=1
			

