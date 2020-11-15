# --------------------------------------------------------------------------------
#                 Board handling piece move functionality
# --------------------------------------------------------------------------------

import settings as s
import ai

import time
import copy
import random
from itertools import chain


class GameState:

    def __init__(self):

        # When testing positions, change this boolean in settings file
        if s.pos_testing:
            self.board = copy.deepcopy(s.start_board_pos_test)
            self.white_king_location, self.black_king_location = s.wk_pos_test, s.bk_pos_test
        else:
            self.board = copy.deepcopy(s.start_board)  # Initialize board to start position
            self.white_king_location, self.black_king_location = s.start_pos_white_king, s.start_pos_black_king

        # Get possible moves for a certain piece type
        self.move_functions = {'p': self.get_pawn_moves,
                               'N': self.get_knight_moves,
                               'B': self.get_bishop_moves,
                               'R': self.get_rook_moves,
                               'Q': self.get_queen_moves,
                               'K': self.get_king_moves}

        self.white_wins = False
        self.is_white_turn = True
        self.move_counter = 1

        self.pins, self.checks = [], []
        self.is_in_check = False
        self.is_check_mate, self.is_stale_mate = False, False
        self.kind_of_stalemate = ''

        self.castling_rights = [True, True, True, True]  # W king side, W queen side, B king side, B queen side
        self.white_has_castled, self.black_has_castled = False, False

        self.enpassant_square = None  # The square where an enpassant is possible
        self.enpassant_made = False
        self.is_pawn_promotion = False

        self.white_mobility, self.black_mobility = 0, 0  # Mobility = number of valid moves times a factor (mobility factor in settings file)

        self.piece_moved, self.piece_captured = '--', '--'

        # Init Zobrist board (https://www.youtube.com/watch?v=gyLCFfrLGIM)
        self.zobrist_board = {}
        self.zobrist_pieces = [0] * 64  # One for each square
        self.zobrist_enpassant = [0] * 8  # One for each column
        self.enpassant_row = None  # Init what column is valid
        self.zobrist_castling = [0] * 4  # W king side, W queen side, B king side, B queen side
        self.zobrist_black_to_move = 0  # Turn

        self.zobrist_key = self.init_zobrist()

        # Gamestate phase (opening, midgame or endgame?)
        self.gamestate_phase = copy.deepcopy(s.total_phase)
        self.midgame, self.endgame = 1, 0
        self.piece_values = self.init_piece_values()

        # Checking 3 fold repetition and 50 move stalemate rules
        self.three_fold = {}
        self.fifty_move_clock = 0

        # Keep track of where pawns are located on the board for evaluation
        self.pawn_columns_list = [[1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8]]
        self.rook_columns_list = [[1, 8], [1, 8]]

        # Distance between the 2 kings
        self.king_distance = 7

        # Keep track of number of pieces on the board
        self.piece_dict = [{'p': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1}, {'p': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1}][:]  # W, B

        # Placeholder to be able to access move_log[-1]. [from square, to square, piece moved, piece_captured, castling rights, enpassant square, enpassant made, zobrist key...
        # ... piece_values, move_is_pawn_promotion]
        self.move_log = [[0, 0, '--', '--', [True, True, True, True], None, False, self.zobrist_key, self.piece_values[:], self.is_pawn_promotion]]

