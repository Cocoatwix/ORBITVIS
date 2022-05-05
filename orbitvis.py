
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

#0 : Use .iteration file to traverse orbits (slower, but easier to set up)
#1 : Use .so files to generate iterations on the fly (way, way faster)
#2 : Same as #1, except current vector states are saved in vectorStates,
#    reducing the C computation needed. (potentially faster than #1 for large moduli,
#    though requires more memory).

#Default CMODE is #1
CMODE = 1

#0 : Colour based on where its initial vector lands on that iteration
#1 : Colour based on which vector goes to that spot

#Default CMODE is #1
COLORMODE = 1

MODULUS = 0
iterations = 0
F = ((c_int * 2) * 2)
MATRIXPATH = ""

ITERPATH = ""
OBJECTPATH = ""
iters = None

#Load config data
#Should be error checking here, but oh well
configData = open("config/system.config", "r")
for line in configData:
	splitline = line.split(" ")
	splitline[1] = splitline[1].rstrip()
	
	if splitline[0] == "mod":
		MODULUS = int(splitline[1])
		
	elif splitline[0] == "cmode":
		CMODE = int(splitline[1])
		
	elif splitline[0] == "colormode":
		COLORMODE = int(splitline[1])
		
	elif splitline[0] == "update":
		MATRIXPATH = splitline[1]
		
	elif splitline[0] == "objects":
		OBJECTPATH = splitline[1]
		
	elif splitline[0] == "iters":
		ITERPATH = splitline[1]


vectorColors = []

#Holds the place in their orbit where each vector is at
#This prevents us from having to retraverse each orbit each time
# we want to iterate
vectorStates = []

if CMODE in [1, 2]:
	#Load C libraries, get function(s)
	#libc = cdll.msvcrt
	sharedC = CDLL(OBJECTPATH + "/orbitvis.so", "r")
	C_step = sharedC.C_step
		
	#Defining the parameter types for the function
	C_step.argtypes = [c_int, c_int, POINTER((c_int * 2) * 2), c_int, c_int]
	C_step.restype = c_int

	#Get update matrix data
	try:
		matrixData = open(MATRIXPATH)
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


def step(iterData, vector):
	'''Uses .iteration file to find given vector's
	next step. Returns the found vector.'''
	
	lineNumber = 0
	for x in range(1, len(vector)+1):
		lineNumber += vector[-x]*MODULUS**(x-1)
	
	iterData.seek(0, 0)
	[iterData.readline() for x in range(0, lineNumber)]
	newVector = (iterData.readline().split(" "))[:-1]
	return [int(x) for x in newVector]

	
def iterate_plane(iterData):
	'''Iterates each vector in the plane, stores their state
	in vectorStates.'''
	
	for x in range(0, MODULUS):
		for y in range(0, MODULUS):
			if CMODE == 0:
				vectorStates[x][y] = step(iterData, vectorStates[x][y])
			elif CMODE == 2:
				vectKey = C_step(vectorStates[x][y][0], vectorStates[x][y][1], F, MODULUS, 1)
				vectY   = vectKey % MODULUS
				vectX   = (vectKey - vectY)//MODULUS
				vectorStates[x][y] = [vectX, vectY]


def draw_plane(surface):
	'''Draws the vector plane with vectors moved to their appropriate
	location after iters iterations.'''
	
	windowDisplay.fill(WHITE)
	
	#These two variables help remove white grid lines on the plot
	# resulting from floating point rounding inconsistencies
	xExtend = 0
	yExtend = 0

	for x in range(0, MODULUS):
		for y in range(0, MODULUS):
		
			#Calculating the appropriate adjustments to remove gridlines
			if x == MODULUS - 1:
				xExtend = 0
			else:
				xExtend = 1
				
			if y == MODULUS - 1:
				yExtend = 0
			else:
				yExtend = 1
				
			if CMODE in [0, 2]:
				if COLORMODE == 0:
					pygame.draw.rect(
					surface,
					vectorColors[vectorStates[x][y][0]][vectorStates[x][y][1]],
					[(windowDimensions[0]-gridSize)/2 + x*(gridSize/MODULUS), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (y+1)*(gridSize/MODULUS),
					gridSize//MODULUS + xExtend, gridSize//MODULUS + yExtend]
					)
					
				elif COLORMODE == 1:
					pygame.draw.rect(
					surface,
					vectorColors[x][y],
					[(windowDimensions[0]-gridSize)/2 + vectorStates[x][y][0]*(gridSize/MODULUS), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (vectorStates[x][y][1]+1)*(gridSize/MODULUS),
					gridSize//MODULUS + xExtend, gridSize//MODULUS + yExtend]
					)
					
			elif CMODE == 1:
				#Convert C output to vector
				vectorKey = C_step(x, y, pointer(F), MODULUS, iterations)
				vectY = vectorKey % MODULUS
				vectX = (vectorKey - vectY)//MODULUS
				#print("Coords:", vectX, vectY)
				
				if COLORMODE == 0:
					pygame.draw.rect(
					surface,
					vectorColors[vectX][vectY],
					[(windowDimensions[0]-gridSize)/2 + x*(gridSize/MODULUS), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (y+1)*(gridSize/MODULUS),
					gridSize//MODULUS + xExtend, gridSize//MODULUS + yExtend]
					)
					
				elif COLORMODE == 1:
					pygame.draw.rect(
					surface,
					vectorColors[x][y],
					[(windowDimensions[0]-gridSize)/2 + vectX*(gridSize/MODULUS), 
					windowDimensions[1] - (windowDimensions[1]-gridSize)/2 - (vectY+1)*(gridSize/MODULUS),
					gridSize//MODULUS + xExtend, gridSize//MODULUS + yExtend]
					)


if CMODE == 0:
	try:
		iters = open(ITERPATH, "r")
	except OSError as error:
		print(error)
		pygame.quit()
		quit()
	
	
#Initialise state of each vector, if needed
if CMODE in [0, 2]:
	vectorStates = [[[x, y] for y in range(0, MODULUS)] for x in range(0, MODULUS)]

#Create array of colors for each vector
vectorColors = [[] for x in range(0, MODULUS)]
for x in range(0, MODULUS):
	for y in range(0, MODULUS):
		vectorColors[x].append((255*x//MODULUS, 255*y//MODULUS, 0))


while True:
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RIGHT: #Iterate
				iterations += 1
				print("Rendering iteration #", iterations, sep="")
				
				if CMODE in [0, 2]:
					iterate_plane(iters)

				draw_plane(windowDisplay)
				pygame.display.update()
				print("Done")
				
			elif event.key == pygame.K_LEFT: #Reset to 0th iteration
				if CMODE in [0, 2]:
					iterations = 0
					vectorStates = [[[x, y] for y in range(0, MODULUS)] for x in range(0, MODULUS)]
					
				elif CMODE in 1:
					iterations -= 1
					if iterations < 0:
						iterations = 0
					
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
				iters.close()
			
			pygame.quit()
			quit()