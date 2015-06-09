




# Pygame
# 
from pygame.locals import *
import ascii




import ascii
from arcade_menu import ArcadeMenuState






class HighScoreState(object):
	"""docstring for HighScoreState"""
	def __init__(self,):
		super(HighScoreState, self).__init__()
		self.pause = 0



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
			ascii_r.draw_text("Highscorse har plz!", color = (1, 1, 1), screenorigin = (0.5, 0.5), textorigin = (0.5, 0.5), align = 'c')
		