# ---------------------------------------------------------------------------------------------------------
#             Make and unmake move functions, Zobrist key
# ---------------------------------------------------------------------------------------------------------

    def make_move(self, start_square, end_square):

        # Square dependent on white or black
        from_square, to_square = (start_square, end_square) if self.is_white_turn else (120 - start_square + s.flip_board[start_square % 10], 120 - end_square + s.flip_board[end_square % 10])
        capture_square = end_square if not self.is_white_turn else 120 - end_square + s.flip_board[end_square % 10]

        # Update piece_moved and piece_captured
        self.piece_moved = self.board[start_square]
        self.piece_captured = self.board[end_square]

        # Update board
        self.board[start_square] = '--'
        self.board[end_square] = self.piece_moved

        # Update Zobrist key
        self.zobrist_key ^= self.zobrist_board[start_square][self.piece_moved]  # Remove piece from start square
        self.zobrist_key ^= self.zobrist_board[end_square][self.piece_captured]  # Remove the piece that was on the end square
        self.zobrist_key ^= self.zobrist_board[end_square][self.piece_moved]  # Place the moved piece on its end square

        # For debugging...
        if self.piece_moved == '--':
            for item in self.move_log:
                print(item)
            print(self.board)
            print(start_square, end_square)
            print(self.is_white_turn)

        # Update the king position
        if self.piece_moved == 'wK':
            self.white_king_location = end_square
        elif self.piece_moved == 'bK':
            self.black_king_location = end_square

        # Pawn promotion
        self.is_pawn_promotion = False
        if (self.piece_moved == 'wp' and end_square in s.end_row_white) or (self.piece_moved == 'bp' and end_square in s.end_row_black):
            self.is_pawn_promotion = True
            self.board[end_square] = f'{self.piece_moved[0]}Q'  # Implement ability to promote to other pieces than queen later

            self.piece_dict[not self.is_white_turn]['p'] -= 1
            self.piece_dict[not self.is_white_turn]['Q'] += 1

            self.zobrist_key ^= self.zobrist_board[end_square][self.piece_moved]  # Remove the pawn from end_square again since it is now a queen
            self.zobrist_key ^= self.zobrist_board[end_square][f'{self.piece_moved[0]}Q']  # Place a queen there instead

            moved_piece_value_change_mid = (-(s.piece_value_base_mid_game['p'] + s.piece_value_mid_game['p'][from_square]) +
                                             (s.piece_value_base_mid_game['Q'] + s.piece_value_mid_game['Q'][to_square])) * self.midgame
            moved_piece_value_change_end = (-(s.piece_value_base_end_game['p'] + s.piece_value_end_game['p'][from_square]) +
                                             (s.piece_value_base_end_game['Q'] + s.piece_value_end_game['Q'][to_square])) * self.endgame

        # Update pawn columns list
        if self.piece_moved[1] == 'p' and (start_square - end_square) % 10 > 0:
            self.pawn_columns_list[not self.is_white_turn].remove(start_square % 10)
            if not self.is_pawn_promotion:
                self.pawn_columns_list[not self.is_white_turn].append(end_square % 10)
        if self.piece_captured[1] == 'p':
            self.pawn_columns_list[self.is_white_turn].remove(end_square % 10)

        # Update rook columns list
        if self.piece_moved[1] == 'R' and (start_square - end_square) % 10 > 0:
            self.rook_columns_list[not self.is_white_turn].remove(start_square % 10)
            self.rook_columns_list[not self.is_white_turn].append(end_square % 10)
        if self.piece_captured[1] == 'R':
            self.rook_columns_list[self.is_white_turn].remove(end_square % 10)

        # Castling logic, only if you have any castling rights left
        castle_piece_value_mid, castle_piece_value_end = 0, 0
        if any(self.castling_rights):
            if self.piece_moved[1] == 'K' and abs(end_square - start_square) == 2:

                # Update the variable "has castled", used in the evaluation function
                exec('self.white_has_castled = True' if self.is_white_turn else 'self.black_has_castled = True')

                # King side castle
                king_end_pos = 97 if self.is_white_turn else 27
                if end_square == king_end_pos:
                    # Update board, rooks and Zobrist
                    self.board[king_end_pos + 1] = '--'  # Remove R
                    self.board[king_end_pos - 1] = f'{self.piece_moved[0]}R'  # Place R

                    self.rook_columns_list[not self.is_white_turn].remove(8)
                    self.rook_columns_list[not self.is_white_turn].append(6)

                    self.zobrist_key ^= self.zobrist_board[king_end_pos + 1][f'{self.piece_moved[0]}R']  # Remove rook from its start square
                    self.zobrist_key ^= self.zobrist_board[king_end_pos - 1][f'{self.piece_moved[0]}R']  # Place rook on its new square

                    castle_piece_value_mid = (-s.piece_value_mid_game['R'][king_end_pos + 1] + s.piece_value_mid_game['R'][king_end_pos - 1]) * self.midgame
                    castle_piece_value_end = (-s.piece_value_end_game['R'][king_end_pos + 1] + s.piece_value_end_game['R'][king_end_pos - 1]) * self.endgame

                # Queen side castle
                king_end_pos = 93 if self.is_white_turn else 23
                if end_square == king_end_pos:
                    # Update board and Zobrist
                    self.board[king_end_pos - 2] = '--'  # Remove R
                    self.board[king_end_pos + 1] = f'{self.piece_moved[0]}R'  # Place R

                    self.rook_columns_list[not self.is_white_turn].remove(1)
                    self.rook_columns_list[not self.is_white_turn].append(4)

                    self.zobrist_key ^= self.zobrist_board[king_end_pos - 2][f'{self.piece_moved[0]}R']  # Remove rook from its start square
                    self.zobrist_key ^= self.zobrist_board[king_end_pos + 1][f'{self.piece_moved[0]}R']  # Place rook on its new square

                    castle_piece_value_mid = (-s.piece_value_mid_game['R'][king_end_pos - 2] + s.piece_value_mid_game['R'][king_end_pos + 1]) * self.midgame
                    castle_piece_value_end = (-s.piece_value_end_game['R'][king_end_pos - 2] + s.piece_value_end_game['R'][king_end_pos + 1]) * self.endgame

        # Enpassant move
        self.enpassant_made = False
        if end_square == self.enpassant_square and self.piece_moved[1] == 'p':
            self.enpassant_made = True

            # Remove captured pawn from board and Zobrist key
            d, color = (10, 'b') if self.is_white_turn else (-10, 'w')
            self.board[end_square + d] = '--'
            self.piece_captured = f'{color}p'
            self.zobrist_key ^= self.zobrist_board[end_square + d]['--']

            self.pawn_columns_list[self.is_white_turn].remove(end_square % 10)

            # Captured piece square is now capture square + d since piece is not on the actual capture square
            capture_square += d

        # Update enpassant possible square
        if abs(start_square - end_square) == 20 and self.piece_moved[1] == 'p':
            self.enpassant_square = (start_square + end_square) // 2  # Enpassant square is the mean of start_square and end_square for the pawn moving 2 squares
            self.enpassant_row = start_square % 10 - 1
            self.zobrist_key ^= self.zobrist_enpassant[self.enpassant_row]
        else:
            if self.enpassant_square:
                self.zobrist_key ^= self.zobrist_enpassant[self.enpassant_row]
            self.enpassant_square = None

        # Update gamestate phase (opening, mid, endgame) and piece dict
        captured_piece_value_mid = captured_piece_value_end = 0
        if self.piece_captured != '--':

            self.piece_dict[self.is_white_turn][self.piece_captured[1]] -= 1

            self.gamestate_phase -= s.piece_phase_calc[self.piece_captured[1]]
            self.midgame = max(0, (self.gamestate_phase - s.endgame_phase_limit) / (24 - s.endgame_phase_limit))
            self.endgame = min(1, (24 - self.gamestate_phase) / (24 - s.endgame_phase_limit))

            captured_piece_value_mid = (s.piece_value_base_mid_game[self.piece_captured[1]] + s.piece_value_mid_game[self.piece_captured[1]][capture_square]) * self.midgame
            captured_piece_value_end = (s.piece_value_base_end_game[self.piece_captured[1]] + s.piece_value_end_game[self.piece_captured[1]][capture_square]) * self.endgame

        if not self.is_pawn_promotion:
            moved_piece_value_change_mid = (-s.piece_value_mid_game[self.piece_moved[1]][from_square] + s.piece_value_mid_game[self.piece_moved[1]][to_square]) * self.midgame
            moved_piece_value_change_end = (-s.piece_value_end_game[self.piece_moved[1]][from_square] + s.piece_value_end_game[self.piece_moved[1]][to_square]) * self.endgame

        # Update the piece values based on the previous move
        color = 0 if self.is_white_turn else 1
        self.piece_values[color] += (moved_piece_value_change_mid + moved_piece_value_change_end) + (castle_piece_value_mid + castle_piece_value_end)
        self.piece_values[not color] -= (captured_piece_value_mid + captured_piece_value_end)

        # Update castling rights
        self.update_castling_rights(end_square)

        # Switch player turn after the move is made
        self.is_white_turn = not self.is_white_turn
        self.zobrist_key ^= self.zobrist_black_to_move

        # Update move log
        self.move_log.append([start_square, end_square, self.piece_moved, self.piece_captured, self.castling_rights[:],
                              self.enpassant_square, self.enpassant_made, self.zobrist_key, self.piece_values[:], self.is_pawn_promotion])

        # Update 50 move clock and check if it has reached 50 moves
        if self.piece_captured != '--' or self.piece_moved[1] == 'p':
            self.fifty_move_clock = 0
        else:
            self.fifty_move_clock += 0.5

        if self.fifty_move_clock >= 50:
            self.is_stale_mate = True
            self.kind_of_stalemate = 'Fifty-move rule'

        # Check for 3-fold repetition
        if self.is_three_fold():
            self.is_stale_mate = True
            self.kind_of_stalemate = 'Threefold repetition'

    def unmake_move(self):

        # Only possible to unmake move if a move has been played
        if len(self.move_log) > 1:

            # Switch player turn back
            self.is_white_turn = not self.is_white_turn

            # Reset any stalemates or checkmates
            self.is_check_mate, self.is_stale_mate = False, False

            # Info about latest move
            latest_move = self.move_log.pop()
            start_square, end_square = latest_move[0], latest_move[1]
            piece_moved, piece_captured = latest_move[2], latest_move[3]

            # Update board
            self.board[start_square] = piece_moved
            self.board[end_square] = piece_captured

            if piece_captured != '--':
                self.piece_dict[self.is_white_turn][piece_captured[1]] += 1

            # Update pawn columns list
            if piece_moved[1] == 'p' and (start_square - end_square) % 10 > 0:
                self.pawn_columns_list[not self.is_white_turn].append(start_square % 10)
                if not latest_move[9]:
                    self.pawn_columns_list[not self.is_white_turn].remove(end_square % 10)
            if piece_captured[1] == 'p':
                self.pawn_columns_list[self.is_white_turn].append(end_square % 10)

            # Update rook columns list
            if piece_moved[1] == 'R' and (start_square - end_square) % 10 > 0:
                self.rook_columns_list[not self.is_white_turn].append(start_square % 10)
                self.rook_columns_list[not self.is_white_turn].remove(end_square % 10)
            if piece_captured[1] == 'R':
                self.rook_columns_list[self.is_white_turn].append(end_square % 10)

            # Update promotion move
            if latest_move[9]:
                self.piece_dict[not self.is_white_turn]['p'] += 1
                self.piece_dict[not self.is_white_turn]['Q'] -= 1

            # Update the king position and the has_castled attribute
            if piece_moved == 'wK':
                self.white_king_location = start_square
            elif piece_moved == 'bK':
                self.black_king_location = start_square

            if piece_moved[1] == 'K' and abs(end_square - start_square) == 2:

                # Update has_castled variable
                if piece_moved == 'wK':
                    self.white_has_castled = False
                else:
                    self.black_has_castled = False

                # King side castle
                king_end_pos = 97 if self.is_white_turn else 27
                if end_square == king_end_pos:
                    # Update board
                    self.board[king_end_pos - 1] = '--'  # Remove R
                    self.board[king_end_pos + 1] = f'{piece_moved[0]}R'  # Place R

                    self.rook_columns_list[not self.is_white_turn].remove(6)
                    self.rook_columns_list[not self.is_white_turn].append(8)

                # Queen side castle
                king_end_pos = 93 if self.is_white_turn else 23
                if end_square == king_end_pos:
                    # Update board
                    self.board[king_end_pos + 1] = '--'  # Remove R
                    self.board[king_end_pos - 2] = f'{piece_moved[0]}R'  # Place R

                    self.rook_columns_list[not self.is_white_turn].remove(4)
                    self.rook_columns_list[not self.is_white_turn].append(1)

            # Undo enpassant move if such move was made
            if latest_move[6]:
                self.board[start_square] = piece_moved
                self.board[end_square] = '--'

                d, color = (10, 'b') if self.is_white_turn else (-10, 'w')
                self.board[end_square + d] = f'{color}p'

            # Update gamestate phase (opening, mid, endgame)
            if piece_captured != '--':
                self.gamestate_phase += s.piece_phase_calc[piece_captured[1]]

                self.midgame = max(0, (self.gamestate_phase - s.endgame_phase_limit) / (24 - s.endgame_phase_limit))
                self.endgame = min(1, (24 - self.gamestate_phase) / (24 - s.endgame_phase_limit))

            # Update things from the latest move
            self.piece_moved, self.piece_captured = self.move_log[-1][2], self.move_log[-1][3]
            self.castling_rights = self.move_log[-1][4][:]
            self.enpassant_square = self.move_log[-1][5]
            self.enpassant_made = self.move_log[-1][6]
            self.zobrist_key = self.move_log[-1][7]
            self.piece_values = self.move_log[-1][8][:]
            self.is_pawn_promotion = self.move_log[-1][9]

            # Update 50 move clock if it is not at 0
            self.fifty_move_clock = max(0, self.fifty_move_clock - 0.5)

    def make_nullmove(self):
        # Switch player turn
        self.is_white_turn = not self.is_white_turn

        latest_move = self.move_log[-1][:]
        latest_move[2], latest_move[3] = '--', '--'  # No piece is moved
        latest_move[5], latest_move[6] = None, False

        self.move_log.append(latest_move)

    def unmake_nullmove(self):

        # Switch player turn
        self.is_white_turn = not self.is_white_turn

        # Remove last move from move list
        self.move_log.pop()

