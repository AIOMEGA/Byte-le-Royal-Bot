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
            # buy Improved Mining tech if I can...
            if avatar.science_points >= avatar.get_tech_info('Improved Mining').cost and not avatar.is_researched('Improved Mining'):
                return [ActionType.BUY_IMPROVED_MINING]
            if avatar.science_points >= avatar.get_tech_info('Improved Drivetrain').cost and not avatar.is_researched('Improved Drivetrain'):
                return [ActionType.BUY_IMPROVED_DRIVETRAIN]
            if avatar.science_points >= avatar.get_tech_info('Superior Mining').cost and not avatar.is_researched('Superior Mining'):
                return [ActionType.BUY_SUPERIOR_MINING]
            if avatar.science_points >= avatar.get_tech_info('Superior Drivetrain').cost and not avatar.is_researched('Superior Drivetrain'):
                return [ActionType.BUY_SUPERIOR_DRIVETRAIN]
            if avatar.science_points >= avatar.get_tech_info('Overdrive Mining').cost and not avatar.is_researched('Overdrive Mining'):
                return [ActionType.BUY_OVERDRIVE_MINING]  
            if avatar.science_points >= avatar.get_tech_info('Overdrive Drivetrain').cost and not avatar.is_researched('Overdrive Drivetrain'):
                return [ActionType.BUY_OVERDRIVE_DRIVETRAIN]
            # otherwise set my state to mining
            self.current_state = State.MINING
        if current_tile.occupied_by.object_type == self.my_station_type:
            if self.company == Company.CHURCH:
                actions = ActionType.MOVE_LEFT
            else:
                actions = ActionType.MOVE_RIGHT


        # Get the current position of the bot
        current_position = avatar.position

        # Example of finding the nearest ore
        nearest_ore_position = self.find_nearest_ore(current_position, world)

        # If I have at least 5 items in my inventory, set my state to selling
        if len([item for item in self.get_my_inventory(world) if item is not None]) >= 20:
            self.current_state = State.SELLING

        if self.nearing_end is not None and self.current_state == State.MINING:
            move_actions = self.generate_moves2
            actions += move_actions
        # Move towards the ore if it's found
        if nearest_ore_position is not None and self.current_state == State.MINING:
            move_actions = self.generate_moves(current_position, nearest_ore_position, turn % 2 == 0, world)
            actions = move_actions  # Combine move actions with existing actions
            
        
        

        # Make action decision for this turn
        if self.current_state == State.SELLING:
            actions = self.generate_moves2
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
        This function will generate a path between the start and end position.
        It does not consider walls and will try to walk directly to the end position.
        :param start_position:      Position to start at
        :param end_position:        Position to get to
        :param vertical_first:      True if the path should be vertical first, False if the path should be horizontal first
        :return:                    Path represented as a list of ActionType
        """
        dx = end_position.x - start_position.x
        dy = end_position.y - start_position.y

        # Generate a list of actions based on the difference in coordinates
        horizontal_actions = [ActionType.MOVE_LEFT] * min(dx, 0) + [ActionType.MOVE_RIGHT] * max(dx, 0)
        vertical_actions = [ActionType.MOVE_UP] * min(dy, 0) + [ActionType.MOVE_DOWN] * max(dy, 0)

        # Combine vertical and horizontal actions based on the preference
        actions = vertical_actions + horizontal_actions if vertical_first else horizontal_actions + vertical_actions

        # Filter out invalid moves
        valid_moves = [action for action in actions if self.is_valid_move(start_position, action, world)]
        
        # Check if there's any valid move, otherwise, move randomly
        if not valid_moves:
            valid_moves = [random.choice([ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT, ActionType.MOVE_UP, ActionType.MOVE_DOWN])]

        return valid_moves

    
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
    def distance_to_base(self, position, action, world):
        if self.company == Company.CHURCH:
            if position == [1,1]:
                distance = 3
            elif position == [1,2]:
                distance = 2
            elif position == [1,3]:
                distance = 1
            elif position == [1,4]:
                distance = 0
            elif position == [1,7]:
                distance = 27
            elif position == [1,8]:
                distance = 28
            elif position == [1,9]:
                distance = 29
            elif position == [1,10]:
                distance = 30
            elif position == [1,11]:
                distance = 31
            elif position == [2,1]:
                distance = 4
            elif position == [2,2]:
                distance = 3
            elif position == [2,3]:
                distance = 2
            elif position == [2,6]:
                distance = 25
            elif position == [2,7]:
                distance = 26
            elif position == [2,8]:
                distance = 27
            elif position == [2,9]:
                distance = 28
            elif position == [2,10]:
                distance = 29
            elif position == [2,11]:
                distance = 30
            elif position == [2,12]:
                distance = 31
            elif position == [3,1]:
                distance = 5
            elif position == [3,2]:
                distance = 4
            elif position == [3,5]:
                distance = 23
            elif position == [3,6]:
                distance = 24
            elif position == [3,7]:
                distance = 25
            elif position == [3,8]:
                distance = 26
            elif position == [3,10]:
                distance = 30
            elif position == [3,11]:
                distance = 31
            elif position == [3,12]:
                distance = 32
            elif position == [4,1]:
                distance = 6
            elif position == [4,2]:
                distance = 5
            elif position == [4,4]:
                distance = 23
            elif position == [4,5]:
                distance = 22
            elif position == [4,6]:
                distance = 23
            elif position == [4,7]:
                distance = 24
            elif position == [4,8]:
                distance = 24
            elif position == [4,11]:
                distance = 32
            elif position == [4,12]:
                distance = 33
            elif position == [5,1]:
                distance = 7
            elif position == [5,2]:
                distance = 6
            elif position == [5,4]:
                distance = 22
            elif position == [5,5]:
                distance = 21
            elif position == [5,6]:
                distance = 22
            elif position == [5,7]:
                distance = 23
            elif position == [5,8]:
                distance = 24
            elif position == [5,9]:
                distance = 25
            elif position == [5,11]:
                distance = 33
            elif position == [5,12]:
                distance = 34
            elif position == [6,1]:
                distance = 8
            elif position == [6,2]:
                distance = 7
            elif position == [6,4]:
                distance = 21
            elif position == [6,5]:
                distance = 20
            elif position == [6,6]:
                distance = 21
            elif position == [6,7]:
                distance = 22
            elif position == [6,8]:
                distance = 23
            elif position == [6,9]:
                distance = 24
            elif position == [6,11]:
                distance = 34
            elif position == [6,12]:
                distance = 35
            elif position == [7,1]:
                distance = 9
            elif position == [7,2]:
                distance = 8
            elif position == [7,4]:
                distance = 20
            elif position == [7,5]:
                distance = 19
            elif position == [7,6]:
                distance = 20
            elif position == [7,7]:
                distance = 21
            elif position == [7,8]:
                distance = 22
            elif position == [7,9]:
                distance = 23
            elif position == [7,11]:
                distance = 35
            elif position == [7,12]:
                distance = 36
            elif position == [8,1]:
                distance = 10
            elif position == [8,2]:
                distance = 9
            elif position == [8,4]:
                distance = 19
            elif position == [8,5]:
                distance = 20
            elif position == [8,6]:
                distance = 19
            elif position == [8,7]:
                distance = 20
            elif position == [8,8]:
                distance = 21
            elif position == [8,9]:
                distance = 22
            elif position == [8,11]:
                distance = 36
            elif position == [8,12]:
                distance = 37
            elif position == [9,1]:
                distance = 11
            elif position == [9,2]:
                distance = 10
            elif position == [9,5]:
                distance = 17
            elif position == [9,6]:
                distance = 18
            elif position == [9,7]:
                distance = 19
            elif position == [9,8]:
                distance = 20
            elif position == [9,9]:
                distance = 21
            elif position == [9,11]:
                distance = 37
            elif position == [9,12]:
                distance = 38
            elif position == [10,1]:
                distance = 12
            elif position == [10,2]:
                distance = 11
            elif position == [10,3]:
                distance = 12
            elif position == [10,5]:
                distance = 16
            elif position == [10,6]:
                distance = 17
            elif position == [10,7]:
                distance = 18
            elif position == [10,8]:
                distance = 19
            elif position == [10,11]:
                distance = 38
            elif position == [10,12]:
                distance = 39
            elif position == [11,1]:
                distance = 13
            elif position == [11,2]:
                distance = 12
            elif position == [11,3]:
                distance = 13
            elif position == [11,4]:
                distance = 14
            elif position == [11,5]:
                distance = 15
            elif position == [11,6]:
                distance = 16
            elif position == [11,7]:
                distance = 17
            elif position == [11,10]:
                distance = 40
            elif position == [11,11]:
                distance = 39
            elif position == [11,12]:
                distance = 40
            elif position == [12,2]:
                distance = 13
            elif position == [12,3]:
                distance = 14
            elif position == [12,4]:
                distance = 15
            elif position == [12,5]:
                distance = 16
            elif position == [12,6]:
                distance = 17
            elif position == [12,9]:
                distance = 42
            elif position == [12,10]:
                distance = 41
            elif position == [12,11]:
                distance = 40
            elif position == [12,12]:
                distance = 41
        if self.company == Company.TURING:
            if position == [1,1]:
                distance = 41
            elif position == [1,2]:
                distance = 40
            elif position == [1,3]:
                distance = 41
            elif position == [1,4]:
                distance = 42
            elif position == [1,7]:
                distance = 17
            elif position == [1,8]:
                distance = 16
            elif position == [1,9]:
                distance = 15
            elif position == [1,10]:
                distance = 14
            elif position == [1,11]:
                distance = 13
            elif position == [2,1]:
                distance = 40
            elif position == [2,2]:
                distance = 39
            elif position == [2,3]:
                distance = 40
            elif position == [2,6]:
                distance = 17
            elif position == [2,7]:
                distance = 16
            elif position == [2,8]:
                distance = 15
            elif position == [2,9]:
                distance = 14
            elif position == [2,10]:
                distance = 13
            elif position == [2,11]:
                distance = 12
            elif position == [2,12]:
                distance = 13
            elif position == [3,1]:
                distance = 39
            elif position == [3,2]:
                distance = 38
            elif position == [3,5]:
                distance = 19
            elif position == [3,6]:
                distance = 18
            elif position == [3,7]:
                distance = 17
            elif position == [3,8]:
                distance = 16
            elif position == [3,10]:
                distance = 12
            elif position == [3,11]:
                distance = 11
            elif position == [3,12]:
                distance = 12
            elif position == [4,1]:
                distance = 37
            elif position == [4,2]:
                distance = 36
            elif position == [4,4]:
                distance = 21
            elif position == [4,5]:
                distance = 20
            elif position == [4,6]:
                distance = 19
            elif position == [4,7]:
                distance = 18
            elif position == [4,8]:
                distance = 17
            elif position == [4,11]:
                distance = 10
            elif position == [4,12]:
                distance = 11
            elif position == [5,1]:
                distance = 36
            elif position == [5,2]:
                distance = 35
            elif position == [5,4]:
                distance = 22
            elif position == [5,5]:
                distance = 21
            elif position == [5,6]:
                distance = 20
            elif position == [5,7]:
                distance = 19
            elif position == [5,8]:
                distance = 18
            elif position == [5,9]:
                distance = 19
            elif position == [5,11]:
                distance = 9
            elif position == [5,12]:
                distance = 10
            elif position == [6,1]:
                distance = 35
            elif position == [6,2]:
                distance = 34
            elif position == [6,4]:
                distance = 23
            elif position == [6,5]:
                distance = 22
            elif position == [6,6]:
                distance = 21
            elif position == [6,7]:
                distance = 20
            elif position == [6,8]:
                distance = 19
            elif position == [6,9]:
                distance = 20
            elif position == [6,11]:
                distance = 8
            elif position == [6,12]:
                distance = 9
            elif position == [7,1]:
                distance = 34
            elif position == [7,2]:
                distance = 33
            elif position == [7,4]:
                distance = 24
            elif position == [7,5]:
                distance = 23
            elif position == [7,6]:
                distance = 22
            elif position == [7,7]:
                distance = 21
            elif position == [7,8]:
                distance = 20
            elif position == [7,9]:
                distance = 21
            elif position == [7,11]:
                distance = 7
            elif position == [7,12]:
                distance = 8
            elif position == [8,1]:
                distance = 33
            elif position == [8,2]:
                distance = 32
            elif position == [8,4]:
                distance = 25
            elif position == [8,5]:
                distance = 24
            elif position == [8,6]:
                distance = 23
            elif position == [8,7]:
                distance = 22
            elif position == [8,8]:
                distance = 21
            elif position == [8,9]:
                distance = 22
            elif position == [8,11]:
                distance = 6
            elif position == [8,12]:
                distance = 7
            elif position == [9,1]:
                distance = 31
            elif position == [9,2]:
                distance = 31
            elif position == [9,5]:
                distance = 26
            elif position == [9,6]:
                distance = 25
            elif position == [9,7]:
                distance = 24
            elif position == [9,8]:
                distance = 23
            elif position == [9,9]:
                distance = 24
            elif position == [9,11]:
                distance = 5
            elif position == [9,12]:
                distance = 6
            elif position == [10,1]:
                distance = 30
            elif position == [10,2]:
                distance = 29
            elif position == [10,3]:
                distance = 30
            elif position == [10,5]:
                distance = 27
            elif position == [10,6]:
                distance = 26
            elif position == [10,7]:
                distance = 25
            elif position == [10,8]:
                distance = 25
            elif position == [10,11]:
                distance = 4
            elif position == [10,12]:
                distance = 5
            elif position == [11,1]:
                distance = 28
            elif position == [11,2]:
                distance = 29
            elif position == [11,3]:
                distance = 30
            elif position == [11,4]:
                distance = 31
            elif position == [11,5]:
                distance = 28
            elif position == [11,6]:
                distance = 29
            elif position == [11,7]:
                distance = 30
            elif position == [11,10]:
                distance = 2
            elif position == [11,11]:
                distance = 3
            elif position == [11,12]:
                distance = 4
            elif position == [12,2]:
                distance = 30
            elif position == [12,3]:
                distance = 30
            elif position == [12,4]:
                distance = 29
            elif position == [12,5]:
                distance = 29
            elif position == [12,6]:
                distance = 28
            elif position == [12,9]:
                distance = 0
            elif position == [12,10]:
                distance = 1
            elif position == [12,11]:
                distance = 2
            elif position == [12,12]:
                distance = 3
        return distance
            
    def generate_moves_to_home(self, position, world):
        current_tile = [position[0]][position[1]]
        y = current_tile[0]
        x = current_tile[1]
        if self.company == Company.CHURCH:
            if x >= 10:
                if y > 2:
                    action = ActionType.MOVE_UP
                else:
                    action = ActionType.MOVE_RIGHT
            elif x == 8 or x == 9:
                if y > 10:
                    action = ActionType.MOVE_RIGHT
                else:
                    action = ActionType.MOVE_LEFT
            elif x >= 5 and x <=7:
                if y < 12:
                    action = ActionType.MOVE_DOWN
                else:
                    action = ActionType.MOVE_UP
            elif x == 4:
                if y > 10:
                    action = ActionType.MOVE_LEFT
                if y < 10:
                    action = ActionType.MOVE_RIGHT
            elif x == 3:
                if y > 3:
                    action = ActionType.MOVE_LEFT
                elif y == 2:
                    action = ActionType.MOVE_UP
                else:
                    action = ActionType.MOVE_RIGHT
                
            elif x < 3:
                if y != 1:
                    action = ActionType.MOVE_UP
        elif self.company==Company.TURING:
            if x < 3:
                if y < 12:
                    action = ActionType.MOVE_DOWN
                else:
                    action = ActionType.MOVE_UP
            elif x == 3:
                if y < 3:
                    action = ActionType.MOVE_LEFT
                elif y == 10:
                    action = ActionType.MOVE_DOWN
                else:
                    action = ActionType.MOVE_RIGHT
            elif x == 4 or x == 5:
                action = ActionType.MOVE_RIGHT
            elif x <= 8 and x >= 6:
                if y < 12:
                    action = ActionType.MOVE_UP
                elif y == 12:
                    action = ActionType.MOVE_DOWN
            elif x == 9:
                if y < 3:
                    action = ActionType.MOVE_RIGHT
                else:
                    action = ActionType.MOVE_LEFT
            elif x == 10:
                if y < 4:
                    action = ActionType.MOVE_RIGHT
                elif y == 11:
                    action = ActionType.MOVE_DOWN
                elif y == 12:
                    action = ActionType.MOVE_LEFT
            elif x == 11 or x == 12:
                if y < 12:
                    action = ActionType.MOVE_DOWN
                elif y == 12:
                    action = ActionType.MOVE_LEFT
        else:
            return None
        return action
    def nearing_end(self, turn, position, action, world):
        if (200-turn < self.distance_to_base + 3):
            action = self.generate_moves_to_home()
        else:
            action = None
        return action


    def get_my_inventory(self, world):
        return world.inventory_manager.get_inventory(self.company)
    



















#check point