
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
from math import log

from os.path import exists
from os import makedirs

from ctypes import *

import pygame
from pygame.locals import VIDEORESIZE
from pygame.locals import RESIZABLE

#Optimise this later when I know what modules I need
pygame.init()

windowDimensions = [640, 480]

# "iterplane" : Use .so files to generate iterations on the fly
# "iterstate" : Same as "iterplane", except current vector states are saved in vectorStates,
#    reducing the C computation needed. (potentially faster for large moduli,
#    though requires more memory).
# "iterall"   : Iterates every possible matrix under the given modulus and displays
#    coloured squares based on the transient and cycle lengths of each matrix.
CMODE = "iterstate"

#repaint  : Colour based on where its initial vector lands on that iteration
#drag     : Colour based on which vector goes to that spot
#relative : Colour iterall tiles based on the relative cycle and translent lengths of others on the same screen
#rellog   : Same as above, but with a logarithmic curve added to the colouring
COLORMODE = "drag"

#mixed : Matrices are coloured based on cycle lengths and transient lengths
#solo  : Matrices are coloured based only on transient lengths
#none  : Matrices are coloured based only on cycle lengths
COLORTRANSIENT = "mixed"

#diag    : For iterall, arrow keys increment the diagonal entries
#nondiag : For iterall, arrow keys increment nondiagonal entries
ARRANGEMENT = "diag"

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

OBJECTPATH = ""
CAPTUREPATH = ""
iters = None

#For iterall mode, this holds the max omega and max tau value for each plane
#This helps us normalise the colour values
maxInfo = [0, 0] 

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
		CMODE = splitline[1]
		
	elif splitline[0] == "colormode":
		COLORMODE = splitline[1]
		
	elif splitline[0] == "arrangement":
		ARRANGEMENT = splitline[1]
		
	elif splitline[0] == "colortransient":
		COLORTRANSIENT = splitline[1]
		
	elif splitline[0] == "update":
		MATRIXPATH = splitline[1]
		
	elif splitline[0] == "objects":
		OBJECTPATH = splitline[1]
		
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
if not exists(CAPTUREPATH) and CAPTUREMODE:
	makedirs(CAPTUREPATH)
	
#Making sure we're using compatiable colouring modes
if CMODE in ["iterstate", "iterplane"] and COLORMODE not in ["repaint", "drag"]:
	print("Selected COLORMODE isn't compatiable with chosen CMODE.")
	print("Defaulting COLORMODE to drag...")
	COLORMODE = "drag"
	
elif CMODE in ["iterall"] and COLORMODE not in ["relative", "rellog"]:
	print("Selected COLORMODE isn't compatiable with chosen CMODE.")
	print("Defaulting COLORMODE to rellog...")
	COLORMODE = "rellog"


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

#Load C libraries, get function(s)
#libc = cdll.msvcrt
sharedC = CDLL(OBJECTPATH + "/orbitvis.so", "r")
C_step = sharedC.C_step
get_orbit_info = sharedC.get_orbit_info
get_orbit_info_array = sharedC.get_orbit_info_array

C_iterate_matrix = sharedC.C_iterate_matrix

#Defining the parameter types for the functions
C_step.argtypes = [c_int, c_int, POINTER((c_int * 2) * 2), c_int, c_int]
C_step.restype = c_int

get_orbit_info.argtypes = [POINTER(c_int * 2), POINTER((c_int * 2) * 2), c_int]
get_orbit_info.restype = c_int

get_orbit_info_array.argtypes = [POINTER((c_int * 2) * 2), c_int]
get_orbit_info_array.restype = c_int

C_iterate_matrix.argtypes = [POINTER((c_int * 2) * 2), POINTER((c_int * 2) * 2), c_int]
C_iterate_matrix.restype = None

#Get update matrix data
if CMODE != "iterall":
	try:
		matrixData = open(MATRIXPATH)
	except OSError as error:
		print(error)
		pygame.quit()
		quit()

	matrixData.readline()
	data = matrixData.readline()
	row1 = (c_int*2)(int(data.split(" ")[0]), int(data.split(" ")[1]))
	data = matrixData.readline()
	row2 = (c_int*2)(int(data.split(" ")[0]), int(data.split(" ")[1]))

	matrixData.close()
	
else:
	row1 = (c_int*2)(0, 0)
	row2 = (c_int*2)(0, 0)

#This is our update matrix
F  = ((c_int * 2) * 2)(row1, row2)

