
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

https://www.tutorialspoint.com/How-can-I-create-a-directory-if-it-does-not-exist-using-Python
'''

from math import floor

from os.path import exists
from os import makedirs

from ctypes import *

import pygame
from pygame.locals import VIDEORESIZE
from pygame.locals import RESIZABLE

windowDimensions = [640, 480]

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

#Says whether we can click on vectors to obtain information about them
#Also activates hovering over vectors with the mouse
HOVERMODE = False

#When this is true, the program will generate all unique planes for
# the given system and screenshot them, putting them in the specified folder
#maxcaptures controls how many screenshots to take before stopping.
#If not set in the .config file, ORBITVIS will continue to take screenshots
# until it reaches the vectors' initial state again
CAPTUREMODE = False
maxcaptures = -1

MODULUS = 0
iterations = 0
F = ((c_int * 2) * 2)
MATRIXPATH = ""

ITERPATH = ""
OBJECTPATH = ""
CAPTUREPATH = ""
iters = None

#Load config data
#Should be error checking here, but oh well
configData = open("config/system.config", "r")
for line in configData:
	splitline = line.split(" ")
	
	if len(splitline) == 2:
		splitline[1] = splitline[1].rstrip()
	else:
		splitline[0] = splitline[0].rstrip()
	
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
		
	elif splitline[0] == "hover":
		HOVERMODE = True
		
	elif splitline[0] == "capture":
		CAPTUREMODE = True
		
	elif splitline[0] == "screenshots":
		CAPTUREPATH = splitline[1]
		
	elif splitline[0] == "maxcaptures":
		maxcaptures = int(splitline[1])
		
	elif splitline[0] == "inititer":
		iterations = int(splitline[1])
		
	elif splitline[0] == "sizeX":
		windowDimensions[0] = int(splitline[1])
		
	elif splitline[0] == "sizeY":
		windowDimensions[1] = int(splitline[1])
		
		
#Checking to see if screenshots directory exists
#If not, we'll make it for the user
if not exists(CAPTUREPATH):
	makedirs(CAPTUREPATH)


vectorColors = []

#Holds the place in their orbit where each vector is at
#This prevents us from having to retraverse each orbit each time
# we want to iterate
vectorStates = []

#This list holds all the vectors that land on a particular vector
# on the current iteration
vectorVisitors = [[[] for y in range(0, MODULUS)] for x in range(0, MODULUS)]

#Holds the vector we're pointing at with the mouse
vectorHover = [-1, -1]

if CMODE in [1, 2]:
	#Load C libraries, get function(s)
	#libc = cdll.msvcrt
	sharedC = CDLL(OBJECTPATH + "/orbitvis.so", "r")
	C_step = sharedC.C_step
	get_orbit_info = sharedC.get_orbit_info
		
	#Defining the parameter types for the function
	C_step.argtypes = [c_int, c_int, POINTER((c_int * 2) * 2), c_int, c_int]
	C_step.restype = c_int
	
	get_orbit_info.argtypes = [POINTER(c_int * 2), POINTER((c_int * 2) * 2), c_int]
	get_orbit_info.restype = c_int

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

gridSize         = min(windowDimensions)
caption          = "ORBITVIS"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 50, 255)

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
				
				
def is_initial_state():
	'''This function checks to see whether our vectors are back at their
	initial states. Returns True is they are, False otherwise.'''
	
	for x in range(0, MODULUS):
		for y in range(0, MODULUS):
			if vectorStates[x][y][0] != x or vectorStates[x][y][1] != y:
				return False
				
	return True


def draw_plane(surface):
	'''Draws the vector plane with vectors moved to their appropriate
	location after iters iterations.'''
	
	windowDisplay.fill(WHITE)
	
	#This list helps remove white grid lines on the plot
	# resulting from floating point rounding inconsistencies
	extend = []
	
	xStart = (windowDimensions[0] - gridSize) / 2
	yStart = (windowDimensions[1] + gridSize) / 2
	tileSize = gridSize/MODULUS
	
	vectorOfInterest = [] #This is used purely for code simplification
	coordX = 0
	coordY = 0
	colorX = 0
	colorY = 0

	for x in range(0, MODULUS):
		for y in range(0, MODULUS):

			#Getting appropriate vector for drawing the square
			if CMODE in [0, 2]:
				vectorOfInterest = vectorStates[x][y]
				
			elif CMODE == 1:
				#Convert C output to vector
				vectorKey = C_step(x, y, pointer(F), MODULUS, iterations)
				vectY = vectorKey % MODULUS
				vectX = (vectorKey - vectY)//MODULUS
				vectorOfInterest = [vectX, vectY]
				
			#Calculating the appropriate values for drawing the square
			extend = [1, 1]
			if COLORMODE == 0:
				if x == MODULUS - 1:
					extend[0] = 0
				if y == MODULUS - 1:
					extend[1] = 0
				
				coordX = xStart + x*tileSize
				coordY = yStart - (y+1)*tileSize
				colorX = vectorOfInterest[0]
				colorY = vectorOfInterest[1]
					
			elif COLORMODE == 1:
				if vectorStates[x][y][0] == MODULUS - 1:
					extend[0] = 0
				if vectorStates[x][y][1] == MODULUS - 1:
					extend[1] = 0
					
				coordX = xStart + vectorOfInterest[0]*tileSize
				coordY = yStart - (vectorOfInterest[1]+1)*tileSize
				colorX = x
				colorY = y

			#Finally, we draw the square
			pygame.draw.rect(
			surface,
			vectorColors[colorX][colorY],
			[coordX, coordY,
			tileSize + extend[0], tileSize + extend[1]])
					
	#Highlight the vector the user is pointing to
	#min() functions adjust the highlight's width to match underlying square
	if HOVERMODE and vectorHover[0] != -1:
		pygame.draw.rect(surface, BLUE, 
		[xStart + vectorHover[0]*tileSize,
		yStart - (vectorHover[1]+1)*tileSize,
		tileSize + min(1, MODULUS-1-vectorHover[0]), 
		tileSize + min(1, MODULUS-1-vectorHover[1])])
		
		
def make_caption():
	'''Returns a caption for the window containing iterations,
	the modulus, and the update matrix.'''
	cap = caption + " - i" + str(iterations) + "m" + str(MODULUS) + "F" + \
	str(F[0][0]) + str(F[0][1]) + str(F[1][0]) + str(F[1][1])
	
	return cap


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

#This allows the starting iteration to be nonzero	
for a in range(0, iterations):
	if CMODE in [0, 2]:
		iterate_plane(iters)
	draw_plane(windowDisplay)
pygame.display.set_caption(make_caption())


if CAPTUREMODE and CMODE in [0, 2]:
	#Generate initial plane
	draw_plane(windowDisplay)
	pygame.display.update()
	if CMODE == 1: #CMODE 1 iterates when draw_plane() is called
		iterations += 1
	
	pygame.display.set_caption(make_caption())
	pygame.image.save(windowDisplay, CAPTUREPATH + "/" + make_caption() + ".png")
	
	iterations += 1
	if (maxcaptures != -1):
		maxcaptures -= 1
	
	while (maxcaptures != 0):
		iterate_plane(iters)
		draw_plane(windowDisplay)
		pygame.display.update()
		pygame.display.set_caption(make_caption())
		pygame.image.save(windowDisplay, CAPTUREPATH + "/" + make_caption() + ".png")
		
		iterations += 1
		if (maxcaptures != -1):
			maxcaptures -= 1
			
		if is_initial_state():
			break
			
		#Allowing the user to quit whenever
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				if CMODE == 0:
					iters.close()
				pygame.quit()
				quit()
			
	pygame.quit()
	quit()


else:
	while True:
		for event in pygame.event.get():
		
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RIGHT: #Iterate
					iterations += 1
					
					if CMODE in [0, 2]:
						iterate_plane(iters)

					draw_plane(windowDisplay)
					pygame.display.update()
					pygame.display.set_caption(make_caption())
					
				elif event.key == pygame.K_LEFT: #Reset to 0th iteration
					if CMODE in [0, 2]:
						iterations = 0
						vectorStates = [[[x, y] for y in range(0, MODULUS)] for x in range(0, MODULUS)]
						
					elif CMODE == 1:
						iterations -= 1
						if iterations < 0:
							iterations = 0
						
					draw_plane(windowDisplay)
					pygame.display.update()
					pygame.display.set_caption(make_caption())
					
				elif event.key == pygame.K_DOWN:
					pygame.image.save(windowDisplay, make_caption() + ".png")
					

			elif event.type == VIDEORESIZE: #When window is resized
				windowDimensions = event.size
				gridSize = min(windowDimensions) #Keep vector grid a square
				windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
				
				draw_plane(windowDisplay)
				pygame.display.update()
				
			elif HOVERMODE and CMODE != 1 and event.type == pygame.MOUSEMOTION:
				#Left, right, top, bottom. Checking to see if mouse is on grid
				posX, posY = event.pos
				if (posX > (windowDimensions[0]-gridSize)/2 and
					posX < (windowDimensions[0]+gridSize)/2 and
					posY > (windowDimensions[1]-gridSize)/2 and
					posY < (windowDimensions[1]+gridSize)/2):
					
					posX = floor((posX - (windowDimensions[0]-gridSize)/2) / (gridSize/MODULUS))
					posY = floor((posY - (windowDimensions[1]-gridSize)/2) / (gridSize/MODULUS))
					
					#posX and posY are now the vector coordinates of where we're pointing
					vectorHover = [posX, MODULUS - posY - 1]
				else:
					vectorHover[0] = -1
					
				draw_plane(windowDisplay)
				pygame.display.update()
				
				#Give info about the vector clicked
			elif HOVERMODE and event.type == pygame.MOUSEBUTTONDOWN:
				if vectorHover[0] != -1:
					print("Vector clicked: <", vectorHover[0], ", ", vectorHover[1], ">", sep="")
					if CMODE in [0, 2]:
						print("Destination: <", vectorStates[vectorHover[0]][vectorHover[1]][0], 
						", ", vectorStates[vectorHover[0]][vectorHover[1]][1], ">", sep="")
						clickedVect = (c_int * 2)(vectorHover[0], vectorHover[1])
						print("Cycle length:", get_orbit_info(clickedVect, F, MODULUS))
						
					
			elif event.type == pygame.QUIT:
				if CMODE == 0:
					iters.close()
				
				pygame.quit()
				quit()
	