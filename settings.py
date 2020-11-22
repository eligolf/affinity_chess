import gui
import PySimpleGUI as sg
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

#  --------------------------------------------------------------------------------
#                              Game settings
#  --------------------------------------------------------------------------------

# Negamax parameters for iterative deepening
max_search_time = 5  # When it reaches more than x seconds for a move it makes a last search
min_search_depth = 6  # Choose to always search for at least a certain number of depth
max_search_depth_strong = 60
max_search_depth_medium = 4
max_search_depth_easy = 2

# Set to True to enable opening book
play_with_opening_book = False

# Set to True if you want to see static evaluation for current position
static_evaluation = False

# Level of AI.
# 0 = Random move
# 1 = Looks 1 half move ahead
# 2 = TBD
# 3 = Negamax with alpha beta pruning
level = 3

# Default start position if no value is set in start pop up window
start_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

# Time each function in the code, for efficiency development
timing = False
timing_sort = 'tottime'  # Chose what to sort timing on. See options here: https://blog.alookanalytics.com/2017/03/21/python-profiling-basics/

# Sounds
sound_piece_moved = 'sounds/chess_on_wood.wav'
sound_move = 'sounds/move.mp3'
sound_capture = 'sounds/capture.mp3'
toggle_sound = True  # Set to False to disable sound

#  --------------------------------------------------------------------------------
#                             FEN related settings
#  --------------------------------------------------------------------------------
# For enpassant square conversion
fen_letters = {'a': '1',
               'b': '2',
               'c': '3',
               'd': '4',
               'e': '5',
               'f': '6',
               'g': '7',
               'h': '8'}

fen_numbers = {'3': '7',
               '6': '4'}

# FEN representation to board pieces
fen_to_piece = {'p': 'bp',
                'n': 'bN',
                'b': 'bB',
                'r': 'bR',
                'q': 'bQ',
                'k': 'bK',
                'P': 'wp',
                'N': 'wN',
                'B': 'wB',
                'R': 'wR',
                'Q': 'wQ',
                'K': 'wK'}

# For enpassant square conversion
fen_letters_ep = {'1': 'a',
                  '2': 'b',
                  '3': 'c',
                  '4': 'd',
                  '5': 'e',
                  '6': 'f',
                  '7': 'g',
                  '8': 'h'}

fen_numbers_ep = {'7': '3',
                  '4': '6'}

# Board pieces to FEN representation
piece_to_fen = {'bp': 'p',
                'bN': 'n',
                'bB': 'b',
                'bR': 'r',
                'bQ': 'q',
                'bK': 'k',
                'wp': 'P',
                'wN': 'N',
                'wB': 'B',
                'wR': 'R',
                'wQ': 'Q',
                'wK': 'K'}


#  --------------------------------------------------------------------------------
#                                Gui parameters
#  --------------------------------------------------------------------------------

# General
title = ' Chess'
icon = pygame.image.load('imgs/icon.ico')

dimension = 8  # 8 rows and 8 columns
sq_size = 90
width = height = dimension * sq_size
fps = 60

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
real_board_squares = [21, 22, 23, 24, 25, 26, 27, 28,
                      31, 32, 33, 34, 35, 36, 37, 38,
                      41, 42, 43, 44, 45, 46, 47, 48,
                      51, 52, 53, 54, 55, 56, 57, 58,
                      61, 62, 63, 64, 65, 66, 67, 68,
                      71, 72, 73, 74, 75, 76, 77, 78,
                      81, 82, 83, 84, 85, 86, 87, 88,
                      91, 92, 93, 94, 95, 96, 97, 98]

king_distance_table = [x for x in range(64)]

manhattan_distance = [6, 5, 4, 3, 3, 4, 5, 6,
                      5, 4, 3, 2, 2, 3, 4, 5,
                      4, 3, 2, 1, 1, 2, 3, 4,
                      3, 2, 1, 0, 0, 1, 2, 3,
                      3, 2, 1, 0, 0, 1, 2, 3,
                      4, 3, 2, 1, 1, 2, 3, 4,
                      5, 4, 3, 2, 2, 3, 4, 5,
                      6, 5, 4, 3, 3, 4, 5, 6]

# Used to flip squares to black point of view
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

