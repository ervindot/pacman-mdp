# mdpAgents.py
# ashish-chawla/Nov-2018
#
# Version 1
#
# 
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Ashish Chawla, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        self.itrStart = 0
        self.iterationDict = {}

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        self.makeMap(state)


        
    # This is what gets run in between multiple games
    def final(self,state):
        print "Looks like the game just ended!"
        self.itrStart = 0
        self.iterationDict = {}

    def makeMap(self, state):
        grid = []
        self.valueMap = {}

        foodloc = tuple(api.food(state))
        corners = api.corners(state)
        walls = api.walls(state)
        capsules = api.capsules(state)


        tempH = -1
        tempW = -1

        for i in range(len(corners)):
            if corners[i][1] > tempH:
                tempH = corners[i][1]
            if corners[i][0] > tempW:
                tempW = corners[i][0]

        height = tempH + 1
        width = tempW + 1

        for i in range(width):
            for j in range(height):
                grid.append((i, j))

        # creates a map where pacman can move around
        self.pcMap = (tuple(set(grid) - set(walls)))
        # print "pcMap",self.pcMap

        # initially assigning same values to all places in the map
        for i in range(len(self.pcMap)):
            self.valueMap[self.pcMap[i]] = 0

        # Assign values in the map based on the objects present in the map
        for i in range(len(self.pcMap)):
            #Assign for Food
            if self.pcMap[i] in foodloc:
                self.valueMap[self.pcMap[i]] = 1
            #Assign for Capsules
            if self.pcMap[i] in capsules:
                self.valueMap[self.pcMap[i]] = 2


    def updatefood(self, state):

        foodloc = tuple(api.food(state))
        capsules = api.capsules(state)


        # initially assigning same values to all places in the map
        for i in range(len(self.pcMap)):
            self.valueMap[self.pcMap[i]] = 0

        # Assign values in the map based on the objects present in the map
        for i in range(len(self.pcMap)):
            # Assign for Food
            if self.pcMap[i] in foodloc:
                self.valueMap[self.pcMap[i]] = 1
            # Assign for Capsules
            if self.pcMap[i] in capsules:
                self.valueMap[self.pcMap[i]] = 2



    # Utilities of all the states are calculated using
    #  Value iterations untill they stop changing before pacman makes a move
    def valueIteration(self, state,ghostcors):
        foodloc = api.food(state)
        capsules = api.capsules(state)


        walls = api.walls(state)
        reward = -0.04
        discountFactor = 0.8

        if self.itrStart == 0:
            self.iterationDict = self.valueMap.copy()
            self.itrStart = 1
        temp = self.iterationDict.copy()

        #Assign rewards on the basis of objects on the map such as food, ghost and capsules
        # and calculates utlity of the coordinates using bellman equation
        for i in range(len(self.pcMap)):
            coords = self.pcMap[i]
            if coords in foodloc:
                reward = 1
            elif coords in capsules:
                reward = 2
            elif coords in ghostcors:
                reward = -4

            # East Coordinates
            if (coords[0] + 1, coords[1]) not in walls:
                ec = (coords[0] + 1, coords[1])
            else:
                ec = coords

            # West Coordinates
            if (coords[0] - 1, coords[1]) not in walls:
                wc = (coords[0] - 1, coords[1])
            else:
                wc = coords

            # North Coordinates
            if (coords[0], coords[1] + 1) not in walls:
                nc = (coords[0], coords[1] + 1)
            else:
                nc = coords

            # South Coordinates
            if (coords[0], coords[1] - 1) not in walls:
                sc = (coords[0], coords[1] - 1)
            else:
                sc = coords

            # Bellman Equation. Calculating utility from the last iterated values
            northVal = ((0.8 * temp[nc]) + (0.1 * temp[wc]) + (0.1 * temp[ec]))
            eastVal = ((0.8 * temp[ec]) + (0.1 * temp[nc]) + (0.1 * temp[sc]))
            southVal = ((0.8 * temp[sc]) + (0.1 * temp[wc]) + (0.1 * temp[ec]))
            westVal = ((0.8 * temp[wc]) + (0.1 * temp[nc]) + (0.1 * temp[sc]))

            valueIter = reward + (discountFactor * max(northVal, eastVal, southVal, westVal))

            # The iteration value is rounded off to 3 decimals
            self.iterationDict[coords] = round(valueIter, 3)


        #This compares all the current value iteration dictionary and the previous one
        stability = cmp(temp,self.iterationDict)
        return stability

    # Pacman selects the best action to move
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        pacloc = api.whereAmI(state)
        ghoststates = api.ghostStates(state)
        ghostcors = []
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        self.updatefood(state)

        #Making a list of ghost coordinates which are still active and not edible
        # So these ghost coordinates will get negative value during iteration
        for i in range(len(ghoststates)):
            # converting ghosts coordinates in integer
            ghostX = ghoststates[i][0][0]
            ghostY = ghoststates[i][0][1]
            ghostXY = (int(ghostX), int(ghostY))
            if ghostXY in self.pcMap and ghoststates[i][1] == 0:
                ghostcors.append((int(ghostX), int(ghostY)))
                
                #Create a buffer around ghost so pacman will avoid it
                eghost = ((ghostXY[0]+1),ghostXY[1])
                wghost = ((ghostXY[0]-1)),ghostXY[1]
                nghost = ((ghostXY[0]),ghostXY[1]+1)
                sghost = ((ghostXY[0]),ghostXY[1]-1)
                ghostcors.append(eghost)
                ghostcors.append(wghost)
                ghostcors.append(nghost)
                ghostcors.append(sghost)


        # The value iteration will be called until all the value of the bellman
        # stops changing from the previous values
        for i in range(100):
            stable = self.valueIteration(state,ghostcors)
            if stable == 0:
                #print "stable at ", i
                break


        # East Coordinates
        if Directions.EAST in legal:
            eastofpacman = (pacloc[0] + 1, pacloc[1])
        else:
            eastofpacman = pacloc

        # West Coordinates
        if Directions.WEST in legal:
            westofpacman = (pacloc[0] - 1, pacloc[1])
        else:
            westofpacman = pacloc

        # North Coordinates
        if Directions.NORTH in legal:
            northofpacman = (pacloc[0], pacloc[1] + 1)
        else:
            northofpacman = pacloc

        # South Coordinates
        if Directions.SOUTH in legal:
            southofpacman = ((pacloc[0], pacloc[1] - 1))
        else:
            southofpacman = pacloc

        maxutil = -999
        makeMove = 'null'

        unorth = self.iterationDict[northofpacman]
        usouth = self.iterationDict[southofpacman]
        ueast = self.iterationDict[eastofpacman]
        uwest = self.iterationDict[westofpacman]

        # Get a movement policy for pacman using the
        # value iteration map that is updated at every move

        if Directions.NORTH in legal:
            movnorth = ((0.8 * unorth) + (0.1 * uwest) + (0.1 * ueast))
            if movnorth > maxutil:
                    maxutil = movnorth
                    makeMove = Directions.NORTH
        if Directions.EAST in legal:
            moveast = ((0.8 * ueast) + (0.1 * unorth) + (0.1 * usouth))
            if moveast > maxutil:
                    maxutil = moveast
                    makeMove = Directions.EAST
        if Directions.SOUTH in legal:
            movsouth = ((0.8 * usouth) + (0.1 * uwest) + (0.1 * ueast))
            if movsouth > maxutil:
                maxutil = movsouth
                makeMove = Directions.SOUTH
        if Directions.WEST in legal:
            movwest = ((0.8 * uwest) + (0.1 * unorth) + (0.1 * usouth))
            if movwest > maxutil:
                maxutil = movwest
                makeMove = Directions.WEST

        if makeMove != 'null':
            self.itrStart = 0
            return api.makeMove(makeMove, legal)
        else:
            print "where am I ?"

