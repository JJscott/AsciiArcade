
# Pygame
# 
from pygame.locals import *
from gameInput import *
import pygame
import ascii

from arcade_menu import ArcadeMenuState
from credits import CreditsState

import re

class HighScoreState(object):
	"""docstring for HighScoreState"""
	def __init__(self, score, state, show_credits=False):
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
		self.delay = 0
		self.name = ["A","A","A","A"]
		self.selectindex = 0
		self.startlocation = 0.425
		self.locationspacing = 0.05
		self.score = score
		self.state = state
		self.keyispressed = False
		self.done = False
		self.show_credits = show_credits
		pygame.mixer.music.play(-1)

	# Game logic
	#
	def tick(self, controller):
		self.pause +=1
		# if self.pause > 50:
		# 	if controller.key_pressed(C_TRIGGER):
		# 		return ArcadeMenuState()
		if self.state==0:
			if self.delay <= 0:
				if controller.key_down(C_POS_Y):
					if self.selectindex < 4:
						self.selected += 1
						self.selected %= self.maxsize
						self.delay = 40
						self.keyispressed = True
					
				elif controller.key_down(C_NEG_Y):
					if self.selectindex < 4:
						self.selected -= 1
						self.selected %= self.maxsize
						self.delay = 40
						self.keyispressed = True
						
				elif controller.key_down(C_POS_X):
					if self.selectindex < 4:
						self.name[self.selectindex] = self.alphabet[self.selected]
						if  self.selectindex < 3:
							self.selected = self.alphabet.index(self.name[self.selectindex+1])
							self.selectindex += 1
						elif self.selectindex == 3:
							self.done = True
						self.delay = 40
						self.keyispressed = True
					
				elif controller.key_down(C_NEG_X):
					if self.selectindex > 0:
						if self.done:
							self.done = False
						else:
							self.name[self.selectindex] = self.alphabet[self.selected]
							self.selected = self.alphabet.index(self.name[self.selectindex-1])
							self.selectindex -= 1
						self.delay = 40
						self.keyispressed = True
				else:
					self.keyispressed = False
					self.delay = 40
			self.delay -= 1
			
			if controller.key_pressed(C_TRIGGER):
				if self.done:
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
					self.pause = 0
		else:
			if controller.key_pressed(C_TRIGGER):
				if self.show_credits:
					return CreditsState()
				else:
					return ArcadeMenuState()


	# Render logic
	#
	def render(self, gl, w, h, ascii_r=None):
		if ascii_r:
			titleArt = ascii.wordart('HIGHSCORE', 'star_wars')
			ascii_r.draw_text(titleArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.9), textorigin = (0.5, 0.5), align = 'c')
			if self.state==0:
				if self.pause % 50 < 25 and self.done:
					selectedArt = ascii.wordart("[SHOOT] to continue", 'big')
					ascii_r.draw_text(selectedArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.3), textorigin = (0.5, 0.5), align = 'c')
					
				elif (self.pause % 50 < 25 or self.keyispressed) and not self.done:
					character = self.alphabet[self.selected]
					if character == " ":
						character = "_"
					selectedArt = ascii.wordart(character, 'big')
					ascii_r.draw_text(selectedArt, color = (0.333, 1, 1), screenorigin = (self.startlocation+(self.selectindex*0.05), 0.5), textorigin = (0.5, 0.5), align = 'c')
				
				for i in range(0,len(self.name)):
					if not i == self.selectindex or self.done:
						character = self.name[i]
						if character == " ":
							character = "_"
						nameArt = ascii.wordart(character, 'big')
						ascii_r.draw_text(nameArt, color = (0.333, 1, 1), screenorigin = (self.startlocation+(0.05*i), 0.5), textorigin = (0.5, 0.5), align = 'c')
				
				
				scoreArt = ascii.wordart("SCORE: "+str(self.score), 'big')
				ascii_r.draw_text(scoreArt, color = (0.333, 1, 1), screenorigin = (0.5, 0.1), textorigin = (0.5, 0.5), align = 'c')
				
			if self.state>=1:
				count = 0
				offset = (self.pause / 20) % len(self.entries)
				for entry in self.entries[offset:]:
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
				