# ---------------------------------------------------------------------------------------------------------
#                    Helper functions
# ---------------------------------------------------------------------------------------------------------

    def update_castling_rights(self, end_square):
        rights = (0, 1) if self.is_white_turn else (2, 3)

        # King moves
        if self.piece_moved[1] == 'K':
            self.castling_rights[rights[0]] = False
            self.castling_rights[rights[1]] = False
            self.zobrist_key ^= self.zobrist_castling[rights[0]]
            self.zobrist_key ^= self.zobrist_castling[rights[1]]

        # Rook moves
        rook_squares = [91, 98] if self.is_white_turn else [21, 28]
        if self.board[rook_squares[0]][1] != 'R':  # If left rook moves
            self.castling_rights[rights[1]] = False
            self.zobrist_key ^= self.zobrist_castling[rights[1]]
        elif self.board[rook_squares[1]][1] != 'R':  # If right rook moves
            self.castling_rights[rights[0]] = False
            self.zobrist_key ^= self.zobrist_castling[rights[0]]

        # Rook gets captured
        rook_logic = (91, 98) if not self.is_white_turn else (21, 28)
        rights = (0, 1) if not self.is_white_turn else (2, 3)
        if rook_logic[0] == end_square:  # If left rook is captured
            self.castling_rights[rights[1]] = False
            self.zobrist_key ^= self.zobrist_castling[rights[1]]
        elif rook_logic[1] == end_square:  # If right rook is captured
            self.castling_rights[rights[0]] = False
            self.zobrist_key ^= self.zobrist_castling[rights[0]]

    def is_three_fold(self):
        cnt = 0
        for pos in reversed(self.move_log[:-1]):
            # Break early if piece captured or pawn moved since they cannot be brought back
            if pos[2][1] == 'p' or pos[3] != '--':
                return False
            if self.zobrist_key == pos[7]:
                cnt += 1
            if cnt == 2:
                return True

