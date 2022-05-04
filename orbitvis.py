
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
https://www.pygame.org/docs/ref/display.html#pygame.display.set_icon
https://www.geeksforgeeks.org/using-c-codes-in-python-set-1/?ref=lbp
https://sodocumentation.net/python/topic/9050/ctypes
https://stackoverflow.com/questions/11384015/

https://docs.python.org/3.8/library/ctypes.html?highlight=ctypes#module-ctypes
'''

from ctypes import *

import pygame
from pygame.locals import VIDEORESIZE
from pygame.locals import RESIZABLE

#0 : Colour based on where its initial vector lands on that iteration
#1 : Colour based on which vector goes to that spot
COLORMODE = 1

#0 : Use .orbits and .orbitsloc files to traverse orbits (slower, but easier to set up)
#1 : Use .so files to generate iterations on the fly (way, way faster)
CMODE = 1

modulus = 0
iterations = 0
F = ((c_int * 2) * 2)

vectorColors = []

#Holds the place in their orbit where each vector is at
#This prevents us from having to retraverse each orbit each time
# we want to iterate
vectorStates = []

if CMODE == 1:
	#Load C libraries, get function(s)
	#libc = cdll.msvcrt
	sharedC = CDLL("./objects/orbitvis.so", "r")
	orbit_step = sharedC.orbit_step
		
	#Defining the parameter types for the function
	orbit_step.argtypes = [c_int, c_int, POINTER((c_int * 2) * 2), c_int, c_int]
	orbit_step.restype = c_int

	#Get update matrix data
	try:
		matrixData = open("matrices/update.matrix")
	except OSError as error:
		print(error)
		pygame.quit()
		quit()

	data = matrixData.readline()
	data = matrixData.readline()
	row1 = (c_int*2)(int(data.split(" ")[0]), int(data.split(" ")[1]))
	data = matrixData.readline()
	row2 = (c_int*2)(int(data.split(" ")[0]), int(data.split(" ")[1]))

	matrixData.close()

	#This is our update matrix
	F  = ((c_int * 2) * 2)(row1, row2)
	
#Load config data
configData = open("config/system.config", "r")
for line in configData:
	#Should be error checking here, but oh well
	if line.split(" ")[0] == "mod":
		modulus = int(line.split(" ")[1])


#Optimise this later when I know what modules I need
pygame.init()

windowDimensions = [640, 480]
gridSize         = min(windowDimensions)
caption          = "ORBITVIS"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
windowCaption = pygame.display.set_caption(caption)
icon = pygame.image.load("index.jpg")
pygame.display.set_icon(icon)

print(modulus)


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
	'''Iterates each vector in the plane, stores their state
	in vectorStates.'''
	
	for x in range(0, modulus):
		for y in range(0, modulus):
			vectorStates[x][y] = nav_orbit(orbitData, orbitLocData, vectorStates[x][y], 1)


def draw_plane(surface):
	'''Draws the vector plane with vectors moved to their appropriate
	location after iters iterations.'''
	
	windowDisplay.fill(WHITE)

	for x in range(0, modulus):
		for y in range(0, modulus):
			if CMODE == 0:
				if COLORMODE == 0:
					pygame.draw.rect(
					surface,
					vectorColors[vectorStates[x][y][0]][vectorStates[x][y][1]],
					[(windowDimensions[0]-gridSize)/2 + x*(gridSize/modulus), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (y+1)*(gridSize/modulus),
					gridSize/modulus, gridSize/modulus]
					)
					
				elif COLORMODE == 1:
					pygame.draw.rect(
					surface,
					vectorColors[x][y],
					[(windowDimensions[0]-gridSize)/2 + vectorStates[x][y][0]*(gridSize/modulus), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (vectorStates[x][y][1]+1)*(gridSize/modulus),
					gridSize/modulus, gridSize/modulus]
					)
					
			elif CMODE == 1:
				#Convert C output to vector
				vectorKey = orbit_step(x, y, pointer(F), modulus, iterations)
				vectY = vectorKey % modulus
				vectX = (vectorKey - vectY)//modulus
				#print("Coords:", vectX, vectY)
				
				if COLORMODE == 0:
					pygame.draw.rect(
					surface,
					vectorColors[vectX][vectY],
					[(windowDimensions[0]-gridSize)/2 + x*(gridSize/modulus), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (y+1)*(gridSize/modulus),
					gridSize/modulus, gridSize/modulus]
					)
					
				elif COLORMODE == 1:
					pygame.draw.rect(
					surface,
					vectorColors[x][y],
					[(windowDimensions[0]-gridSize)/2 + vectX*(gridSize/modulus), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (vectY+1)*(gridSize/modulus),
					gridSize/modulus, gridSize/modulus]
					)


if CMODE == 0:				
	#Open orbit files
	try:
		orbits    = open("orbits/orbits.orbits", "r")
		orbitsloc = open("orbits/orbits.orbitsloc", "r")
	except OSError as error:
		print(error)
		pygame.quit()
		quit()

	#Determine the size/dimensions of our grid (the modulus)
	#The -1 ignores the \n at the end of the line
	modulus = len(orbitsloc.readline().split(" ")) - 1
	
	#Initialise state of each vector
	vectorStates = [[[x, y] for y in range(0, modulus)] for x in range(0, modulus)]

#Create array of colors for each vector
vectorColors = [[] for x in range(0, modulus)]
for x in range(0, modulus):
	for y in range(0, modulus):
		vectorColors[x].append((255*x//modulus, 255*y//modulus, 0))


while True:
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RIGHT: #Iterate
				iterations += 1
				print("Rendering iteration #", iterations, sep="")
				
				if CMODE == 0:
					iterate_plane(orbits, orbitsloc)

				draw_plane(windowDisplay)
				pygame.display.update()
				print("Done")
				
			elif event.key == pygame.K_LEFT: #Reset to 0th iteration
				if CMODE == 0:
					iterations = 0
				elif CMODE == 1:
					iterations -= 1
					if iterations < 0:
						iterations = 0
				
				if CMODE == 0:
					vectorStates = [[[x, y] for y in range(0, modulus)] for x in range(0, modulus)]
					
				print("Rendering iteration #", iterations, sep="")
				draw_plane(windowDisplay)
				pygame.display.update()
				print("Done")

		elif event.type == VIDEORESIZE: #When window is resized
			print("Rendering iteration #", iterations, sep="")
			windowDimensions = event.size
			gridSize = min(windowDimensions) #Keep vector grid a square
			windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
			
			draw_plane(windowDisplay)
			pygame.display.update()
			print("Done")
			
		elif event.type == pygame.QUIT:
			if CMODE == 0:
				orbits.close()
				orbitsloc.close()
			
			pygame.quit()
			quit()