#When using iterplane, this array keeps track of what our
# matrix has iterated to.
currentF = ((c_int * 2) * 2)(row1, row2)

gridSize = min(windowDimensions)
caption  = "ORBITVIS"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE  = (50, 50, 255)

windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
windowCaption = pygame.display.set_caption(caption)
icon = pygame.image.load("index.jpg")
pygame.display.set_icon(icon)

def set_matrix(theMatrix, matrixArr):
	'''Sets the values for our update matrix, used with "iterall".'''
	
	for x in range(0, len(matrixArr)):
		for y in range(0, len(matrixArr[0])):
			theMatrix[x][y] = matrixArr[x][y]

	
def iterate_plane():
	'''Iterates each vector in the plane, stores their state
	in vectorStates (if needed).
	
	For CMODE "iterall", vectorStates holds the results of all
	currently seen matrices after using Floyd's Cycle Detection
	Algorithm.'''
	
	for x in range(0, MODULUS):
		for y in range(0, MODULUS):
			if CMODE == "iterstate":
				vectKey = C_step(vectorStates[x][y][0], vectorStates[x][y][1], F, MODULUS, 1)
				vectY   = vectKey % MODULUS
				vectX   = (vectKey - vectY)//MODULUS
				vectorStates[x][y] = [vectX, vectY]
				
			elif CMODE == "iterplane":
				C_iterate_matrix(pointer(F), pointer(currentF), MODULUS)
				
			elif CMODE == "iterall":
				if ARRANGEMENT == "nondiag":
					F[0][0] = x
					F[1][1] = y
				elif ARRANGEMENT == "diag":
					F[0][1] = x
					F[1][0] = y
				vectKey = get_orbit_info_array(F, MODULUS)
				vectTau = vectKey % (2*MODULUS)             #The two is from rows(F)
				vectOmega = (vectKey - vectTau)//(2*MODULUS) #Same as above
				vectorStates[x][y] = [vectOmega, vectTau]
				
				#Now, update maxInfo so we can normalise colours
				#Probably a better way to do this, but oh well
				maxInfo[0] = 0
				maxInfo[1] = 0
				for newX in range(0, MODULUS):
					for newY in range(0, MODULUS):
						if vectorStates[newX][newY][0] > maxInfo[0]:
							maxInfo[0] = vectorStates[newX][newY][0]
							
						if vectorStates[newX][newY][1] > maxInfo[1]:
							maxInfo[1] = vectorStates[newX][newY][1]
				
				
def is_initial_state():
	'''This function checks to see whether our vectors are back at their
	initial states. Returns True is they are, False otherwise.'''
	
	for x in range(0, MODULUS):
		for y in range(0, MODULUS):
			if CMODE == "iterstate":
				if vectorStates[x][y][0] != x or vectorStates[x][y][1] != y:
					return False
			
			elif CMODE == "iterplane":
				#Convert C output to vector, see if it's at it's original position
				vectorKey = C_step(x, y, pointer(currentF), MODULUS, 1)
				vectY = vectorKey % MODULUS
				vectX = (vectorKey - vectY)//MODULUS
				
				if vectX != x or vectY != y:
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
			if CMODE in ["iterstate", "iterall"]:
				vectorOfInterest = vectorStates[x][y]
				
			elif CMODE == "iterplane":
				#Convert C output to vector
				vectorKey = C_step(x, y, pointer(currentF), MODULUS, 1)
				vectY = vectorKey % MODULUS
				vectX = (vectorKey - vectY)//MODULUS
				vectorOfInterest = [vectX, vectY]

				
			extend = [1, 1]
			if CMODE == "iterall":
				coordX = xStart + x*tileSize
				coordY = yStart - (y+1)*tileSize
				
			#Calculating the appropriate values for drawing the square
			else:
				if COLORMODE == "repaint":
					if x == MODULUS - 1:
						extend[0] = 0
					if y == MODULUS - 1:
						extend[1] = 0
					
					coordX = xStart + x*tileSize
					coordY = yStart - (y+1)*tileSize
						
				elif COLORMODE == "drag":
					if CMODE != "iterplane": #Prevents indexing a list that doesn't exist in CMODE "iterplane"
						if vectorStates[x][y][0] == MODULUS - 1:
							extend[0] = 0
						if vectorStates[x][y][1] == MODULUS - 1:
							extend[1] = 0
						
					coordX = xStart + vectorOfInterest[0]*tileSize
					coordY = yStart - (vectorOfInterest[1]+1)*tileSize
				
			#Now determining the proper colours to use for the display
			
			#MODULUS-1 prevents colorX and colorY from going over MODULUS
			if COLORMODE == "relative":
				if COLORTRANSIENT != "solo":
					colorX = (vectorOfInterest[0]*(MODULUS-1))//maxInfo[0]
				
				if maxInfo[1] != 0 and COLORTRANSIENT != "none":
					colorY = (vectorOfInterest[1]*(MODULUS-1))//maxInfo[1]
					
				
			elif COLORMODE == "rellog":
				if COLORTRANSIENT != "solo":
					colorX = floor(log(vectorOfInterest[0]+1, maxInfo[0]+1)*(MODULUS-1))
				
				if maxInfo[1] != 0 and COLORTRANSIENT != "none":
					colorY = floor(log(vectorOfInterest[1]+1, maxInfo[1]+1)*(MODULUS-1))
					
				
			elif COLORMODE == "repaint":
				colorX = vectorOfInterest[0]
				colorY = vectorOfInterest[1]
				
				
			elif COLORMODE == "drag":
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
	if CMODE != "iterall":
		cap = caption + " - i" + str(iterations) + "m" + str(MODULUS) + "F" + \
		str(F[0][0]) + str(F[0][1]) + str(F[1][0]) + str(F[1][1])
		
	else:
		if ARRANGEMENT == "nondiag":
			cap = caption + " - m" + str(MODULUS) + " from F0" + \
			str(F[0][1]) + str(F[1][0]) + "0 to F" + str(MODULUS) + \
			str(F[0][1]) + str(F[1][0]) + str(MODULUS)
		elif ARRANGEMENT == "diag":
			cap = caption + " - m" + str(MODULUS) + " from F" + str(F[0][0]) + \
			"00" + str(F[1][1]) + " to F" + str(F[0][0]) + str(MODULUS) + \
			str(MODULUS) + str(F[1][1])
	
	return cap 

	
