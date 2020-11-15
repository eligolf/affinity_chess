import numpy as np
import math
import contextlib
with contextlib.redirect_stdout(None):
    import pygame


#  --------------------------------------------------------------------------------
#                              Game settings
#  --------------------------------------------------------------------------------

game_mode = 'ai'  # Opponent, 'human' or 'ai'
is_ai_white = True  # Set to true if AI should play as white
play_with_opening_book = False  # Set to False to disable opening book

pos_testing = False  # Set up a special board for testing different positions and scenarios, see bottom of this file

# Negamax parameters
max_search_time = 5  # When it reaches more than x seconds for a move it makes a last search
min_search_depth = 6  # Choose to always search for at least a certain number of depth
max_search_depth = 6  # Used in iterative deepening

mvv_storing = 10  # How many of the MVV_LVV top candidates to use
no_of_killer_moves = 2  # Number of killer moves stored per depth
R = 2  # Used in nullmove logic

# Level of evaluation function
# 0 = Simple evaluation just to get piece values and placement of pieces
# 1 = Just one piece table for entire game with added bonus for mobility, bishop pair, castling
# 2 = Added more things....

evaluation_function = 2
eval_divisions = {0: 100,
                  1: 100,
                  2: 100}
eval_level = eval_divisions[evaluation_function]

static_evaluation = False  # Set to True if you want to see static evaluation for current position

# Level of AI.
# 0 = Random move
# 1 = Looks 1 half move ahead
# 2 = TBD. Right now set to level 1 in ai file.
# 3 = Negamax with alpha beta pruning

level = 3

# Time each function in the code
timing = False
timing_sort = 'tottime'  # Chose what to sort timing on. See options here: https://blog.alookanalytics.com/2017/03/21/python-profiling-basics/

# Sound
sound_piece_moved = 'sounds/chess_on_wood.wav'  # Sound file
toggle_sound = True  # Set to False to disable sound

#  --------------------------------------------------------------------------------
#                                Gui parameters
#  --------------------------------------------------------------------------------

# General
title = ' Chess'
icon = pygame.image.load('imgs/icon.ico')
icon_tkinter = r'C:\Users\Elias\Desktop\Python programs\Chess 2\20201107\imgs/icon.ico'

dimension = 8  # 8 squares in row/column
sq_size = 90
width = height = dimension * sq_size
fps = 120

# Piece images
images = {}
sprite = pygame.transform.smoothscale(pygame.image.load('imgs/pieces.png'), (int(sq_size*6), int(sq_size*2)))
pieces = ['wK', 'wQ', 'wB', 'wN', 'wR', 'wp', 'bK', 'bQ', 'bB', 'bN', 'bR', 'bp']
for i in range(2):
    for j in range(6):
        images[pieces[i*6 + j]] = pygame.Surface.subsurface(sprite, (j*sq_size, i*sq_size, sq_size, sq_size))

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
check_red = (200, 12, 12)
green = (0, 255, 0)
orange = (255, 128, 0)
grey = [(x*32, x*32, x*32) for x in reversed(range(1, 8))]  # Grey scale, from light to dark

