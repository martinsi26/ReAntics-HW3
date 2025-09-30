#Authors: Malory Morey, Simon Martin
#CS421 HW3
import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Simple Food Gatherer")
        #the coordinates of the agent's food and tunnel will be stored in these
        #variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None
    
    ##
    #getPlacement 
    #
    # The agent uses a hardcoded arrangement for phase 1 to provide maximum
    # protection to the queen.  Enemy food is placed randomly.
    #
    def getPlacement(self, currentState):
        #Just put in my previous method for starting the game, can change to better strategy
        self.myFood = None
        self.myTunnel = None

        if currentState.phase == SETUP_PHASE_1:
            return [
                (0, 0), (8, 1),  # Anthill and hive
                #Make a Grass wall
                (0, 3), (1, 3), (2, 3), (3, 3),  #Grass 
                (4, 3), (5, 3), (6, 3), #Grass
                (8, 3), (9, 3) # Grass
            ]
        #Placing the enemies food (In the corners/randomly far away from their anthill)
        elif currentState.phase == SETUP_PHASE_2:
            #The places the method will choose and append to return
            foodSpots = []
            #Corner coordinates
            corners = [(0, 9), (0, 6), (9, 6), (9, 9)]

            #Go through corners, make sure its legal and add to the return list
            for coord in corners:
                if legalCoord(coord) and getConstrAt(currentState, coord) is None:
                    foodSpots.append(coord)
                #If you have both spots, break and go to return
                if len(foodSpots) == 2:
                    break
            #If one or more of the corners are covered pick a random spot
            while len(foodSpots) < 2:
                coord = (random.randint(0, 9), random.randint(6, 9))
                if legalCoord(coord) and getConstrAt(currentState, coord) is None and coord not in foodSpots:
                    foodSpots.append(coord)

            #Return final list of enemy food placement
            return foodSpots

        return None
    
    ##
    #getMove
    #
    # This agent simply gathers food as fast as it can with its worker.  It
    # never attacks and never builds more ants.  The queen is never moved.
    #
    ##
    def getMove(self, currentState):
        pass
                              
    
    ##
    #getAttack
    #
    # This agent never attacks
    #
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0]  #don't care
        
    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass