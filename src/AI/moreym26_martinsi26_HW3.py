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
                (1, 1), (8, 1),  # Anthill and hive
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
        rootNode = Node(None, currentState, 0, self.utility(currentState, currentState, currentState.whoseTurn), None)
        best_score = -math.inf
        move_choice = None
        for node in self.expandNode(rootNode, currentState.whoseTurn):
            score = self.minimax(node, -math.inf, math.inf, currentState.whoseTurn)
            if score > best_score:
                best_score = score
                move_choice = node.move
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
    def minimax(self, node, alpha, beta, myTurn):
        DEPTH_LIMIT = 3

        if getWinner(node.gameState) is not None or node.depth >= DEPTH_LIMIT:
            # Base case: if it is a leaf node then find utility
            return node.evaluation

        isMyTurn = (node.gameState.whoseTurn == myTurn)

        children = self.expandNode(node, myTurn)
        if not children:
            return node.evaluation

        # Recurrsive Case 1: My move
        if isMyTurn:
            best_eval = -math.inf

            for child in children:
                eval = self.minimax(child, alpha, beta, myTurn)
                best_eval = max(eval, best_eval)
                alpha = max(alpha, best_eval)
                if beta <= alpha:
                    # Beta cutoff
                    break
            return best_eval

        # Recurrsive Case 2: Opponents move
        else:
            best_eval = math.inf

            for child in children:
                eval = self.minimax(child, alpha, beta, myTurn)
                best_eval = min(best_eval, eval)
                beta = min(beta, best_eval)
                if beta <= alpha:
                    # Alpha cutoff
                    break
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
    def expandNode(self, node, myTurn):
        moves = listAllLegalMoves(node.gameState)
        nodeList = []

        for move in moves:
            gameState = getNextStateAdversarial(node.gameState, move)
            childNode = Node(move, gameState, node.depth+1, self.utility(gameState, node.gameState, myTurn), node)
            nodeList.append(childNode)

        nodeList.sort(key=lambda n: n.evaluation, reverse=(node.gameState.whoseTurn == myTurn))

        topPercent = 0.05
        cutoff = max(1, int(len(nodeList) * topPercent))
        
        return nodeList[:cutoff]


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
    def utility(self, currentState, previousState, myTurn):
        TARGET_WORKERS = 2
        TARGET_R_SOLDIER = 1

        winner = getWinner(currentState)

        score = 0

        # Game over scoring
        if winner == myTurn:
            score += -math.inf
        elif winner == 1 - myTurn:
            score += math.inf
        
        if currentState.whoseTurn == myTurn:
            myInv = getCurrPlayerInventory(currentState)
            enemyInv = getEnemyInv(self, currentState)
        else:
            enemyInv = getCurrPlayerInventory(currentState)
            myInv = getEnemyInv(self, currentState)

        # Queen HP
        if myInv.getQueen() is not None:
            score += 10 * myInv.getQueen().health
        if enemyInv.getQueen() is not None:
            score -= 10 * enemyInv.getQueen().health

        # Queen off Anthill
        if myInv.getQueen().coords == myInv.getAnthill().coords:
            score -= 5
        else:
            score += 5

        # Anthill HP
        score += 5 * myInv.getAnthill().captureHealth
        score -= 5 * enemyInv.getAnthill().captureHealth

        # Worker incentive
        myWorkers = getAntList(currentState, myTurn, (WORKER,))
        numWorkers = len(myWorkers)
        if numWorkers <= TARGET_WORKERS:
            score += 5 * numWorkers

        # Army incentive
        myRSoldiers = getAntList(currentState, myTurn, (R_SOLDIER,))
        numRSoldiers = len(myRSoldiers)
        if numRSoldiers <= TARGET_R_SOLDIER:
            score += 5 * numRSoldiers
        
        # Food incentive only if army target is met
        if numWorkers >= TARGET_WORKERS and numRSoldiers >= TARGET_R_SOLDIER:
            score += 10 * myInv.foodCount

        # Penalize enemy army
        enemyArmy = getAntList(currentState, 1 - myTurn, (WORKER, DRONE, SOLDIER, R_SOLDIER)) # All enemy ants but disregarding their queen
        score -= 3 * len(enemyArmy)

        # Ranged soldier movement incentive
        score += self.rangedSoldierUtility(myRSoldiers, enemyArmy)

        # Worker movement incentive
        previousWorkers = getAntList(previousState, myTurn, (WORKER,))
        score += self.workerUtility(myWorkers, previousWorkers, currentState, myInv)

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
                # Calculate the Manhattan distance separately for x and y
                distances = [
                    (abs(rsoldier.coords[0] - e.coords[0]), abs(rsoldier.coords[1] - e.coords[1]))
                    for e in enemyAnts
                ]
                # Find closest enemy based on Manhattan distance
                closestX, closestY = min(distances, key=lambda d: d[0] + d[1])
                
                # Prioritize y-direction slightly more
                weightedDist = closestX + 1.2 * closestY  # increase weight on y
                score += 5 / (weightedDist + 1)
        
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
    def workerUtility(self, myWorkers, previousWorkers, currentState, myInv):
        score = 0
        
        # Get food on the board
        foodList = getConstrList(currentState, pid=None, types=(FOOD,))
        
        # Get home locations (Anthill + Tunnels)
        homeList = [myInv.getAnthill()] + myInv.getTunnels()
        
        for worker in myWorkers:
            for prevWorker in previousWorkers:
                if prevWorker.UniqueID != worker.UniqueID:
                    continue
                
                closestHomeDist = min(stepsToReach(currentState, worker.coords, home.coords) for home in homeList)
                closestFoodDist = min(stepsToReach(currentState, worker.coords, food.coords) for food in foodList)

                # Worker just picked up food
                if worker.carrying and not prevWorker.carrying and closestFoodDist == 0:
                    score += 12
                
                # Worker just dropped food off
                elif not worker.carrying and prevWorker.carrying and closestHomeDist == 0:
                    score += 12

                # Move worker towards Home
                elif worker.carrying:
                    score += 10 / (closestHomeDist + 1)

                # Move worker towards Food
                elif not worker.carrying:
                    score += 10 / (closestFoodDist + 1) 
        
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
        #method templaste, not implemented
        pass

class Node:
    def __init__(self, move, gameState, depth, evaluation, parent):
        self.move = move
        self.gameState = gameState
        self.depth = depth
        self.evaluation = evaluation
        self.parent = parent
        