# Board
start_board = {0: 'FF',   1: 'FF',   2: 'FF',   3: 'FF',   4: 'FF',   5: 'FF',   6: 'FF',   7: 'FF',   8: 'FF',   9: 'FF',   # [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9]
              10: 'FF',  11: 'FF',  12: 'FF',  13: 'FF',  14: 'FF',  15: 'FF',  16: 'FF',  17: 'FF',  18: 'FF',  19: 'FF',   # [ 10,  11,  12,  13,  14,  15,  16,  17,  18,  19]
              20: 'FF',  21: 'bR',  22: 'bN',  23: 'bB',  24: 'bQ',  25: 'bK',  26: 'bB',  27: 'bN',  28: 'bR',  29: 'FF',   # [ 20,  21,  22,  23,  24,  25,  26,  27,  28,  29]
              30: 'FF',  31: 'bp',  32: 'bp',  33: 'bp',  34: 'bp',  35: 'bp',  36: 'bp',  37: 'bp',  38: 'bp',  39: 'FF',   # [ 30,  31,  32,  33,  34,  35,  36,  37,  38,  39]
              40: 'FF',  41: '--',  42: '--',  43: '--',  44: '--',  45: '--',  46: '--',  47: '--',  48: '--',  49: 'FF',   # [ 40,  41,  42,  43,  44,  45,  46,  47,  48,  49]
              50: 'FF',  51: '--',  52: '--',  53: '--',  54: '--',  55: '--',  56: '--',  57: '--',  58: '--',  59: 'FF',   # [ 50,  51,  52,  53,  54,  55,  56,  57,  58,  59]
              60: 'FF',  61: '--',  62: '--',  63: '--',  64: '--',  65: '--',  66: '--',  67: '--',  68: '--',  69: 'FF',   # [ 60,  61,  62,  63,  64,  65,  66,  67,  68,  69]
              70: 'FF',  71: '--',  72: '--',  73: '--',  74: '--',  75: '--',  76: '--',  77: '--',  78: '--',  79: 'FF',   # [ 70,  71,  72,  73,  74,  75,  76,  77,  78,  79]
              80: 'FF',  81: 'wp',  82: 'wp',  83: 'wp',  84: 'wp',  85: 'wp',  86: 'wp',  87: 'wp',  88: 'wp',  89: 'FF',   # [ 80,  81,  82,  83,  84,  85,  86,  87,  88,  89]
              90: 'FF',  91: 'wR',  92: 'wN',  93: 'wB',  94: 'wQ',  95: 'wK',  96: 'wB',  97: 'wN',  98: 'wR',  99: 'FF',   # [ 90,  91,  92,  93,  94,  95,  96,  97,  98,  99]
             100: 'FF', 101: 'FF', 102: 'FF', 103: 'FF', 104: 'FF', 105: 'FF', 106: 'FF', 107: 'FF', 108: 'FF', 109: 'FF',   # [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
             110: 'FF', 111: 'FF', 112: 'FF', 113: 'FF', 114: 'FF', 115: 'FF', 116: 'FF', 117: 'FF', 118: 'FF', 119: 'FF'}   # [110, 111, 112, 113, 114, 115, 116, 117, 118, 119]

real_board_squares = {21, 22, 23, 24, 25, 26, 27, 28,
                      31, 32, 33, 34, 35, 36, 37, 38,
                      41, 42, 43, 44, 45, 46, 47, 48,
                      51, 52, 53, 54, 55, 56, 57, 58,
                      61, 62, 63, 64, 65, 66, 67, 68,
                      71, 72, 73, 74, 75, 76, 77, 78,
                      81, 82, 83, 84, 85, 86, 87, 88,
                      91, 92, 93, 94, 95, 96, 97, 98}

manhattan_distance = [6, 5, 4, 3, 3, 4, 5, 6,
                      5, 4, 3, 2, 2, 3, 4, 5,
                      4, 3, 2, 1, 1, 2, 3, 4,
                      3, 2, 1, 0, 0, 1, 2, 3,
                      3, 2, 1, 0, 0, 1, 2, 3,
                      4, 3, 2, 1, 1, 2, 3, 4,
                      5, 4, 3, 2, 2, 3, 4, 5,
                      6, 5, 4, 3, 3, 4, 5, 6]

# Used to flip square to black view
flip_board = {1: -8,
              2: -6,
              3: -4,
              4: -2,
              5:  0,
              6:  2,
              7:  4,
              8:  6}

directions = [-10, -1, 10, 1, -11, -9, 9, 11]  # Up, left, down, right, up/left, up/right, down/left, down/right
knight_moves = [-21, -19, -12, -8, 8, 12, 19, 21]  # Up-up-left, up-up-right ......

start_row_white = [x for x in range(81, 89)]
start_row_black = [x for x in range(31, 39)]
end_row_white = [x for x in range(21, 29)]
end_row_black = [x for x in range(91, 99)]

start_pos_white_king = 95
start_pos_black_king = 25

board_colors = [(130, 82, 1), (182, 155, 76)]
background = pygame.transform.smoothscale(pygame.image.load('imgs/bg.png'), (width, height))
numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
capital_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

