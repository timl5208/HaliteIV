from kaggle_environments.envs.halite.helpers import *

####################
# Helper functions #
####################

# Helper function we'll use for getting adjacent position with the most halite
def argmax(arr, key=None):
    return arr.index(max(arr, key=key)) if key else arr.index(max(arr))


# Converts position from 1D to 2D representation
def get_col_row(size, pos):
    return (pos % size, pos // size)


# Returns the position in some direction relative to the current position (pos)
def get_to_pos(size, pos, direction):
    col, row = get_col_row(size, pos)
    if direction == "NORTH":
        return pos - size if pos >= size else size ** 2 - size + col
    elif direction == "SOUTH":
        return col if pos + size >= size ** 2 else pos + size
    elif direction == "EAST":
        return pos + 1 if col < size - 1 else row * size
    elif direction == "WEST":
        return pos - 1 if col > 0 else (row + 1) * size - 1


# Get positions in all directions relative to the current position (pos)
# Especially useful for figuring out how much halite is around you
def getAdjacent(pos, size):
    return [
        get_to_pos(size, pos, "NORTH"),
        get_to_pos(size, pos, "SOUTH"),
        get_to_pos(size, pos, "EAST"),
        get_to_pos(size, pos, "WEST"),
    ]

def getAdjacentWithLevel(positions, size):
    for i in range(4):
        positions[i] = get_to_pos(size, positions[i], DIRS[i])
    return positions

# Returns best direction to move from one position (fromPos) to another (toPos)
# Example: If I'm at pos 0 and want to get to pos 55, which direction should I choose?
def getDirTo(fromPos, toPos, size):
    if fromPos == toPos: return "STAY"
    fromY, fromX = divmod(fromPos, size)
    toY, toX = divmod(toPos, size)
    if fromY < toY: return "SOUTH"
    if fromY > toY: return "NORTH"
    if fromX < toX: return "EAST"
    if fromX > toX: return "WEST"


# Possible directions a ship can move in
DIRS = ["NORTH", "SOUTH", "EAST", "WEST"]
# We'll use this to keep track of whether a ship is collecting halite or
# carrying its cargo to a shipyard
ship_states = {}


#############
# The agent #
#############
def agent(obs, config):

    board = Board(obs, config)

    should_spawn = True

    # Get the player's halite, shipyard locations, and ships (along with cargo)
    player_halite, shipyards, ships = obs.players[obs.player]

    opp_shipyards = obs.players[1 - obs.player][1]  # other guy

    size = config["size"]
    # Initialize a dictionary containing commands that will be sent to the game
    action = {}
    # Actual coordinates on the map
    position_choices = []

    # If there are no shipyards, convert first ship into shipyard.
    if len(shipyards) == 0 and len(ships) > 0:

        uid = list(ships.keys())[0]
        print("Ship ", uid, "converting, round# ", board.step)
        action[uid] = "CONVERT"

    ship_sorted_by_halite = sorted(ships.items(), key=lambda halite: halite[1][1], reverse=True)

    for uid, ship in ship_sorted_by_halite:

        if uid not in action:  # Ignore ships that will be converted to shipyards
            print("Ship ", uid, "round# ", board.step)
            pos, cargo = ship  # Get the ship's position and halite in cargo

            halite_dict = {}  # amount of halites at each map position

            ### Part 1: Set the ship's state
            if cargo < 200:  # If cargo is too low, collect halite
                ship_states[uid] = "COLLECT"
            if cargo > 500:  # If cargo gets very big, deposit halite
                ship_states[uid] = "DEPOSIT"

            ### Part 2: Use the ship's state to select an action
            print("position choices are", position_choices)
            print("ship status", ship_states[uid])
            if ship_states[uid] == "DEPOSIT":
                # Move towards shipyard to deposit cargo
                direction = getDirTo(pos, list(shipyards.values())[0], size)
                if direction:
                    next_pos = get_to_pos(size, pos, direction)
                    if next_pos not in position_choices:
                        position_choices.append(next_pos)
                        action[uid] = direction
                    else:
                        position_choices.append(pos)
            elif ship_states[uid] == "COLLECT":

                # put in different halite amount here
                if obs.halite[pos] < 20 or pos in position_choices:
                    level = 0
                    halite_bar = 20
                    positions = [pos] * 4
                    while halite_bar <= 20:
                        all_possible_pos = getAdjacentWithLevel(positions, size)
                        if level == 0:
                            all_possible_pos.append(pos)
                        print("all possible pos", all_possible_pos)
                        for i in all_possible_pos:
                            halite_amount = obs.halite[i]
                            if i not in position_choices and halite_amount > halite_bar:
                                halite_dict[i] = halite_amount
                                halite_bar = halite_amount
                        level += 1
                        print("actual possible pos", halite_dict.keys())

                    best_pos = max(halite_dict, key=halite_dict.get)  # could be far away
                    direction = getDirTo(pos, best_pos, size)
                    arriving_pos = get_to_pos(size, pos, direction)
                    if arriving_pos not in position_choices:
                        position_choices.append(arriving_pos)
                        if direction != "STAY":
                            action[uid] = direction
                else:
                    position_choices.append(pos)

            if uid in action:
                print("ship action", action[uid])
            else:
                print("no action")

    # If there are no ships, use first shipyard to spawn a ship.
    num_of_ship = int(player_halite / 1500)
    if len(ships) < num_of_ship and len(shipyards) > 0 and player_halite >= 500:
        shipyard = list(shipyards.items())[0]
        # print(shipyard)
        uid, pos = shipyard
        if pos not in position_choices:
            action[uid] = "SPAWN"
            position_choices.append(pos)

    position_choices = []

    return action