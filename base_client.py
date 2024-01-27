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
        self.visited_positions = set()

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
        """
        This is where your AI will decide what to do.
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        if turn == 1:
            self.first_turn_init(world, avatar)
            
        current_tile = world.game_map[avatar.position.y][avatar.position.x]

        # If I start the turn on my station, I should...
        if current_tile.occupied_by.object_type == self.my_station_type:
            # Buy Improved Mining tech if I can...
            if avatar.science_points >= avatar.get_tech_info('Improved Drivetrain').cost and not avatar.is_researched('Improved Drivetrain'):
                return [ActionType.BUY_IMPROVED_DRIVETRAIN]
            # # Otherwise set my state to mining
            # self.current_state = State.MINING

        # Get the current position of the bot
        current_position = avatar.position

        # Example of finding the nearest ore
        nearest_ore_position = self.find_nearest_ore(current_position, world)

        # Move towards the ore if it's found
        if nearest_ore_position is not None:
            move_actions = self.generate_moves(current_position, nearest_ore_position, turn % 2 == 0, world)
            actions = move_actions  # Combine move actions with existing actions
            
        # If I have at least 5 items in my inventory, set my state to selling
        if len([item for item in self.get_my_inventory(world) if item is not None]) >= 5:
            self.current_state = State.SELLING

        # Make action decision for this turn
        if self.current_state == State.SELLING:
            actions = self.generate_moves2(avatar.position, self.base_position, turn % 2 == 0)
        else:
            if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION:
                actions = [ActionType.MINE]
            else:
                # Move randomly
                actions = [random.choice([ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT, ActionType.MOVE_UP, ActionType.MOVE_DOWN])]

        return actions
    
    def find_nearest_ore(self, current_position, world):
        """
        Find the position of the nearest ore.
        :param current_position:    The current position of the bot.
        :param world:               Generic world information.
        :return:                    The position of the nearest ore, or None if no ore is found.
        """
        # Example: Iterate over the game map to find the nearest ore position
        nearest_ore_position = None
        min_distance = float('inf')

        for y, row in enumerate(world.game_map):
            for x, tile in enumerate(row):
                if tile.is_occupied_by_object_type(ObjectType.ORE_OCCUPIABLE_STATION):
                    distance = abs(current_position.x - x) + abs(current_position.y - y)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_ore_position = Vector(x, y)

        return nearest_ore_position

    def generate_moves(self, start_position, end_position, vertical_first, world):
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

        # Check for obstacles (walls) and visited positions
        valid_horizontal = [action for action in horizontal if self.is_valid_move(start_position, action, world)]
        valid_vertical = [action for action in vertical if self.is_valid_move(start_position, action, world)]

        return valid_vertical + valid_horizontal if vertical_first else valid_horizontal + valid_vertical
    
    def generate_moves2(self, start_position, end_position, vertical_first):
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
    
    def is_valid_move(self, position, action, world):
        """
        Check if a move is valid (not a wall and not visited).
        :param position:    The current position of the bot.
        :param action:      The ActionType of the move.
        :param world:       Generic world information.
        :return:            True if the move is valid, False otherwise.
        """
        new_position = Vector(position.x, position.y)  # Create a new Vector with the same coordinates

        if action == ActionType.MOVE_UP:
            new_position.y -= 1
        elif action == ActionType.MOVE_DOWN:
            new_position.y += 1
        elif action == ActionType.MOVE_LEFT:
            new_position.x -= 1
        elif action == ActionType.MOVE_RIGHT:
            new_position.x += 1

        # Check if the new position is within the bounds of the game map
        if (
            0 <= new_position.y < len(world.game_map) and
            0 <= new_position.x < len(world.game_map[0]) and
            world.game_map[new_position.y][new_position.x].occupied_by is not None
        ):
            # Check if the next move is a wall or already visited
            if (
                world.game_map[new_position.y][new_position.x].occupied_by.object_type == ObjectType.WALL
                or new_position in self.visited_positions
            ):
                return False

            # Add the new position to the set of visited positions
            self.visited_positions.add(new_position)
            return True

        return False



    def get_my_inventory(self, world):
        return world.inventory_manager.get_inventory(self.company)



















#check point