#  --------------------------------------------------------------------------------
#                           AI parameters
#  --------------------------------------------------------------------------------

# Used in Negamax algorithm
if is_ai_white:
    start_color = -1
else:
    start_color = 1

# Piece base values
piece_value_base_mid_game = {'K': 60000,
                             'Q': 900,
                             'R': 490,
                             'B': 320,
                             'N': 290,
                             'p': 100}

piece_value_base_end_game = {'K': 60000,
                             'Q': 900,
                             'R': 490,
                             'B': 320,
                             'N': 290,
                             'p': 100}

# ------- Piece values/factors for different cases ----------------

# Number of squares that a piece is attacking in the center 4 squares and the surrounding ones as well
piece_center_attack = {'K': 0,
                       'Q': 5,
                       'R': 5,
                       'B': 5,
                       'N': 5,
                       'p': 5}

center_attacks = {0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,1,1,1,1,0,0,0,
                  0,0,0,1,2,2,1,0,0,0,
                  0,0,0,1,2,2,1,0,0,0,
                  0,0,0,1,1,1,1,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0,
                  0,0,0,0,0,0,0,0,0,0}

# MVV-LVA move ordering
mvv_lva_values = {'K': 20000,
                  'Q': 900,
                  'R': 490,
                  'B': 320,
                  'N': 290,
                  'p': 100,
                  '-': 0}

# Calculate the phase of the game
piece_phase_calc = {'K': 0,
                    'Q': 4,
                    'R': 2,
                    'B': 1,
                    'N': 1,
                    'p': 0}

endgame_phase_limit = 14  # Game phase starts at 24. When down to 14 or less then it is considered endgame. Tune this factor later

total_phase = 16*piece_phase_calc['p'] + 4*piece_phase_calc['B'] + 4*piece_phase_calc['N'] + 4*piece_phase_calc['R'] + 2*piece_phase_calc['Q']

