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
        #Loop through the node to expand the frontier node chosen
        for move in moves:
            gameState = getNextStateAdversarial(node.gameState, move)
            childNode = Node(move, gameState, node.depth+1, None, node)
            nodeList.append(childNode)
        
        return nodeList
    
    def utility(self, currentState):
        #combined heuristic, lower is better
        return -(self.foodHeuristic(currentState) + self.geh_h_attack(currentState) + self.get_h_queen(currentState))
    
    def foodHeuristic(self, parentState, currentState):
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

        if workerList != []:
            totMoves -= 1000
            for worker in workerList:
                if (worker.carrying):
                    dist = approxDist(worker.coords, myTunnel.coords)
                    totMoves += self.dist_to_moves(dist, WORKER)
                    foodNeeded -= 1 # each worker will deliver the food

                else:
                    dist_to_food_1 = approxDist(worker.coords, food1.coords)
                    dist_to_food_2 = approxDist(worker.coords, food2.coords)

                    if dist_to_food_1 < dist_to_food_2:
                        dist = dist_to_food_1
                        dist += approxDist(food1.coords, myTunnel.coords)
                    else:
                        dist = dist_to_food_2
                        dist += approxDist(food2.coords, myTunnel.coords)
                    totMoves += self.dist_to_moves(dist, WORKER)
                    foodNeeded -= 1 # each worker will deliver the food
        
        dist_between_tunnel_food = min (approxDist(food1.coords, myTunnel.coords), approxDist(food2.coords, myTunnel.coords))
        totMoves += 2 * foodNeeded * self.dist_to_moves(dist_between_tunnel_food, WORKER)
            
        return  totMoves
    
    
    
    
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
    def dist_to_moves (self, dist, ant_type):
        return math.ceil (dist / UNIT_STATS[ant_type][MOVEMENT])
    
    def select_from_frontierNodes(self, frontierNodes, max_depth):
        min_f_value = 10000000
        selected_node = None

        for node in frontierNodes:
            if node['depth'] < max_depth and node['f_value'] < min_f_value:
                selected_node = node

        if selected_node == None:
            return None
        
        return selected_node

    def findBestNode(self, nodes):
        #intialize vars
        best_node = nodes[0]
        min_value = best_node['f_value']
        #Get best utility
        for node in nodes:
            if (node['f_value'] < min_value):
                min_value = node['f_value']
                best_node = node  

        best_nodes = []
        for node in nodes:
            if node['f_value'] == min_value:
                best_nodes.append(node)

        best_node = best_nodes[random.randint(0,len(best_nodes) - 1)]

        # Find the best movement -> from the current depth to the first depth !!! 
        while best_node['depth'] > 2:
            best_node = best_node['parentNode']

        return best_node

    def h_func(self, parentState, currentState):
        h_food = self.foodHeuristic(parentState, currentState)
        
        h_attack = self.get_h_attack(parentState, currentState)

        h_queen = self.get_h_queen(parentState, currentState)
        #Add all together
        h_final = h_food + h_attack + h_queen

        return h_final


    def get_h_attack(self, parentState, currentState):
        myId = currentState.whoseTurn
        myInv = currentState.inventories[myId]

        enemyId = 1 - myId
        enemyInv = currentState.inventories[enemyId]

        myAntList = getAntList(currentState, myId)
        enemyTunnel = getConstrList(currentState, enemyId, (TUNNEL,))[0]

        # If enemy queen is killed
        if getAntList(currentState, enemyId, (QUEEN,)) == []:
            return 0
        
        Total_moves = 2100
        num_r_soldier = 0
        num_soldier = 0

        for ant in myAntList:
            if ant.type == R_SOLDIER:
                num_r_soldier += 1
            if ant.type == SOLDIER:
                num_soldier += 1

        if num_r_soldier != 0:
            Total_moves = max (0, Total_moves - 500 * num_r_soldier)

        enemyQueen = getAntList(currentState, enemyId, (QUEEN,))[0]
        enemyWorkers = getAntList(currentState, enemyId, (WORKER,))
        if enemyWorkers == []:
            Total_moves -= 100

        for ant in myAntList:
            if ant.type == R_SOLDIER:
                if enemyWorkers == []:
                    dist_to_target = approxDist(ant.coords, enemyQueen.coords)
                else:
                    dist_to_target = approxDist(ant.coords, enemyWorkers[0].coords)

                moves_to_target = self.dist_to_moves (dist_to_target, R_SOLDIER)
                Total_moves += moves_to_target

        return Total_moves
    
    # Check whethere the Queen is blocking the anthill
    def get_h_queen(self, parentState, currentState):
        myId = currentState.whoseTurn
        myAnthill = getConstrList(currentState, myId, (ANTHILL,))[0]
        myTunnel = getConstrList(currentState, myId, (TUNNEL,))[0]
        myQueen = getAntList(currentState, myId, (QUEEN,))[0]

        Foods = getConstrList(currentState, None, (FOOD,))
        myFood_1, myFood_2 = None, None
        for food in Foods:
            if food.coords[1] <= 3:
                if myFood_1 == None:
                    myFood_1 = food
                else:
                    myFood_2 = food

        Total_moves = 2
        if  (myQueen.coords != myAnthill.coords) and (myQueen.coords != myTunnel.coords):
            Total_moves -= 1
        elif (myQueen.coords != myFood_1.coords) and (myQueen.coords != myFood_2.coords):
            Total_moves -= 1

        dist_to_destination = approxDist(myQueen.coords, (1,2))
        Total_moves += self.dist_to_moves (dist_to_destination, QUEEN)
        
        return Total_moves

class Node:
    def __init__(self, move, gameState, depth, evaluation, parent):
        self.move = move
        self.gameState = gameState
        self.depth = depth
        self.evaluation = evaluation
        self.parent = parent
        