# ---------------------------------------------------------------------------------------------------------
#                                  Init functions
# ---------------------------------------------------------------------------------------------------------

    def init_piece_values(self):
        piece_values = [0, 0]

        for square in self.board:
            color, piece = self.board[square][0], self.board[square][1]
            if color == 'w':
                piece_values[0] += s.piece_value_base_mid_game[piece] + s.piece_value_mid_game[piece][square]
            elif color == 'b':
                square_flipped = 120 - square + s.flip_board[square % 10]
                piece_values[1] += s.piece_value_base_mid_game[piece] + s.piece_value_mid_game[piece][square_flipped]

        return piece_values

    # Init the zobrist board at the start of a game
    def init_zobrist(self):
        zobrist_key = 0

        for square in range(120):
            if self.board[square] != 'FF':  # Only do for real board squares
                pieces = {'--': 0, 'wp': 0, 'wR': 0, 'wN': 0, 'wB': 0, 'wQ': 0, 'wK': 0, 'bp': 0, 'bR': 0, 'bN': 0, 'bB': 0, 'bQ': 0, 'bK': 0}
                for piece in pieces:
                    if piece == '--':
                        random_number = 0  # Keep the 0 value for empty squares
                    else:
                        random_number = random.getrandbits(64)  # Else, get a random 64bit number
                    pieces[piece] = random_number
                self.zobrist_board[square] = pieces  # The complete zobrist board with 12 states on each square (64 x 12 dict of dicts)

        # Create the zobrist key for the initial position for all squares
        for square in self.board:
            if self.board[square] != 'FF':
                piece_type = self.board[square]
                zobrist_key ^= self.zobrist_board[square][piece_type]

        # Enpassant, castling, black to move
        for col in range(8):
            self.zobrist_enpassant[col] = random.getrandbits(64)
            zobrist_key ^= self.zobrist_enpassant[col]
        for castle_side in range(4):
            self.zobrist_castling[castle_side] = random.getrandbits(64)
            zobrist_key ^= self.zobrist_castling[castle_side]
        self.zobrist_black_to_move = random.getrandbits(64)
        zobrist_key ^= self.zobrist_black_to_move

        return zobrist_key

