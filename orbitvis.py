
'''
A simple GUI app for visualising
orbits made with LINCELLAUT.

May 3, 2022
'''

'''
The following resources were used as a reference:
https://www.pygame.org/wiki/WindowResizing
https://stackoverflow.com/questions/25937966/
https://docs.python.org/3.8/tutorial/inputoutput.html
https://docs.python.org/3.8/library/stdtypes.html?highlight=comparing%20strings#string-methods

'''

import pygame
from pygame.locals import VIDEORESIZE
from pygame.locals import RESIZABLE

#Optimise this later when I know what modules I need
pygame.init()

windowDimensions = [640, 480]
gridSize         = min(windowDimensions)
caption          = "ORBITVIS"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
windowCaption = pygame.display.set_caption(caption)

modulus = 0

vectorColors = []

#Holds the place in their orbit where each vector is at
#This prevents us from having to retraverse each orbit each time
# we want to iterate
vectorStates = []


def find_orbit(orbitData, orbitLocData, vector):
	'''Sets orbitData to the correct location for the
	given vector's orbit.'''
	
	vector = [int(vector[0]), int(vector[1])]
	
	#Go to correct position in .orbitsloc file
	orbitLocData.seek(0, 0) 
	[orbitLocData.readline() for x in range(0, vector[0])]
	
	#Get line number of our vector's orbit, goto correct line
	lineNumber = int(orbitLocData.readline().split(" ")[vector[1]])
	orbitData.seek(0, 0)
	[orbitData.readline() for x in range(0, lineNumber)]


def nav_orbit(orbitData, orbitLocData, vector, iters):
	'''Finds the correct vector in the orbit for the 
	number of iterations given and returns it.'''

	find_orbit(orbitData, orbitLocData, vector)
	
	vectInOrbit = str(vector[0]) + " " + str(vector[1])
	prevVectInOrbit = ""
	
	#Now, we navigate through the orbit
	while iters > 0:
		vectInOrbit = orbitData.readline()
		
		#If we got to the end of the listed orbit
		if (vectInOrbit == "-\n"):
			find_orbit(orbitData, orbitLocData, prevVectInOrbit.split(" "))
		else:
			prevVectInOrbit = vectInOrbit
			iters -= 1
	
	return [int(vectInOrbit.rstrip().split(" ")[x]) for x in range(0, 2)]
	
	
def iterate_plane(orbitData, orbitLocData):
	''''''
	pass
	

def draw_plane(surface):
	'''Draws the vector plane with vectors moved to their appropriate
	location after iters iterations.'''

	for x in range(0, modulus):
		for y in range(0, modulus):
			pygame.draw.rect(
			surface,
			vectorColors[vectorStates[x][y][0]][vectorStates[x][y][1]],
			[(windowDimensions[0]-gridSize)/2 + x*(gridSize/modulus), 
			windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (y+1)*(gridSize/modulus),
			gridSize/modulus, gridSize/modulus]
			)
	

#Open orbit files
try:
	orbits    = open("orbitdata/orbits.orbits", "r")
	orbitsloc = open("orbitdata/orbits.orbitsloc", "r")
except OSError as error:
	print(error)
	input()
	
	pygame.quit()
	quit()
	
#Determine the size/dimensions of our grid (the modulus)
#The -1 ignores the \n at the end of the line
modulus = len(orbitsloc.readline().split(" ")) - 1

#Create array of colors for each vector
vectorColors = [[] for x in range(0, modulus)]
for x in range(0, modulus):
	for y in range(0, modulus):
		vectorColors[x].append((255*x//modulus, 255*y//modulus, 0))
		
#Initialise state of each vector
vectorStates = [[[x, y] for y in range(0, modulus)] for x in range(0, modulus)]

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			orbits.close()
			orbitsloc.close()
			
			pygame.quit()
			quit()
			
		elif event.type == VIDEORESIZE: #When window is resized
			windowDimensions = event.size
			gridSize = min(windowDimensions) #Keep vector grid a square
			windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
			
			windowDisplay.fill(WHITE)
			draw_plane(windowDisplay)
			pygame.display.update()