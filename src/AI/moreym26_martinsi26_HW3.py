#Authors: Malory Morey, Simon Martin
#CS421 HW3
import random
import sys
import math
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
        super(AIPlayer,self).__init__(inputPlayerId, "HW3_AI")
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
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        rootNode = Node(None, currentState, 0, self.utility(currentState), None)
        best_score = -math.inf
        move_choice = None
        for node in self.expandNode(rootNode):
            score = self.minimax(node, self.playerId)
            if score > best_score:
                best_score = score
                move_choice = node.move
        print(best_score)
        print(move_choice)
        return move_choice


    ##
    #minimax
    #Description: Mini-Max algorithm to find the best path
    #
    #Parameters:
    #   node - The current node we are looking at
    #   whoseTurn - Variable indicating if this is my move or the opponents move
    #
    #Return: The mini-max evaluation of the move
    ##
    def minimax(self, node, whoseTurn):
        DEPTH_LIMIT = 3

        if node.depth == DEPTH_LIMIT or getWinner(node.gameState) is not None:
            print(f"Random node eval: {node.evaluation}")
            # if it is a leaf node then find utility
            #Moved the utility call into minimax since leaf nodes utility and non leaf nodes use other min/max vals
            return self.utility(node.gameState)
        # My move
        if whoseTurn == self.playerId:
            best_eval = -math.inf
            for child in self.expandNode(node):
                eval = self.minimax(child, 1 - whoseTurn)
                best_eval = max(best_eval, eval)
            return best_eval

        # Opponents move
        else:
            best_eval = math.inf
            for child in self.expandNode(node):
                eval = self.minimax(child, 1 - whoseTurn)
                best_eval = min(best_eval, eval)
            return best_eval
    

    ##
    # expandNode
    # Description: Expands a node to generate all possible child nodes based on legal moves.
    #
    # Parameters:
    #   node - The node to be expanded (Node)
    #
    # Return: A list of child nodes generated from the current node
    ##
    def expandNode(self, node):
        moves = listAllLegalMoves(node.gameState)
        #print("Legal moves at depth", node.depth, ":", moves)

        nodeList = []

        for move in moves:
            gameState = getNextStateAdversarial(node.gameState, move)
            childNode = Node(move, gameState, node.depth+1, None, node)
            nodeList.append(childNode)
        
        return nodeList


    ##
    #utility
    #Description: Calculates the evaluation score for a given game state.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #   preCarrying - A boolean value to see if a worker was carrying food before the move
    #
    #Return: The evaluation value for the move
    ##
    def utility(self, currentState):
        TARGET_WORKERS = 2
        TARGET_ARMY = {R_SOLDIER: 1, SOLDIER: 1}

        winner = getWinner(currentState)

        # Game over scoring
        if winner == PLAYER_ONE:
            return math.inf
        elif winner == PLAYER_TWO:
            return -math.inf
        
        myInv = getCurrPlayerInventory(currentState)
        enemyInv = getEnemyInv(self, currentState)

        score = 0

        # Queen HP
        score += 10 * myInv.getQueen().health
        score -= 10 * enemyInv.getQueen().health

        # Anthill HP
        score += 5 * myInv.getAnthill().captureHealth
        score -= 5 * enemyInv.getAnthill().captureHealth

        # Worker incentive
        myWorkers = getAntList(currentState, currentState.whoseTurn, (WORKER,))
        numWorkers = len(myWorkers)
        if numWorkers < TARGET_WORKERS:
            score += 5 * numWorkers
        else:
            score += 5 * TARGET_WORKERS

        # Army incentive
        for antType, targetCount in TARGET_ARMY.items():
            myCount = sum(1 for ant in myInv.ants if ant.type == antType)
            if myCount < targetCount:
                score += 4 * myCount
            else:
                score += 4 * targetCount
        
        # Food incentive only if army target is met
        if numWorkers >= TARGET_WORKERS and all(
            sum(1 for ant in myInv.ants if ant.type == t) >= c 
            for t, c in TARGET_ARMY.items()
        ):
            score += 10 * myInv.foodCount

        # Penalize enemy army
        enemyArmy = getAntList(currentState, 1 - currentState.whoseTurn, (WORKER, DRONE, SOLDIER, R_SOLDIER)) # All enemy ants but disregarding their queen
        score -= 3 * len(enemyArmy)

        # Ranged soldier movement incentive
        myRSoldiers = [ant for ant in getAntList(currentState, currentState.whoseTurn, (R_SOLDIER,))]
        score += self.rangedSoldierUtility(myRSoldiers, enemyArmy)

        # Worker movement incentive
        myWorkers = getAntList(currentState, currentState.whoseTurn, (WORKER,))
        score += self.workerUtility(myWorkers, currentState)

        return score


    ##
    #rangedSoldierUtility
    #Description: Calculates the evaluation score for ranged soldier movement
    #
    #Parameters:
    #   myRanged - A list of ranged soldier ants
    #   enemyAnts - A list of enemy ants
    #
    #Return: The evaluation value for ranged soldier movement
    ##
    def rangedSoldierUtility(self, myRanged, enemyAnts):
        score = 0
        for rsoldier in myRanged:
            if enemyAnts:
                closestDist = min(approxDist(rsoldier.coords, e.coords) for e in enemyAnts)
                # Closer distance gives higher score
                score += 5 / (closestDist + 1)  
            
        return score
    

    ##
    #workerUtility
    #Description: Calculates the evaluation score for worker movement
    #
    #Parameters:
    #   myRanged - A list of worker ants
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The evaluation value for worker movement
    ##
    def workerUtility(self, myWorkers, currentState):
        score = 0
        myInv = getCurrPlayerInventory(currentState)
        
        # Get food on the board
        foodList = getConstrList(currentState, pid=None, types=(FOOD,))
        
        # Get home locations (Anthill + Tunnels)
        homeList = [myInv.getAnthill()] + myInv.getTunnels()
        #Get ants
        ants = getAntList(currentState, currentState.whoseTurn)

        for worker in myWorkers:
            if worker.carrying:
                # Worker has food: move towards closest home (anthill/tunnel)
                homesByDistance = sorted(homeList, key=lambda h: approxDist(worker.coords, h.coords))
                # Closer distance is better, invert distance
                for home in homesByDistance:
                    occupied = any(a.coords == home.coords and a is not worker for a in ants)
                    if not occupied:
                        closestHomeDist = approxDist(worker.coords, home.coords)
                        score += 10 / (closestHomeDist + 1)
                        score += 10  # bonus for carrying food
                        if worker.coords in [home.coords for home in homeList]:
                            score += 20  # Encourage dropping food
                        if closestHomeDist > 5:
                            score -= 5
                        break
            else:
                # Worker not carrying: move towards closest food
                if foodList:
                    closestFoodDist = min(approxDist(worker.coords, food.coords) for food in foodList)
                    score += 10 / (closestFoodDist + 1) 

        # Reward for delivered food
        score += 10 * myInv.foodCount
        
        return score
  
    
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
        #method template, not implemented
        pass

class Node:
    def __init__(self, move, gameState, depth, evaluation, parent):
        self.move = move
        self.gameState = gameState
        self.depth = depth
        self.evaluation = evaluation
        self.parent = parent
        