# Piece tables
piece_value_mid_game = {'K': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
                                       0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
                                       0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
                                       0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
                                       0, -20, -30, -30, -40, -40, -30, -30, -20, 0,
                                       0, -10, -20, -20, -20, -20, -20, -20, -10, 0,
                                       0, 20, 20, 0, 0, 0, 0, 20, 20, 0,
                                       0, 20, 30, 0, 0, 0, 0, 30, 20, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'Q': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -20, -10, -10, -5, -5, -10, -10, -20, 0,
                                       0, -10, 0, 0, 0, 0, 0, 0, -10, 0,
                                       0, -10, 0, 5, 5, 5, 5, 0, -10, 0,
                                       0, -5, 0, 5, 5, 5, 5, 0, -5, 0,
                                       0, -5, 0, 5, 5, 5, 5, 0, -5, 0,
                                       0, -10, 5, 5, 5, 5, 5, 0, -10, 0,
                                       0, -10, 0, 5, 0, 0, 0, 0, -10, 0,
                                       0, -20, -10, -10, 0, 0, -10, -10, -20, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'R': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 5, 15, 15, 15, 15, 15, 15, 5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, 0, 0, 5, 10, 10, 5, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'B': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -20, -10, -10, -10, -10, -10, -10, -20, 0,
                                       0, -10, 0, 0, 0, 0, 0, 0, -10, 0,
                                       0, -10, 0, 5, 10, 10, 5, 0, -10, 0,
                                       0, -10, 5, 5, 10, 10, 5, 5, -10, 0,
                                       0, -10, 0, 10, 10, 10, 10, 0, -10, 0,
                                       0, -10, 10, 10, 10, 10, 10, 10, -10, 0,
                                       0, -10, 5, 0, 0, 0, 0, 5, -10, 0,
                                       0, -20, -10, -10, -10, -10, -10, -10, -20, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'N': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -50, -40, -30, -30, -30, -30, -40, -50, 0,
                                       0, -40, -20, 0, 0, 0, 0, -20, -40, 0,
                                       0, -30, 0, 10, 15, 15, 10, 0, -30, 0,
                                       0, -30, 5, 15, 20, 20, 15, 5, -30, 0,
                                       0, -30, 0, 15, 20, 20, 15, 0, -30, 0,
                                       0, -30, 5, 10, 15, 15, 10, 5, -30, 0,
                                       0, -40, -20, 0, 5, 5, 0, -20, -40, 0,
                                       0, -50, -40, -30, -30, -30, -30, -40, -50, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'p': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 50, 50, 50, 50, 50, 50, 50, 50, 0,
                                       0, 10, 10, 20, 30, 30, 20, 10, 10, 0,
                                       0, 5, 5, 10, 25, 25, 10, 5, 5, 0,
                                       0, 0, 0, 0, 20, 20, 0, 0, 0, 0,
                                       0, 5, -5, -10, 0, 0, -10, -5, 5, 0,
                                       0, 5, 10, 10, -20, -20, 10, 10, 5, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

piece_value_end_game = {'K': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -50, -40, -30, -20, -20, -30, -40, -50, 0,
                                       0, -30, -20, -10, 0, 0, -10, -20, -30, 0,
                                       0, -30, -10, 20, 30, 30, 20, -10, -30, 0,
                                       0, -30, -10, 30, 40, 40, 30, -10, -30, 0,
                                       0, -30, -10, 30, 40, 40, 30, -10, -30, 0,
                                       0, -30, -10, 20, 30, 30, 20, -10, -30, 0,
                                       0, -30, -30, 0, 0, 0, 0, -30, -30, 0,
                                       0, -50, -30, -30, -30, -30, -30, -30, -50, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'Q': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -20, -10, -10, -5, -5, -10, -10, -20, 0,
                                       0, -10, 0, 0, 0, 0, 0, 0, -10, 0,
                                       0, -10, 0, 5, 5, 5, 5, 0, -10, 0,
                                       0, -5, 0, 5, 5, 5, 5, 0, -5, 0,
                                       0, -5, 0, 5, 5, 5, 5, 0, -5, 0,
                                       0, -10, 5, 5, 5, 5, 5, 0, -10, 0,
                                       0, -10, 0, 5, 0, 0, 0, 0, -10, 0,
                                       0, -20, -10, -10, 0, 0, -10, -10, -20, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'R': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 5, 15, 15, 15, 15, 15, 15, 5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, -5, 0, 0, 0, 0, 0, 0, -5, 0,
                                       0, 0, 0, 5, 10, 10, 5, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'B': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -20, -10, -10, -10, -10, -10, -10, -20, 0,
                                       0, -10, 0, 0, 0, 0, 0, 0, -10, 0,
                                       0, -10, 0, 5, 10, 10, 5, 0, -10, 0,
                                       0, -10, 5, 5, 10, 10, 5, 5, -10, 0,
                                       0, -10, 0, 10, 10, 10, 10, 0, -10, 0,
                                       0, -10, 10, 10, 10, 10, 10, 10, -10, 0,
                                       0, -10, 5, 0, 0, 0, 0, 5, -10, 0,
                                       0, -20, -10, -10, -10, -10, -10, -10, -20, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'N': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, -50, -40, -30, -30, -30, -30, -40, -50, 0,
                                       0, -40, -20, 0, 0, 0, 0, -20, -40, 0,
                                       0, -30, 0, 10, 15, 15, 10, 0, -30, 0,
                                       0, -30, 5, 15, 20, 20, 15, 5, -30, 0,
                                       0, -30, 0, 15, 20, 20, 15, 0, -30, 0,
                                       0, -30, 5, 10, 15, 15, 10, 5, -30, 0,
                                       0, -40, -20, 0, 5, 5, 0, -20, -40, 0,
                                       0, -50, -40, -30, -30, -30, -30, -40, -50, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'p': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 50, 50, 50, 50, 50, 50, 50, 50, 0,
                                       0, 10, 10, 20, 30, 30, 20, 10, 10, 0,
                                       0, 5, 5, 10, 25, 25, 10, 5, 5, 0,
                                       0, 0, 0, 0, 20, 20, 0, 0, 0, 0,
                                       0, 5, -5, -10, 0, 0, -10, -5, 5, 0,
                                       0, 5, 10, 10, -20, -20, 10, 10, 5, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

# Extra bonuses
bishop_pair_bonus = 30
castling_bonus = 30
mobility_factor = 5

double_pawn_punishment = -30  # Give punishment if there are 2 pawns on the same column, maybe increase if late in game. Calibrate value
isolated_pawn_punishment = -30  # If the pawn has no allies on the columns next to it, calibrate value later

knight_endgame_punishment = -10  # Punishment for knights in endgame, per piece
bishop_endgame_bonus = 10  # Bonus for bishops in endgame, per piece

blocking_d_e_pawn_punishment = -40  # Punishment for blocking unmoved pawns on d and e file

# Not implemented
check_bonus = 50  # Give bonus if move results in a check, not implemented in code
rook_on_semi_open_file_bonus = 3000  # Give rook a bonus for being on an open file without any own pawns, per piece?
rook_on_open_file_bonus = 3000  # Give rook a bonus for being on an open file without any pawns, per piece?


# If down in material, punish exchanging material. And the opposite if up in material
# Add king_end piece table to logic (e.g. if no queens on the board or only queens and pawns)
#
# Other improvements to make on evaluation function:
#
# Attacking squares (how many squares own piece are attacking, including possibilities to take a piece)
# King safety, how many attackers are around the own king
#      - Attacking king, how many own pieces are attacking squares around enemy king
# Development bonus (bonus for developing bishops, knights, and do castle first, along with pawns, and then rooks and queen later)
# Pawn formations, passed pawns etc. Use pawn hash table?
# Rook behind passed pawn bonus
# Passed pawn against knight bonus, since knight can't move far very quickly

# Mobility per piece, e.g. give larger punishment if queen is less mobile. And difference punishment depending on state of game.
# Move same piece twice in opening punishment.


#  --------------------------------------------------------------------------------
#                            Test variables
#  --------------------------------------------------------------------------------

start_board_pos_test = {0: 'FF',   1: 'FF',   2: 'FF',   3: 'FF',   4: 'FF',   5: 'FF',   6: 'FF',   7: 'FF',   8: 'FF',   9: 'FF',
              10: 'FF',  11: 'FF',  12: 'FF',  13: 'FF',  14: 'FF',  15: 'FF',  16: 'FF',  17: 'FF',  18: 'FF',  19: 'FF',
              20: 'FF',  21: '--',  22: '--',  23: '--',  24: '--',  25: '--',  26: '--',  27: '--',  28: '--',  29: 'FF',
              30: 'FF',  31: '--',  32: '--',  33: '--',  34: '--',  35: 'bR',  36: 'bK',  37: '--',  38: '--',  39: 'FF',
              40: 'FF',  41: '--',  42: '--',  43: '--',  44: 'bR',  45: '--',  46: '--',  47: '--',  48: '--',  49: 'FF',
              50: 'FF',  51: '--',  52: '--',  53: '--',  54: '--',  55: '--',  56: '--',  57: '--',  58: '--',  59: 'FF',
              60: 'FF',  61: '--',  62: '--',  63: '--',  64: '--',  65: '--',  66: '--',  67: '--',  68: '--',  69: 'FF',
              70: 'FF',  71: '--',  72: '--',  73: '--',  74: '--',  75: '--',  76: '--',  77: '--',  78: '--',  79: 'FF',
              80: 'FF',  81: '--',  82: '--',  83: '--',  84: '--',  85: '--',  86: '--',  87: '--',  88: 'wR',  89: 'FF',
              90: 'FF',  91: 'wK',  92: '--',  93: '--',  94: '--',  95: '--',  96: '--',  97: '--',  98: '--',  99: 'FF',
             100: 'FF', 101: 'FF', 102: 'FF', 103: 'FF', 104: 'FF', 105: 'FF', 106: 'FF', 107: 'FF', 108: 'FF', 109: 'FF',
             110: 'FF', 111: 'FF', 112: 'FF', 113: 'FF', 114: 'FF', 115: 'FF', 116: 'FF', 117: 'FF', 118: 'FF', 119: 'FF'}

wk_pos_test, bk_pos_test = 91, 36