# ---------------------------------------------------------------------------------------------------------
#                      Valid moves, pins/checks, and all possible moves
# ---------------------------------------------------------------------------------------------------------

    # Get all moves considering checks
    def get_valid_moves(self):

        moves = self.get_all_possible_moves()

        king_pos = self.white_king_location if self.is_white_turn else self.black_king_location

        # Find if is in check and all the possible pinned pieces
        self.is_in_check, self.pins, self.checks = self.check_for_pins_and_checks(king_pos)

        if self.is_in_check:
            if len(self.checks) == 1:  # Single check
                check = self.checks[0]
                checking_piece_pos = check[0]
                piece_checking = self.board[check[0]]  # Enemy piece that is causing the check
                valid_squares = []  # Valid squares the piece can move to
                if piece_checking[1] == 'N':  # Knight check, must capture knight or move king
                    valid_squares = [checking_piece_pos]
                else:
                    for i in range(1, 8):
                        valid_square = (king_pos + check[1] * i)  # Look in the direction of checking piece
                        valid_squares.append(valid_square)
                        if valid_square == checking_piece_pos:  # If finding the checking piece, look no further
                            break
                # Filter to only keep moves that are valid during check
                moves = list(filter(lambda x: x[0] == king_pos or x[1] in valid_squares or
                                    (self.board[x[0]][1] == 'p' and x[1] == self.enpassant_square and piece_checking[1] == 'p'), moves))
            else:  # Double check, only king can move
                moves = []
                self.get_king_moves(king_pos, moves, False)

        # Check for check mate and stale mate
        if len(moves) == 0:
            if self.is_in_check:
                self.is_check_mate = True
                if not self.is_white_turn:
                    self.white_wins = True
            else:
                self.is_stale_mate = True
                self.kind_of_stalemate = 'Stalemate'

        '''# Mobility counter
        if self.is_white_turn:
            self.white_mobility = len(moves)
        else:
            self.black_mobility = len(moves)'''

        return moves

    # Checks if there are any pinned pieces or current checks
    def check_for_pins_and_checks(self, square):
        pins, checks = [], []
        is_in_check = False

        enemy_color, friendly_color = ('b', 'w') if self.is_white_turn else ('w', 'b')

        # Check out from all directions from the king
        for i in range(8):
            d = s.directions[i]
            possible_pin = False
            for j in range(8):  # Check the entire row/column in that direction
                end_square = square + d*j
                piece_color, piece_type = self.board[end_square][0], self.board[end_square][1]
                if piece_type != 'F':
                    if piece_color == friendly_color and piece_type != 'K':
                        if not possible_pin:  # First own piece, possible pin
                            possible_pin = (end_square, d)
                        else:  # 2nd friendly piece, no pin
                            break
                    elif piece_color == enemy_color:
                        # 5 different cases:
                        # 1. Orthogonally from king and piece is a rook
                        # 2. Diagonally from king and piece is a bishop
                        # 3. 1 square away diagonally from king and piece is a pawn
                        # 4. Any direction and piece is a queen
                        # 5. Any direction 1 square away and piece is a king
                        if (0 <= i <= 3 and piece_type == 'R') or \
                                (4 <= i <= 7 and piece_type == 'B') or \
                                (j == 1 and piece_type == 'p' and ((enemy_color == 'w' and 6 <= i <= 7) or (enemy_color == 'b' and 4 <= i <= 5))) or \
                                (piece_type == 'Q') or \
                                (j == 1 and piece_type == 'K'):
                            if not possible_pin:  # No friendly piece is blocking -> is check
                                is_in_check = True
                                checks.append((end_square, d))
                                break
                            else:  # Friendly piece is blocking -> pinned piece
                                pins.append(possible_pin)
                                break
                        else:  # Enemy piece that is not applying check or pin
                            break
                else:  # i, j is off board
                    break

        # Check for knight checks
        for d in s.knight_moves:
            end_square = square + d
            end_piece = self.board[end_square]
            if end_piece != 'FF':
                if end_piece[0] == enemy_color and end_piece[1] == 'N':  # Enemy knight attacking king
                    is_in_check = True
                    checks.append((end_square, d))

        return is_in_check, pins, checks

    # Get all moves without considering checks
    def get_all_possible_moves(self):
        moves = []

        # Loop through all squares on the board
        for square in s.real_board_squares:
            if self.board[square][0] in 'wb':  # If it is a piece on the square

                turn = self.board[square][0]
                if (turn == 'w' and self.is_white_turn) or (turn == 'b' and not self.is_white_turn):

                    # Get corresponding moves for each piece
                    self.move_functions[self.board[square][1]](square, moves, False)

        # Find if there is a draw by insufficient material (https://support.chess.com/article/128-what-does-insufficient-mating-material-mean)
        if self.piece_dict[0]['p'] == self.piece_dict[1]['p'] == 0:
            if self.piece_dict[0]['Q'] == self.piece_dict[0]['R'] == self.piece_dict[1]['Q'] == self.piece_dict[1]['R'] == 0:
                if self.piece_dict[0]['N'] == self.piece_dict[0]['B'] == 0 and self.piece_dict[1]['B'] < 2 and (self.piece_dict[1]['B'] + self.piece_dict[1]['N']) < 2 or \
                        self.piece_dict[1]['N'] == self.piece_dict[1]['B'] == 0 and self.piece_dict[0]['B'] < 2 and (self.piece_dict[0]['B'] + self.piece_dict[0]['N']) < 2 or \
                        self.piece_dict[0]['N'] == 0 and self.piece_dict[0]['B'] == 1 and self.piece_dict[1]['N'] == 0 and self.piece_dict[1]['B'] == 1 or \
                        self.piece_dict[0]['N'] == 1 and self.piece_dict[0]['B'] == 0 and self.piece_dict[1]['N'] == 0 and self.piece_dict[1]['B'] == 1 or \
                        self.piece_dict[0]['N'] == 0 and self.piece_dict[0]['B'] == 1 and self.piece_dict[1]['N'] == 1 and self.piece_dict[1]['B'] == 0 or \
                        self.piece_dict[0]['N'] >= 0 and self.piece_dict[0]['B'] == 0 and self.piece_dict[1]['N'] >= 0 and self.piece_dict[1]['B'] == 0:

                    self.is_stale_mate = True
                    self.kind_of_stalemate = 'Insufficient material'

        return moves

