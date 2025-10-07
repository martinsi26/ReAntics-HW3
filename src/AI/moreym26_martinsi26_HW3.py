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
            score = self.minimax(node)
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
    def minimax(self, node):
        DEPTH_LIMIT = 3

        if node.depth == DEPTH_LIMIT or getWinner(node.gameState) is not None:
            print(f"Random node eval: {node.evaluation}")
            print(f"Move with node: {node.move}")
            # Base case: if it is a leaf node then find utility
            if node.evaluation is None:
                node.evaluation = self.utility(node.gameState)
            return node.evaluation

        # Recursive Case 1: My move
        if node.gameState.whoseTurn == self.playerId:
            best_eval = -math.inf
            for child in self.expandNode(node):
                eval = self.minimax(child)
                best_eval = max(best_eval, eval)
            return best_eval

        # Recursive Case 2: Opponents move
        else:
            best_eval = math.inf
            for child in self.expandNode(node):
                eval = self.minimax(child)
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
        #Loop through the node to expand the frontier node chosen
        for move in moves:
            gameState = getNextStateAdversarial(node.gameState, move)
            childNode = Node(move, gameState, node.depth+1, None, node)
            nodeList.append(childNode)
        
        return nodeList
    
    ##
    # utility
    # Description: Combines all the other heuristic functions
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: full heuristic value
    ##
    def utility(self, currentState):
        #combined heuristic, lower is better
        return -(self.foodHeuristic(currentState) + self.attackHeuristic(currentState) + self.queenHeuristic(currentState))
    ##
    # foodHeuristic
    # Description: gets the heuristic value for food
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: heuristic value for food
    ##
    def foodHeuristic(self, currentState):
        #defining vars
        myId = currentState.whoseTurn
        myInv = currentState.inventories[myId]
        workerList = getAntList(currentState, myId, (WORKER,))
        myTunnel = getConstrList(currentState, myId, (TUNNEL,))[0]

        foodNeeded = FOOD_GOAL - myInv.foodCount
        if foodNeeded <= 0:
            return 0
        
        foods = getConstrList(currentState, None, (FOOD,))
        food1, food2 = [f for f in foods if f.coords[1] <= 3][:2]

        totMoves = 0

        for worker in workerList:
            if (worker.carrying):
                dist = approxDist(worker.coords, myTunnel.coords)
            else:
                dist_to_food_1 = approxDist(worker.coords, food1.coords)
                dist_to_food_2 = approxDist(worker.coords, food2.coords)
                dist = min(dist_to_food_1, dist_to_food_2)

            totMoves += self.dist_to_moves(dist, WORKER)
            foodNeeded -= 1 # each worker will deliver the food
        
        if foodNeeded > 0:
            tunnel_food_dist = min(approxDist(food1.coords, myTunnel.coords),
                                   approxDist(food2.coords, myTunnel.coords))
            totMoves += 2 * foodNeeded * self.dist_to_moves(tunnel_food_dist, WORKER)    
        
        return  totMoves
    
    ##
    # attackHeuristic
    # Description: gets the heuristic value for attacking
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: heuristic value for attacking
    ##
    def attackHeuristic(self, currentState):
        myId = currentState.whoseTurn
        enemyId = 1 - myId
        myAnts = getAntList(currentState, myId)
        enemyQueen = getAntList(currentState, enemyId, (QUEEN,))
        
        if not enemyQueen:
            return 0
        enemyQueen = enemyQueen[0]
        
        moves = 0
        for ant in myAnts:
            if ant.type in (SOLDIER, R_SOLDIER):
                dist = approxDist(ant.coords, enemyQueen.coords)
                moves += self.dist_to_moves(dist, ant.type)
        
        return moves
    
    ##
    # queenHeuristic
    # Description: gets the heuristic value for the queen and what shes doing
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: heuristic value for the queen
    ##
    def queenHeuristic(self, currentState):
        myId = currentState.whoseTurn
        myAnthill = getConstrList(currentState, myId, (ANTHILL,))[0]
        myTunnel = getConstrList(currentState, myId, (TUNNEL,))[0]
        myQueen = getAntList(currentState, myId, (QUEEN,))[0]

        penalty = 0
        if myQueen.coords in (myTunnel.coords, myAnthill.coords):
            penalty += 100 
        return penalty + self.dist_to_moves(approxDist(myQueen.coords, (1, 2)), QUEEN)

    def dist_to_moves (self, dist, ant_type):
        return math.ceil (dist / UNIT_STATS[ant_type][MOVEMENT])
    
    ##
    #getAttack
    #
    # This agent never attacks
    #
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0]  
        
    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method template, not implemented
        pass
    #Node class definition
class Node:
    def __init__(self, move, gameState, depth, evaluation, parent):
        self.move = move
        self.gameState = gameState
        self.depth = depth
        self.evaluation = evaluation
        self.parent = parent
        