board_colors = [(130, 82, 1), (182, 155, 76)]
background = pygame.transform.smoothscale(pygame.image.load('imgs/bg.png'), (width, height))
numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
capital_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Start up window
sg.theme('DarkAmber')
start_up = [[sg.Text('')],
            [sg.Text('Start FEN (Optional): ', size=(15, 1)), sg.InputText(size=(60, 1), key='fen')],
            [sg.Text('')],
            [sg.Text('Opponent:  '), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai'), sg.Radio('Human', '1', size=(5, 1), key='human')],
            [sg.Text('Play as:     '), sg.Radio('White', '2', default=True, size=(5, 1), key='white'), sg.Radio('Black', '2', key='black')],
            [sg.Text('AI strength:'), sg.Radio('Strong', '3', default=True, size=(5, 1), key='strong'), sg.Radio('Medium', '3', key='medium'), sg.Radio('Easy', '3', key='easy')],
            [sg.Text('')],
            [sg.Submit()]]

wrong_fen_start_up = [[sg.Text('')],
                      [sg.Text('Start FEN (Optional): ', size=(15, 1)), sg.InputText(size=(60, 1), key='fen')],
                      [sg.Text('Please enter a valid FEN, or leave empty for start position.', text_color='red')],
                      [sg.Text('')],
                      [sg.Text('Opponent:  '), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai'), sg.Radio('Human', '1', size=(5, 1), key='human')],
                      [sg.Text('Play as:     '), sg.Radio('White', '2', default=True, size=(5, 1), key='white'), sg.Radio('Black', '2', key='black')],
                      [sg.Text('AI strength:'), sg.Radio('Strong', '3', default=True, size=(5, 1), key='strong'), sg.Radio('Medium', '3', key='medium'), sg.Radio('Easy', '3', key='easy')],
                      [sg.Text('')],
                      [sg.Submit()]]


#  --------------------------------------------------------------------------------
#                           AI parameters
#  --------------------------------------------------------------------------------

mvv_storing = 10  # How many of the MVV_LVV top candidates to use
no_of_killer_moves = 2  # Number of killer moves stored per depth
R = 2  # Used in nullmove logic

# Level of evaluation function
# 0 = Simple evaluation just to get piece values and placement of pieces
# 1 = Just one piece table for entire game with added bonus for bishop pair and castling
# 2 = Main best evaluation function
evaluation_function = 2
eval_divisions = {0: 100,
                  1: 100,
                  2: 100}
eval_level = eval_divisions[evaluation_function]

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

center_attacks = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 1, 1, 1, 1, 0, 0, 0,
                  0, 0, 0, 1, 2, 2, 1, 0, 0, 0,
                  0, 0, 0, 1, 2, 2, 1, 0, 0, 0,
                  0, 0, 0, 1, 1, 1, 1, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

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

# Piece tables
king_mid = [0,   0,   0,   0,   0,   0,   0,   0,   0, 0,
            0,   0,   0,   0,   0,   0,   0,   0,   0, 0,
            0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
            0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
            0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
            0, -30, -40, -40, -50, -50, -40, -40, -30, 0,
            0, -20, -30, -30, -40, -40, -30, -30, -20, 0,
            0, -10, -20, -20, -20, -20, -20, -20, -10, 0,
            0,  20,  20,   0,   0,   0,   0,  20,  20, 0,
            0,  20,  30,   0,   0,   0,   0,  30,  20, 0,
            0,   0,   0,   0,   0,   0,   0,   0,   0, 0,
            0,   0,   0,   0,   0,   0,   0,   0,   0, 0]
queen_mid = [0,   0,   0,   0,  0,  0,   0,   0,   0, 0,
             0,   0,   0,   0,  0,  0,   0,   0,   0, 0,
             0, -20, -10, -10, -5, -5, -10, -10, -20, 0,
             0, -10,   0,   0,  0,  0,   0,   0, -10, 0,
             0, -10,   0,   5,  5,  5,   5,   0, -10, 0,
             0,  -5,   0,   5,  5,  5,   5,   0,  -5, 0,
             0,  -5,   0,   5,  5,  5,   5,   0,  -5, 0,
             0, -10,   5,   5,  5,  5,   5,   0, -10, 0,
             0, -10,   0,   5,  0,  0,   0,   0, -10, 0,
             0, -20, -10, -10,  0,  0, -10, -10, -20, 0,
             0,   0,   0,   0,  0,  0,   0,   0,   0, 0,
             0,   0,   0,   0,  0,  0,   0,   0,   0, 0]
rook_mid = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
bishop_mid = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0, -20, -10, -10, -10, -10, -10, -10, -20, 0,
              0, -10, 0, 0, 0, 0, 0, 0, -10, 0,
              0, -10, 0, 5, 10, 10, 5, 0, -10, 0,
              0, -10, 5, 5, 10, 10, 5, 5, -10, 0,
              0, -10, 0, 10, 10, 10, 10, 0, -10, 0,
              0, -10, 10, 10, 10, 10, 10, 10, -10, 0,
              0, -10, 10, 0, 10, 10, 0, 10, -10, 0,
              0, -20, -10, -30, -10, -10, -30, -10, -20, 0,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
knight_mid = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
pawn_mid = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

king_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
queen_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
rook_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
bishop_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
knight_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
pawn_end = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
piece_value_mid_game = {'K': king_mid,
                        'Q': queen_mid,
                        'R': rook_mid,
                        'B': bishop_mid,
                        'N': knight_mid,
                        'p': pawn_mid}

piece_value_end_game = {'K': king_end,
                        'Q': queen_end,
                        'R': rook_end,
                        'B': bishop_end,
                        'N': knight_end,
                        'p': pawn_end}

# Extra bonus/punishment
bishop_pair_bonus = 15
castling_bonus = 20
mobility_factor = 5

double_pawn_punishment = -30  # Give punishment if there are 2 pawns on the same column, maybe increase if late in game. Calibrate value
isolated_pawn_punishment = -30  # If the pawn has no allies on the columns next to it, calibrate value later

knight_endgame_punishment = -10  # Punishment for knights in endgame, per piece
bishop_endgame_bonus = 10  # Bonus for bishops in endgame, per piece

rook_on_semi_open_file_bonus = 20  # Give rook a bonus for being on an open file without any own pawns, right now it is per rook
rook_on_open_file_bonus = 20  # Give rook a bonus for being on an open file without any pawns, right now it is per rook

blocking_d_e_pawn_punishment = -40  # Punishment for blocking unmoved pawns on d and e file


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
