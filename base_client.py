import random

from game.client.user_client import UserClient
from game.common.enums import *
from game.utils.vector import Vector


class State(Enum):
    MINING = auto()
    SELLING = auto()


class Client(UserClient):
    # Variables and info you want to save between turns go here
    def __init__(self):
        super().__init__()

    def team_name(self):
        """
        Allows the team to set a team name.
        :return: Your team name
        """
        return 'BitBots'
    
    def first_turn_init(self, world, avatar):
        """
        This is where you can put setup for things that should happen at the beginning of the first turn
        """
        self.company = avatar.company
        self.my_station_type = ObjectType.TURING_STATION if self.company == Company.TURING else ObjectType.CHURCH_STATION
        self.current_state = State.MINING
        self.base_position = world.get_objects(self.my_station_type)[0][0]
    
    # This is where your AI will decide what to do
    def take_turn(self, turn, actions, world, avatar):
        countATech =0
          
        """
        This is where your AI will decide what to do.
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        if turn == 1:
            self.first_turn_init(world, avatar)
            
        current_tile = world.game_map[avatar.position.y][avatar.position.x] # set current tile to the tile that I'm standing on
        
        # If I start the turn on my station, I should...
        if current_tile.occupied_by.object_type == self.my_station_type:
            # buy Improved Mining tech if I can...
            if avatar.science_points >= avatar.get_tech_info('Improved Mining').cost and not avatar.is_researched('Improved Mining'):
                return [ActionType.BUY_IMPROVED_MINING]
            #if avatar.science_points >= avatar.get_tech_info('Dynamite').cost and not avatar.is_researched('Dynamite'):
                #return [ActionType.BUY_DYNAMITE]
            if avatar.science_points >= avatar.get_tech_info('Improved Drivetrain').cost and not avatar.is_researched('Improved Drivetrain'):
                return [ActionType.BUY_IMPROVED_DRIVETRAIN]
            if avatar.science_points >= avatar.get_tech_info('Superior Mining').cost and not avatar.is_researched('Superior Mining'):
                return [ActionType.BUY_SUPERIOR_MINING]
            #if avatar.science_points >= avatar.get_tech_info('Landmines').cost and not avatar.is_researched('Landmines'):
                #return [ActionType.BUY_LANDMINES]
            if avatar.science_points >= avatar.get_tech_info('Superior Drivetrain').cost and not avatar.is_researched('Superior Drivetrain'):
                return [ActionType.BUY_SUPERIOR_DRIVETRAIN]
            #if avatar.science_points >= avatar.get_tech_info('EMPs').cost and not avatar.is_researched('EMPs'):
               # return [ActionType.BUY_EMPS] 
            if avatar.science_points >= avatar.get_tech_info('Overdrive Mining').cost and not avatar.is_researched('Overdrive Mining'):
                return [ActionType.BUY_OVERDRIVE_MINING]  
            if avatar.science_points >= avatar.get_tech_info('Overdrive Drivetrain').cost and not avatar.is_researched('Overdrive Drivetrain'):
                return [ActionType.BUY_OVERDRIVE_DRIVETRAIN]
            
            # otherwise set my state to mining
            self.current_state = State.MINING
            
        # If I have at least 5 items in my inventory, set my state to selling
        if len([item for item in self.get_my_inventory(world) if item is not None]) >= 45 or countATech >= 5:
            self.current_state = State.SELLING
            countATech=0
            
        #if I have enough ATech i will go back to base  
        if  countATech >= 5:
               self.current_state = State.SELLING

            
          
            
        # Make action decision for this turn
        if self.current_state == State.SELLING:
            # actions = [ActionType.MOVE_LEFT if self.company == Company.TURING else ActionType.MOVE_RIGHT] # If I'm selling, move towards my base
            actions = self.generate_moves(avatar.position, self.base_position, turn % 2 == 0)
        else:
            if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION:
                # If I'm mining and I'm standing on an ore, mine it
                ore = current_tile.get_occupied_by(ObjectType.ORE_OCCUPIABLE_STATION).held_item
                actions = [ActionType.MINE]
                ore = current_tile.get_occupied_by(ObjectType.ORE_OCCUPIABLE_STATION).held_item
                    #check if current ore is ancient tech
                if  ore.object_type == ObjectType.ANCIENT_TECH:
                    countATech = countATech +1
                    if  countATech >= 5:
                        self.current_state = State.SELLING
                        countATech=0

                    
            else:
                # If I'm mining and I'm not standing on an ore, move randomly
                actions = [random.choice([ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT, ActionType.MOVE_UP, ActionType.MOVE_DOWN])]
                
        return actions

    def generate_moves(self, start_position, end_position, vertical_first):
        """
        This function will generate a path between the start and end position. It does not consider walls and will
        try to walk directly to the end position.
        :param start_position:      Position to start at
        :param end_position:        Position to get to
        :param vertical_first:      True if the path should be vertical first, False if the path should be horizontal first
        :return:                    Path represented as a list of ActionType
        """
        dx = end_position.x - start_position.x
        dy = end_position.y - start_position.y
        
        horizontal = [ActionType.MOVE_LEFT] * -dx if dx < 0 else [ActionType.MOVE_RIGHT] * dx
        vertical = [ActionType.MOVE_UP] * -dy if dy < 0 else [ActionType.MOVE_DOWN] * dy
        
        return vertical + horizontal if vertical_first else horizontal + vertical
    
    def get_my_inventory(self, world):
        return world.inventory_manager.get_inventory(self.company)
    
    