# ---------------------------------------------------------------------------------------------------------
#                                Get piece moves
# ---------------------------------------------------------------------------------------------------------

    def get_pawn_moves(self, square, moves, piece_pinned):
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == square:
                piece_pinned = True
                pin_direction = (self.pins[i][1])
                self.pins.remove(self.pins[i])
                break

        # Parameters depending on if white or black turn
        move_dir, start_row, enemy_color = (-10, s.start_row_white, 'b') if self.is_white_turn else (10, s.start_row_black, 'w')

        # 1 square move
        if self.board[square + move_dir] == '--':
            if not piece_pinned or pin_direction in (move_dir, -move_dir):
                moves.append((square, square + move_dir))
                # 2 square move
                if square in start_row and self.board[square + 2*move_dir] == '--':
                    moves.append((square, square + 2*move_dir))

        # Capture and enpassant to the left
        if self.board[square + move_dir - 1][0] == enemy_color or square + move_dir - 1 == self.enpassant_square:
            if not piece_pinned or pin_direction == move_dir - 1:
                moves.append((square, square + move_dir - 1))

        # Capture and enpassant to the right
        if self.board[square + move_dir + 1][0] == enemy_color or square + move_dir + 1 == self.enpassant_square:
            if not piece_pinned or pin_direction == move_dir + 1:
                moves.append((square, square + move_dir + 1))

    def get_knight_moves(self, square, moves, piece_pinned):

        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == square:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        friendly_color = 'w' if self.is_white_turn else 'b'
        for d in s.knight_moves:
            end_square = square + d
            if self.board[end_square] != 'FF' and self.board[end_square][0] != friendly_color and not piece_pinned:
                moves.append((square, end_square))

    def get_bishop_moves(self, square, moves, piece_pinned):
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == square:
                piece_pinned = True
                pin_direction = (self.pins[i][1])
                self.pins.remove(self.pins[i])
                break

        enemy_color = 'b' if self.is_white_turn else 'w'
        for d in s.directions[4:8]:
            for i in range(1, 8):
                end_square = square + d * i
                end_piece = self.board[end_square][0]
                if end_piece in f'{enemy_color}-':
                    if not piece_pinned or pin_direction in (-d, d):  # Able to move towards and away from pin
                        moves.append((square, end_square))
                        if end_piece == enemy_color:
                            break
                else:
                    break

    def get_rook_moves(self, square, moves, piece_pinned):
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == square:
                piece_pinned = True
                pin_direction = (self.pins[i][1])
                self.pins.remove(self.pins[i])
                break

        enemy_color = 'b' if self.is_white_turn else 'w'
        for d in s.directions[0:4]:
            for i in range(1, 8):
                end_square = square + d * i
                end_piece = self.board[end_square][0]
                if end_piece in f'{enemy_color}-':
                    if not piece_pinned or pin_direction in (d, -d):  # Able to move towards and away from pin
                        moves.append((square, end_square))
                        if end_piece == enemy_color:
                            break
                else:
                    break

    def get_queen_moves(self, square, moves, piece_pinned):
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == square:
                piece_pinned = True
                pin_direction = (self.pins[i][1])
                self.pins.remove(self.pins[i])
                break

        enemy_color = 'b' if self.is_white_turn else 'w'
        for d in s.directions:
            for i in range(1, 8):
                end_square = square + d * i
                end_piece = self.board[end_square][0]
                if end_piece in f'{enemy_color}-':
                    if not piece_pinned or pin_direction in (-d, d):  # Able to move towards and away from pin
                        moves.append((square, end_square))
                        if end_piece == enemy_color:
                            break
                else:
                    break

    def get_king_moves(self, square, moves, _):
        friendly_color = 'w' if self.is_white_turn else 'b'
        for i in range(8):
            end_square = square + s.directions[i]
            end_piece = self.board[end_square]
            if end_piece != 'FF' and end_piece[0] != friendly_color:

                # Temporarily replace piece from the square and check all surrounding squares to see if they are attacked or not
                self.board[end_square] = '--'
                is_in_check = self.check_for_checks(end_square)
                self.board[end_square] = end_piece

                if not is_in_check:
                    moves.append((square, end_square))

        # Castling:
        # Can't castle if in check, if square between K or R is under attack, or if castling rights are broken (K or R is not in their original places)
        if not self.is_in_check:
            castling_rights = (0, 1) if self.is_white_turn else (2, 3)

            # Castle King side
            if self.castling_rights[castling_rights[0]] and all(x == '--' for x in (self.board[square + 1], self.board[square + 2])):

                # Check if squares are in check or not
                is_in_check_1 = self.check_for_checks(square + 1)
                is_in_check_2 = self.check_for_checks(square + 2)

                if not (is_in_check_1 or is_in_check_2):
                    moves.append((square, square + 2))

            # Castle Queen side
            if self.castling_rights[castling_rights[1]] and all(x == '--' for x in (self.board[square - 1], self.board[square - 2], self.board[square - 3])):

                # Check if squares are in check or not, king doesn't pass the knight square on queenside castle so no use in checking that square
                is_in_check_1 = self.check_for_checks(square - 1)
                is_in_check_2 = self.check_for_checks(square - 2)

                if not (is_in_check_1 or is_in_check_2):
                    moves.append((square, square - 2))

