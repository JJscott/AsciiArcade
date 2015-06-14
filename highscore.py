
# Pygame
# 
from pygame.locals import *
import pygame
import ascii

from arcade_menu import ArcadeMenuState

import re

class HighScoreState(object):
	"""docstring for HighScoreState"""
	def __init__(self, score, state):
		super(HighScoreState, self).__init__()
		self.pause = 0
		self.path = 'Highscore.txt'
		f = open(self.path,'r')
		self.entries = []
		for line in f:
			line = re.sub('\n','',line)
			string = re.split('\t', line)
			self.entries.append(string)
		f.close
		self.selected = 0
		self.alphabet = map(chr, range(65, 91)) + [' ']
		self.maxsize = len(self.alphabet)
		self.pressed = False
		self.delay = 0
		self.name = ["A","A","A","A"]
		self.selectindex = 0
		self.selectlocation = 0.425
		self.score = score
		self.state = state
		pygame.mixer.music.play(-1)

	# Game logic
	#
	def tick(self, pressed):
		self.pause +=1
		if self.pause > 50:
			if pressed[K_SPACE]:
				return ArcadeMenuState()
		if self.state==0:
			if pressed[K_UP]:
				if not self.pressed and self.delay <= 0:
					self.selected += 1
					self.selected %= self.maxsize
				self.pressed = True
				
			elif pressed[K_DOWN]:
				if not self.pressed and self.delay <= 0:
					self.selected -= 1
					self.selected %= self.maxsize
				self.pressed = True
				
			elif pressed[K_RETURN]:
				if not self.pressed and self.delay <= 0:
					if self.selectindex < 4:
						self.name[self.selectindex] = self.alphabet[self.selected]
						self.selectindex += 1
						self.selectlocation += 0.05
						self.selected = 0
				self.pressed = True
				
			elif pressed[K_DELETE]:
				if not self.pressed and self.delay <= 0:
					if self.selectindex > 0:
						self.selectindex -= 1
						self.name[self.selectindex] = "A"
						self.selectlocation -= 0.05
						self.selected = 0
				self.pressed = True
				
			else:
				self.pressed = False
			self.delay -= 1
			
			if self.selectindex >= 4:
				#correct formatting
				self.name = str(''.join(self.name))
				self.entries.append([self.name,self.score])
				for entry in self.entries:
					entry[1] = int(entry[1])
				
				#sort entries
				self.entries.sort(key=lambda tup: tup[1])
				self.entries.reverse()
				
				#write to file
				f = open(self.path,"w")
				for entry in self.entries:
					f.write( str(entry[0]) + str("\t") + str(entry[1]) + str('\n') )
				
				#reopen and reread
				f = open(self.path,'r')
				self.entries = []
				for line in f:
					line = re.sub('\n','',line)
					string = re.split('\t', line)
					self.entries.append(string)
				self.state = 2


	# Render logic
	#
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r and self.state==0:
			titleArt = ascii.wordart('HIGHSCORE', 'big')
			ascii_r.draw_text(titleArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5), align = 'c')
			
			if self.pause % 50 < 25 or self.pressed==True:
				selectedArt = ascii.wordart(self.alphabet[self.selected], 'big')
				ascii_r.draw_text(selectedArt, color = (0.333, 1, 1), screenorigin = (self.selectlocation, 0.5), textorigin = (0.5, 0.5), align = 'c')
			
			for i in range(0,len(self.name)):
				if not i == self.selectindex:
					nameArt = ascii.wordart(self.name[i], 'big')
					ascii_r.draw_text(nameArt, color = (0.333, 1, 1), screenorigin = (0.425+(0.05*i), 0.5), textorigin = (0.5, 0.5), align = 'c')
			
			
			scoreArt = ascii.wordart("SCORE: "+str(self.score), 'big')
			ascii_r.draw_text(scoreArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.1), textorigin = (0.5, 0.5), align = 'c')
			
		if ascii_r and self.state>=1:
			#ascii_r.draw_text("Highscorse har plz!", color = (1, 1, 1), screenorigin = (0.5, 0.5), textorigin = (0.5, 0.5), align = 'c')
			
			titleArt = ascii.wordart('HIGHSCORE', 'big')
			ascii_r.draw_text(titleArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5), align = 'c')
			
			count = 0
			for entry in self.entries:
				nameArt = ascii.wordart(entry[0],'big')
				ascii_r.draw_text(nameArt, color = (1, 0.333, 1), screenorigin = (0.25, 0.7-(0.1*count)), textorigin = (0.5, 0.5), align = 'l')
				
				scoreArt = ascii.wordart(entry[1],'big')
				ascii_r.draw_text(scoreArt, color = (1, 0.333, 1), screenorigin = (0.75, 0.7-(0.1*count)), textorigin = (0.5, 0.5), align = 'r')
				count+=1
			if self.state==1:
				yourscoreArt = ascii.wordart("YOUR SCORE: ",'big')
				ascii_r.draw_text(yourscoreArt, color = (1, 0.333, 1), screenorigin = (0.5, 0.05), textorigin = (0.5, 0.5), align = 'c')
				yourscoreNumArt = ascii.wordart(str(self.score),'big')
				ascii_r.draw_text(yourscoreNumArt, color = (1, 0.333, 1), screenorigin = (0.75, 0.05), textorigin = (0.5, 0.5), align = 'r')
			