#Create array of colors for each vector
vectorColors = [[] for x in range(0, MODULUS)]
for x in range(0, MODULUS):
	for y in range(0, MODULUS):
		vectorColors[x].append((255*x//MODULUS, 255*y//MODULUS, 0))

#Initialise state of each vector before drawing, if needed
if CMODE == "iterstate":
	vectorStates = [[[x, y] for y in range(0, MODULUS)] for x in range(0, MODULUS)]
	
elif CMODE == "iterplane":
	set_matrix(currentF, [[1, 0], [0, 1]])
	
elif CMODE == "iterall":
	vectorStates = [[[0, 0] for y in range(0, MODULUS)] for x in range(0, MODULUS)]
	iterate_plane()

#This allows the starting iteration to be nonzero	
for a in range(0, iterations):
	iterate_plane()
draw_plane(windowDisplay)
pygame.display.set_caption(make_caption())


if CAPTUREMODE:
	#First, calculate the cycle length and transient length
	# so that ORBITVIS can stop taking screenshots once there's
	# nothing new to see (only if CMODE != "iterall").
	
	#These parameters aren't needed if we're iterating the entire matrix space
	if CMODE != "iterall":
		orbitKey   = get_orbit_info_array(F, MODULUS)
		orbitTau   = orbitKey % (2*MODULUS)
		orbitOmega = (orbitKey - orbitTau)//(2*MODULUS)
	
		#The +2 is to include one repeated image so the user knows a cycle happened,
		# as well as the original plane
		if maxcaptures > orbitTau + orbitOmega + 2 or maxcaptures < 0:
			maxcaptures = orbitTau + orbitOmega + 2


	#Loop until there're no more pictures to take
	while maxcaptures > 0 or maxcaptures == -1:
		if iterations != 0:
			iterate_plane()

		draw_plane(windowDisplay)
		pygame.display.update()
		pygame.display.set_caption(make_caption())
		pygame.image.save(windowDisplay, CAPTUREPATH + "/" + make_caption() + ".png")
		
		iterations += 1
		if (maxcaptures != -1):
			maxcaptures -= 1
				
		if CMODE != "iterall":
			if is_initial_state() and iterations != 1:
				break
				
		#Iterate to next screen
		else:
			if ARRANGEMENT == "nondiag":
				F[0][1] += 1
				if F[0][1] >= MODULUS:
					F[0][1] -= MODULUS
					F[1][0] += 1
					if F[1][0] >= MODULUS:
						break
			
			elif ARRANGEMENT == "diag":
				F[1][1] += 1
				if F[1][1] >= MODULUS:
					F[1][1] -= MODULUS
					F[0][0] += 1
					if F[0][0] >= MODULUS:
						break
			
		#Allowing the user to quit whenever
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
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
					
					#When using iterall, arrow keys change F
					if CMODE == "iterall":
						if ARRANGEMENT == "nondiag":
							F[0][1] += 1
							if F[0][1] >= MODULUS:
								F[0][1] -= MODULUS
						
						elif ARRANGEMENT == "diag":
							F[1][1] += 1
							if F[1][1] >= MODULUS:
								F[1][1] -= MODULUS
						
					iterate_plane()
					draw_plane(windowDisplay)
					pygame.display.update()
					pygame.display.set_caption(make_caption())
					
				elif event.key == pygame.K_LEFT: #Reset to 0th iteration or change matrix
					if CMODE == "iterstate":
						iterations = 0
						vectorStates = [[[x, y] for y in range(0, MODULUS)] for x in range(0, MODULUS)]
						
					elif CMODE == "iterplane":
						iterations = 0
						set_matrix(currentF, [[1, 0], [0, 1]])
							
					elif CMODE == "iterall":
						if ARRANGEMENT == "nondiag":
							F[0][1] -= 1
							if F[0][1] < 0:
								F[0][1] += MODULUS
								
						elif ARRANGEMENT == "diag":
							F[1][1] -= 1
							if F[1][1] < 0:
								F[1][1] += MODULUS
								
						iterate_plane()	
						
					draw_plane(windowDisplay)
					pygame.display.update()
					pygame.display.set_caption(make_caption())
					
				elif event.key == pygame.K_DOWN:
					if CMODE == "iterall": #Changing matrix in iterall mode
						if ARRANGEMENT == "nondiag":
							F[1][0] -= 1
							if F[1][0] < 0:
								F[1][0] += MODULUS
								
						elif ARRANGEMENT == "diag":
							F[0][0] -= 1
							if F[0][0] < 0:
								F[0][0] += MODULUS
							
						iterate_plane()
						draw_plane(windowDisplay)
						pygame.display.update()
						pygame.display.set_caption(make_caption())
						
				elif event.key == pygame.K_UP:
					if CMODE == "iterall": #Changing matrix in iterall mode
						if ARRANGEMENT == "nondiag":
							F[1][0] += 1
							if F[1][0] >= MODULUS:
								F[1][0] -= MODULUS
								
						elif ARRANGEMENT == "diag":
							F[0][0] += 1
							if F[0][0] >= MODULUS:
								F[0][0] -= MODULUS
							
						iterate_plane()
						draw_plane(windowDisplay)
						pygame.display.update()
						pygame.display.set_caption(make_caption())
						
				elif event.key == pygame.K_s:
					pygame.image.save(windowDisplay, make_caption() + ".png")
					print("Screenshot saved to working directory.")
					

			elif event.type == VIDEORESIZE: #When window is resized
				windowDimensions = event.size
				gridSize = min(windowDimensions) #Keep vector grid a square
				windowDisplay = pygame.display.set_mode(windowDimensions, RESIZABLE)
				
				draw_plane(windowDisplay)
				pygame.display.update()
				
			elif HOVERMODE and CMODE != "iterplane" and event.type == pygame.MOUSEMOTION:
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
				if CMODE == "iterstate":
					if vectorHover[0] != -1:
						print("Vector clicked: <", vectorHover[0], ", ", vectorHover[1], ">", sep="")
						print("Destination: <", vectorStates[vectorHover[0]][vectorHover[1]][0], 
						", ", vectorStates[vectorHover[0]][vectorHover[1]][1], ">", sep="")
						clickedVect = (c_int * 2)(vectorHover[0], vectorHover[1])
						print("Cycle length:", get_orbit_info(clickedVect, F, MODULUS))
							
				elif CMODE == "iterall":
					if vectorHover[0] != -1:
						print("Matrix clicked:")
						if ARRANGEMENT == "nondiag":
							print(vectorHover[0], F[0][1])
							print(F[1][0], vectorHover[1])
						elif ARRANGEMENT == "diag":
							print(F[0][0], vectorHover[0])
							print(vectorHover[1], F[1][1])
						print("Cycle length:", vectorStates[vectorHover[0]][vectorHover[1]][0])
						print("Transient length:", vectorStates[vectorHover[0]][vectorHover[1]][1])
						print("")
						
					
			elif event.type == pygame.QUIT:
				pygame.quit()
				quit()
	