# ---------------------------------------------------------------------------------------------------------
#                        Special check for check function for speed up
# ---------------------------------------------------------------------------------------------------------

    # Checks if there are any pinned pieces or current checks
    def check_for_checks(self, square):
        is_in_check = False

        enemy_color, friendly_color = ('b', 'w') if self.is_white_turn else ('w', 'b')

        # Check out from all directions from the king
        for i in range(8):
            d = s.directions[i]
            possible_pin = False
            for j in range(8):  # Check the entire row/column in that direction
                end_square = square + d*j
                piece_color, piece_type = self.board[end_square][0], self.board[end_square][1]
                if piece_type != 'F':
                    if piece_color == friendly_color and piece_type != 'K':
                        if not possible_pin:  # First own piece, possible pin
                            possible_pin = True
                        else:  # 2nd friendly piece, no pin
                            break
                    elif piece_color == enemy_color:
                        # 5 different cases:
                        # 1. Orthogonally from king and piece is a rook
                        # 2. Diagonally from king and piece is a bishop
                        # 3. 1 square away diagonally from king and piece is a pawn
                        # 4. Any direction and piece is a queen
                        # 5. Any direction 1 square away and piece is a king
                        if (0 <= i <= 3 and piece_type == 'R') or \
                                (4 <= i <= 7 and piece_type == 'B') or \
                                (j == 1 and piece_type == 'p' and ((enemy_color == 'w' and 6 <= i <= 7) or (enemy_color == 'b' and 4 <= i <= 5))) or \
                                (piece_type == 'Q') or \
                                (j == 1 and piece_type == 'K'):
                            if not possible_pin:  # No friendly piece is blocking -> is check
                                is_in_check = True
                                break
                            else:  # Friendly piece is blocking -> pinned piece
                                break
                        else:  # Enemy piece that is not applying check or pin
                            break
                else:  # i, j is off board
                    break

        # Check for knight checks
        for d in s.knight_moves:
            end_square = square + d
            end_piece = self.board[end_square]
            if end_piece != 'FF':
                if end_piece[0] == enemy_color and end_piece[1] == 'N':  # Enemy knight attacking king
                    is_in_check = True

        return is_in_check
