# --------------------------------------------------------------------------------
#                 Board handling piece move functionality
# --------------------------------------------------------------------------------

import settings as s
import fen_handling as fh

import random


class GameState:

    def __init__(self, start_fen, game_mode, is_ai_white, max_search_depth):

        # Init the board and relevant variables from an input fen string
        self.start_fen = start_fen
        self.board, self.castling_rights, self.enpassant_square, self.fifty_move_clock, self.is_white_turn = fh.run_fen_to_board(self.start_fen)

        self.enpassant_col = self.enpassant_square % 10 - 1 if self.enpassant_square else None

        self.play_with_opening_book = s.play_with_opening_book
        self.game_mode = game_mode
        self.is_ai_white = is_ai_white
        self.max_search_depth = max_search_depth

        # Keep track of where pawns are located on the board for evaluation
        self.pawn_columns_list, self.rook_columns_list = [[], []], [[], []]
        self.init_piece_columns()

        # Keep track of number of pieces on the board
        self.piece_dict = [{'p': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0, 'K': 0}, {'p': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0, 'K': 0}]  # W, B
        self.init_piece_dict()

        # Gamestate phase (midgame or endgame)
        self.midgame, self.endgame = 0, 0
        self.gamestate_phase = 0
        self.init_gamestate_phase()

        # Piece values (base and square dependent)
        self.piece_values = [0, 0]
        self.init_piece_values()

        # Init king positions
        self.white_has_castled = self.black_has_castled = False
        self.white_king_location, self.black_king_location = 0, 0
        self.init_king_positions()

        # King distance and attack squares
        self.kings_distance = 0
        self.king_attack_squares = [[], []]
        self.update_king_attack_squares_and_dist()

        # Get possible moves for a certain piece type
        self.possible_moves = []
        self.move_functions = {'p': self.get_pawn_moves,
                               'N': self.get_knight_moves,
                               'B': self.get_bishop_moves,
                               'R': self.get_rook_moves,
                               'Q': self.get_queen_moves,
                               'K': self.get_king_moves}

        # Check, stalemate and checkmate variables
        self.white_wins = False
        self.move_counter = 0.5
        self.pins, self.checks = [], []
        self.is_in_check = False
        self.is_check_mate = self.is_stale_mate = False
        self.kind_of_stalemate = ''

        # Move related variables
        self.piece_moved = self.piece_captured = '--'
        self.center_attacks_white = self.center_attacks_black = 0
        self.king_attacks_white = self.king_attacks_black = 0
        self.mobility = [0, 0]

        # Init Zobrist board (https://www.youtube.com/watch?v=gyLCFfrLGIM)
        self.zobrist_board = {}
        self.zobrist_pieces = [0] * 64  # One for each square
        self.zobrist_enpassant = [0] * 8  # One for each column
        self.zobrist_castling = {'K': 0, 'Q': 0, 'k': 0, 'q': 0}  # W king side, W queen side, B king side, B queen side
        self.zobrist_black_to_move = 0  # Turn

        self.zobrist_key = self.init_zobrist()

        # Init the move log. [move, piece moved, piece_captured, castling rights, enpassant square, zobrist key, piece_values]
        self.move_log = [[(0, 0, 0, 0), '--', '--', self.castling_rights, self.enpassant_square, self.zobrist_key, self.piece_values[:]]]

# ---------------------------------------------------------------------------------------------------------
#             Make and unmake move functions, Zobrist key
# ---------------------------------------------------------------------------------------------------------

    def make_move(self, move):

        start_square, end_square, move_type = move[0], move[1], move[2]

        # Square dependent on white or black
        from_square, to_square = (start_square, end_square) if self.is_white_turn else (120 - start_square + s.flip_board[start_square % 10], 120 - end_square + s.flip_board[end_square % 10])

        # Init values
        castle_piece_value_mid, castle_piece_value_end = 0, 0
        captured_piece_value_mid, captured_piece_value_end = 0, 0
        capture_square = 0

        if self.enpassant_square:
            self.zobrist_key ^= self.zobrist_enpassant[self.enpassant_col]
        self.enpassant_square = None

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

        # Update the king position and has castled attributes
        if self.piece_moved == 'wK':
            self.white_king_location = end_square
            self.update_king_attack_squares_and_dist()
            if move_type in 'ckcq':
                self.white_has_castled = True
        elif self.piece_moved == 'bK':
            self.black_king_location = end_square
            self.update_king_attack_squares_and_dist()
            if move_type in 'ckcq':
                self.black_has_castled = True

        # Update pawn columns list
        elif self.piece_moved[1] == 'p' and (start_square - end_square) % 10 > 0:
            self.pawn_columns_list[not self.is_white_turn].remove(start_square % 10)
            self.pawn_columns_list[not self.is_white_turn].append(end_square % 10)

        # Update rook columns list
        elif self.piece_moved[1] == 'R' and (start_square - end_square) % 10 > 0:
            self.rook_columns_list[not self.is_white_turn].remove(start_square % 10)
            self.rook_columns_list[not self.is_white_turn].append(end_square % 10)

        # Non "normal" moves
        if move_type != 'no':

            # Pawn promotion
            if move_type in 'pQpRpBpN':
                self.board[end_square] = f'{self.piece_moved[0]}{move_type[1]}'

                self.piece_dict[not self.is_white_turn]['p'] -= 1
                self.piece_dict[not self.is_white_turn][f'{move_type[1]}'] += 1

                self.zobrist_key ^= self.zobrist_board[end_square][self.piece_moved]  # Remove the pawn from end_square again since it now changed
                self.zobrist_key ^= self.zobrist_board[end_square][f'{self.piece_moved[0]}{move_type[1]}']  # Place the promoted piece there instead

                # Capture to promotion or normal move?
                if (start_square - end_square) % 10 > 0:
                    self.pawn_columns_list[not self.is_white_turn].remove(end_square % 10)
                else:
                    self.pawn_columns_list[not self.is_white_turn].remove(start_square % 10)

                # If choosing a rook, add it to rook columns list
                if move_type == 'pR':
                    self.rook_columns_list[not self.is_white_turn].append(end_square % 10)

                # Update piece value change
                moved_piece_value_change_mid = (-(s.piece_value_base_mid_game['p'] + s.piece_value_mid_game['p'][from_square]) +
                                                 (s.piece_value_base_mid_game[f'{move_type[1]}'] + s.piece_value_mid_game[f'{move_type[1]}'][to_square])) * self.midgame
                moved_piece_value_change_end = (-(s.piece_value_base_end_game['p'] + s.piece_value_end_game['p'][from_square]) +
                                                 (s.piece_value_base_end_game[f'{move_type[1]}'] + s.piece_value_end_game[f'{move_type[1]}'][to_square])) * self.endgame

            # Castling king side
            elif move_type == 'ck':
                king_end_pos = 97 if self.is_white_turn else 27

                # Update board, rooks and Zobrist
                self.board[king_end_pos + 1] = '--'  # Remove R
                self.board[king_end_pos - 1] = f'{self.piece_moved[0]}R'  # Place R

                self.rook_columns_list[not self.is_white_turn].remove(8)
                self.rook_columns_list[not self.is_white_turn].append(6)

                self.zobrist_key ^= self.zobrist_board[king_end_pos + 1][f'{self.piece_moved[0]}R']  # Remove rook from its start square
                self.zobrist_key ^= self.zobrist_board[king_end_pos - 1][f'{self.piece_moved[0]}R']  # Place rook on its new square

                castle_piece_value_mid = (-s.piece_value_mid_game['R'][98] + s.piece_value_mid_game['R'][96]) * self.midgame
                castle_piece_value_end = (-s.piece_value_end_game['R'][98] + s.piece_value_end_game['R'][96]) * self.endgame

            # Castling queen side
            elif move_type == 'cq':
                king_end_pos = 93 if self.is_white_turn else 23

                # Update board and Zobrist
                self.board[king_end_pos - 2] = '--'  # Remove R
                self.board[king_end_pos + 1] = f'{self.piece_moved[0]}R'  # Place R

                self.rook_columns_list[not self.is_white_turn].remove(1)
                self.rook_columns_list[not self.is_white_turn].append(4)

                self.zobrist_key ^= self.zobrist_board[king_end_pos - 2][f'{self.piece_moved[0]}R']  # Remove rook from its start square
                self.zobrist_key ^= self.zobrist_board[king_end_pos + 1][f'{self.piece_moved[0]}R']  # Place rook on its new square

                castle_piece_value_mid = (-s.piece_value_mid_game['R'][91] + s.piece_value_mid_game['R'][94]) * self.midgame
                castle_piece_value_end = (-s.piece_value_end_game['R'][91] + s.piece_value_end_game['R'][94]) * self.endgame

            # Enpassant
            elif move_type == 'ep':

                # Remove captured pawn from board and Zobrist key
                d, color = (10, 'b') if self.is_white_turn else (-10, 'w')
                self.board[end_square + d] = '--'
                self.piece_captured = f'{color}p'
                self.zobrist_key ^= self.zobrist_board[end_square + d][f'{color}p']

                # Captured piece square is now capture square - d since piece is not on the actual capture square
                capture_square = -10

            # Two square pawn move, update enpassant possible square
            elif move_type == 'ts':
                self.enpassant_square = (start_square + end_square) // 2  # Enpassant square is the mean of start_square and end_square for the pawn moving 2 squares
                self.enpassant_col = start_square % 10 - 1
                self.zobrist_key ^= self.zobrist_enpassant[self.enpassant_col]

        # Capture moves
        if self.piece_captured != '--':

            self.piece_dict[self.is_white_turn][self.piece_captured[1]] -= 1

            self.gamestate_phase -= s.piece_phase_calc[self.piece_captured[1]]
            self.midgame = max(0, (self.gamestate_phase - s.endgame_phase_limit) / (24 - s.endgame_phase_limit))
            self.endgame = min(1, (24 - self.gamestate_phase) / (24 - s.endgame_phase_limit))

            capture_square += end_square if not self.is_white_turn else 120 - end_square + s.flip_board[end_square % 10]

            captured_piece_value_mid = (s.piece_value_base_mid_game[self.piece_captured[1]] + s.piece_value_mid_game[self.piece_captured[1]][capture_square]) * self.midgame
            captured_piece_value_end = (s.piece_value_base_end_game[self.piece_captured[1]] + s.piece_value_end_game[self.piece_captured[1]][capture_square]) * self.endgame

            # Update pawn and rook columns lists
            if self.piece_captured[1] == 'p':
                self.pawn_columns_list[self.is_white_turn].remove(end_square % 10)
            elif self.piece_captured[1] == 'R':
                self.rook_columns_list[self.is_white_turn].remove(end_square % 10)

        if move_type not in 'pQpRpBpN':
            moved_piece_value_change_mid = (-s.piece_value_mid_game[self.piece_moved[1]][from_square] + s.piece_value_mid_game[self.piece_moved[1]][to_square]) * self.midgame
            moved_piece_value_change_end = (-s.piece_value_end_game[self.piece_moved[1]][from_square] + s.piece_value_end_game[self.piece_moved[1]][to_square]) * self.endgame

        # Update the piece values based on the previous move
        color = 0 if self.is_white_turn else 1
        self.piece_values[color] += (moved_piece_value_change_mid + moved_piece_value_change_end) + (castle_piece_value_mid + castle_piece_value_end)
        self.piece_values[not color] -= (captured_piece_value_mid + captured_piece_value_end)

        # Update castling rights if there are any left
        if self.castling_rights:
            self.update_castling_rights(end_square)

        # Switch player turn after the move is made
        self.is_white_turn = not self.is_white_turn
        self.zobrist_key ^= self.zobrist_black_to_move

        # Update move log
        self.move_log.append([move, self.piece_moved, self.piece_captured, self.castling_rights,
                              self.enpassant_square, self.zobrist_key, self.piece_values[:]])

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

        # Switch player turn back
        self.is_white_turn = not self.is_white_turn

        # Reset any stalemates or checkmates
        self.is_check_mate, self.is_stale_mate = False, False

        # Info about latest move
        latest_move = self.move_log.pop()
        start_square, end_square = latest_move[0][0], latest_move[0][1]
        move_type = latest_move[0][2]
        piece_moved, piece_captured = latest_move[1], latest_move[2]

        # Update board
        self.board[start_square] = piece_moved
        self.board[end_square] = piece_captured

        # Captures
        if piece_captured != '--':

            # Update piece dict
            self.piece_dict[self.is_white_turn][piece_captured[1]] += 1

            # Update gamestate phase (opening, mid, endgame)
            self.gamestate_phase += s.piece_phase_calc[piece_captured[1]]

            self.midgame = max(0, (self.gamestate_phase - s.endgame_phase_limit) / (24 - s.endgame_phase_limit))
            self.endgame = min(1, (24 - self.gamestate_phase) / (24 - s.endgame_phase_limit))

            # Update pawn and rook columns lists
            if piece_captured[1] == 'p':
                self.pawn_columns_list[self.is_white_turn].append(end_square % 10)
            elif piece_captured[1] == 'R':
                self.rook_columns_list[self.is_white_turn].append(end_square % 10)

        # Update pawn columns list
        if piece_moved[1] == 'p' and (start_square - end_square) % 10 > 0:
            self.pawn_columns_list[not self.is_white_turn].append(start_square % 10)
            if move_type not in 'pQpRpBpN':
                self.pawn_columns_list[not self.is_white_turn].remove(end_square % 10)

        # Update rook columns list
        elif piece_moved[1] == 'R' and (start_square - end_square) % 10 > 0:
            self.rook_columns_list[not self.is_white_turn].append(start_square % 10)
            self.rook_columns_list[not self.is_white_turn].remove(end_square % 10)

        # Update the king position
        elif piece_moved == 'wK':
            self.white_king_location = start_square
            self.update_king_attack_squares_and_dist()
            if move_type in 'ckcq':
                self.white_has_castled = False
        elif piece_moved == 'bK':
            self.black_king_location = start_square
            self.update_king_attack_squares_and_dist()
            if move_type in 'ckcq':
                self.black_has_castled = False

        # Update promotion move
        if move_type != 'no':
            if move_type in 'pQpRpBpN':
                self.piece_dict[not self.is_white_turn]['p'] += 1
                self.piece_dict[not self.is_white_turn][f'{move_type[1]}'] -= 1

                if (start_square - end_square) % 10 == 0:
                    self.pawn_columns_list[not self.is_white_turn].append(start_square % 10)

                if move_type == 'pR':
                    self.rook_columns_list[not self.is_white_turn].remove(end_square % 10)

            elif move_type == 'ck':

                # Update board
                king_end_pos = 97 if self.is_white_turn else 27
                self.board[king_end_pos - 1] = '--'  # Remove R
                self.board[king_end_pos + 1] = f'{piece_moved[0]}R'  # Place R

                self.rook_columns_list[not self.is_white_turn].remove(6)
                self.rook_columns_list[not self.is_white_turn].append(8)

            elif move_type == 'cq':

                # Update board
                king_end_pos = 93 if self.is_white_turn else 23
                self.board[king_end_pos + 1] = '--'  # Remove R
                self.board[king_end_pos - 2] = f'{piece_moved[0]}R'  # Place R

                self.rook_columns_list[not self.is_white_turn].remove(4)
                self.rook_columns_list[not self.is_white_turn].append(1)

            elif move_type == 'ep':
                self.board[start_square] = piece_moved
                self.board[end_square] = '--'

                d, color = (10, 'b') if self.is_white_turn else (-10, 'w')
                self.board[end_square + d] = f'{color}p'

        # Update things from the latest move [move, piece moved, piece_captured, castling rights, enpassant square, enpassant made, zobrist key, piece_values]
        self.piece_moved, self.piece_captured = self.move_log[-1][1], self.move_log[-1][2]
        self.castling_rights = self.move_log[-1][3]
        self.enpassant_square = self.move_log[-1][4]
        self.zobrist_key = self.move_log[-1][5]
        self.piece_values = self.move_log[-1][6][:]

        # Update 50 move clock if it is not at 0
        self.fifty_move_clock = max(0, self.fifty_move_clock - 0.5)

    def make_nullmove(self):

        # Enpassant square
        if self.enpassant_square:
            self.zobrist_key ^= self.zobrist_enpassant[self.enpassant_col]
        self.enpassant_square = None

        # Update piece_moved and piece_captured
        self.piece_moved = '--'
        self.piece_captured = '--'

        # Switch player turn after the move is made
        self.is_white_turn = not self.is_white_turn
        self.zobrist_key ^= self.zobrist_black_to_move

        # Update move log
        self.move_log.append([(0, 0, 'no', 0), self.piece_moved, self.piece_captured, self.castling_rights,
                              self.enpassant_square, self.zobrist_key, self.piece_values[:]])

    def unmake_nullmove(self):

        self.move_log.pop()

        # Switch player turn after the move is made
        self.is_white_turn = not self.is_white_turn

        # Update from previous moves
        self.piece_moved, self.piece_captured = self.move_log[-1][1], self.move_log[-1][2]
        self.enpassant_square = self.move_log[-1][4]
        self.zobrist_key = self.move_log[-1][5]

# ---------------------------------------------------------------------------------------------------------
#                       Helper functions
# ---------------------------------------------------------------------------------------------------------

    def update_castling_rights(self, end_square):

        # King moves
        if self.piece_moved[1] == 'K':

            # Only update Zobrist key if castling rights are changing
            param = ('K', 'Q') if self.is_white_turn else ('k', 'q')
            if param[0] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[0]]
                self.castling_rights = self.castling_rights.replace(param[0], '')
            if param[1] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[1]]
                self.castling_rights = self.castling_rights.replace(param[1], '')

        # If left rook moves
        param = (91, 'Q') if self.is_white_turn else (21, 'q')
        if self.board[param[0]][1] != 'R':
            if param[1] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[1]]
                self.castling_rights = self.castling_rights.replace(param[1], '')

        # If right rook moves
        param = (98, 'K') if self.is_white_turn else (28, 'k')
        if self.board[param[0]][1] != 'R':
            if param[1] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[1]]
                self.castling_rights = self.castling_rights.replace(param[1], '')

        # If left rook gets captured
        param = (21, 'q') if self.is_white_turn else (91, 'Q')
        if param[0] == end_square:
            if param[1] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[1]]
            self.castling_rights = self.castling_rights.replace(param[1], '')

        # If right rook gets captured
        param = (28, 'k') if self.is_white_turn else (98, 'K')
        if param[0] == end_square:
            if param[1] in self.castling_rights:
                self.zobrist_key ^= self.zobrist_castling[param[1]]
            self.castling_rights = self.castling_rights.replace(param[1], '')

    def is_three_fold(self):
        cnt = 0
        for pos in reversed(self.move_log[1:]):
            if self.zobrist_key == pos[5]:
                cnt += 1
            if cnt == 3:
                return True
            # Break early if piece captured or pawn moved since they cannot be brought back
            if pos[1][1] == 'p' or pos[2] != '--':
                return False

    def update_king_attack_squares_and_dist(self):
        self.king_attack_squares[0] = s.king_attack_squares[self.white_king_location]
        self.king_attack_squares[1] = s.king_attack_squares[self.black_king_location]

        horizontal_distance = abs(self.white_king_location % 10 - self.black_king_location % 10)
        vertical_distance = abs(self.white_king_location // 10 - self.black_king_location // 10)
        self.kings_distance = horizontal_distance + vertical_distance

# ---------------------------------------------------------------------------------------------------------
#                                  Init and update functions
# ---------------------------------------------------------------------------------------------------------

    def init_piece_values(self):
        for square in self.board:
            color, piece = self.board[square][0], self.board[square][1]
            if color == 'w':
                self.piece_values[0] += s.piece_value_base_mid_game[piece] + s.piece_value_mid_game[piece][square]
            elif color == 'b':
                square_flipped = 120 - square + s.flip_board[square % 10]
                self.piece_values[1] += s.piece_value_base_mid_game[piece] + s.piece_value_mid_game[piece][square_flipped]

    def init_piece_dict(self):
        for square in self.board:
            piece_type, color = self.board[square][1], self.board[square][0]
            if piece_type in 'pNBRQK':
                if color == 'w':
                    self.piece_dict[0][piece_type] += 1
                elif color == 'b':
                    self.piece_dict[1][piece_type] += 1

    def init_piece_columns(self):
        for square in self.board:
            piece_type, color = self.board[square][1], self.board[square][0]
            if piece_type == 'R':
                if color == 'w':
                    self.rook_columns_list[0].append(square % 10)
                elif color == 'b':
                    self.rook_columns_list[1].append(square % 10)
            if piece_type == 'p':
                if color == 'w':
                    self.pawn_columns_list[0].append(square % 10)
                elif color == 'b':
                    self.pawn_columns_list[1].append(square % 10)

    def init_gamestate_phase(self):
        for square in self.board:
            if self.board[square] not in ['--', 'FF']:
                piece_type = self.board[square][1]
                self.gamestate_phase += s.piece_phase_calc[piece_type]

        # Endgame is 100% when gamestate is below s.endgame_phase_limit, else interpolate between the two phases
        self.midgame = max(0, (self.gamestate_phase - s.endgame_phase_limit) / (24 - s.endgame_phase_limit))
        self.endgame = min(1, (24 - self.gamestate_phase) / (24 - s.endgame_phase_limit))

    def init_king_positions(self):
        for square in self.board:
            piece_type, color = self.board[square][1], self.board[square][0]
            if piece_type == 'K':
                if color == 'w':
                    self.white_king_location = square
                else:
                    self.black_king_location = square

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
        for castle_side in 'KQkq':
            self.zobrist_castling[castle_side] = random.getrandbits(64)
            zobrist_key ^= self.zobrist_castling[castle_side]
        self.zobrist_black_to_move = random.getrandbits(64)
        zobrist_key ^= self.zobrist_black_to_move

        return zobrist_key

# ---------------------------------------------------------------------------------------------------------
#                              Get valid moves
# ---------------------------------------------------------------------------------------------------------

    # Get all moves considering checks and pins
    def get_valid_moves(self):

        # Initiate piece attacking variables
        if self.is_white_turn:
            self.center_attacks_white = 0
            self.king_attacks_white = 0
        else:
            self.center_attacks_black = 0
            self.king_attacks_black = 0

        king_pos = self.white_king_location if self.is_white_turn else self.black_king_location

        # Find if is in check and all the possible pinned pieces
        self.is_in_check, self.pins, self.checks = self.check_for_pins_and_checks(king_pos)

        if self.is_in_check:
            if len(self.checks) == 1:  # Single check
                moves = self.get_all_possible_moves()
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
        else:
            moves = self.get_all_possible_moves()

        # Check for check mate and stale mate
        if len(moves) == 0:
            if self.is_in_check:
                self.is_check_mate = True
                if not self.is_white_turn:
                    self.white_wins = True
            else:
                self.is_stale_mate = True
                self.kind_of_stalemate = 'Stalemate'

        self.possible_moves = moves

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
                        self.piece_dict[0]['N'] <= 2 and self.piece_dict[0]['B'] == 0 and self.piece_dict[1]['N'] <= 2 and self.piece_dict[1]['B'] == 0 or \
                        self.piece_dict[0]['N'] == 1 and self.piece_dict[0]['B'] == 0 and self.piece_dict[1]['N'] == 0 and self.piece_dict[1]['B'] == 1 or \
                        self.piece_dict[0]['N'] == 0 and self.piece_dict[0]['B'] == 1 and self.piece_dict[1]['N'] == 1 and self.piece_dict[1]['B'] == 0:

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
        move_dir, start_row, enemy_color, end_row, friendly_color = \
            (-10, s.start_row_white, 'b', s.end_row_white, 'w') if self.is_white_turn else (10, s.start_row_black, 'w', s.end_row_black, 'b')

        '''# Add square to attacking squares king and center
        if self.is_white_turn:
            if any((square - 9, square - 11)) in self.king_attack_squares[1]:
                self.king_attacks_white += s.piece_king_attack['p']
            self.center_attacks_white += s.center_attacks[square - 9] * s.piece_center_attack['p']
            self.center_attacks_white += s.center_attacks[square - 11] * s.piece_center_attack['p']
        else:
            if any((square + 9, square + 11)) in self.king_attack_squares[0]:
                self.king_attacks_black += s.piece_king_attack['p']
            self.center_attacks_black += s.center_attacks[square + 9] * s.piece_center_attack['p']
            self.center_attacks_black += s.center_attacks[square + 11] * s.piece_center_attack['p']'''

        # 1 square move
        if self.board[square + move_dir] == '--':
            if not piece_pinned or pin_direction in (move_dir, -move_dir):
                piece_increase = (s.piece_value_mid_game['p'][square + move_dir] - s.piece_value_mid_game['p'][square]) * self.midgame + \
                                 (s.piece_value_end_game['p'][square + move_dir] - s.piece_value_end_game['p'][square]) * self.endgame
                if square + move_dir in end_row:
                    moves.append((square, square + move_dir, 'pQ', piece_increase))
                    moves.append((square, square + move_dir, 'pR', piece_increase))
                    moves.append((square, square + move_dir, 'pB', piece_increase))
                    moves.append((square, square + move_dir, 'pN', piece_increase))
                else:
                    moves.append((square, square + move_dir, 'no', piece_increase))
                # 2 square move
                if square in start_row and self.board[square + 2*move_dir] == '--':
                    moves.append((square, square + 2*move_dir, 'ts', piece_increase))

        # Capture and enpassant to the left
        if self.board[square + move_dir - 1][0] == enemy_color:
            if not piece_pinned or pin_direction == move_dir - 1:
                piece_increase = (s.piece_value_mid_game['p'][square + move_dir - 1] - s.piece_value_mid_game['p'][square]) * self.midgame + \
                                 (s.piece_value_end_game['p'][square + move_dir - 1] - s.piece_value_end_game['p'][square]) * self.endgame
                if square + move_dir in end_row:
                    moves.append((square, square + move_dir - 1, 'pQ', piece_increase + s.mvv_lva_values['Q'] + s.mvv_lva_values[self.board[square + move_dir - 1][1]]))
                    moves.append((square, square + move_dir - 1, 'pR', piece_increase + s.mvv_lva_values['R'] + s.mvv_lva_values[self.board[square + move_dir - 1][1]]))
                    moves.append((square, square + move_dir - 1, 'pB', piece_increase + s.mvv_lva_values['B'] + s.mvv_lva_values[self.board[square + move_dir - 1][1]]))
                    moves.append((square, square + move_dir - 1, 'pN', piece_increase + s.mvv_lva_values['N'] + s.mvv_lva_values[self.board[square + move_dir - 1][1]]))
                else:
                    moves.append((square, square + move_dir - 1, 'no', piece_increase + s.mvv_lva_values[self.board[square + move_dir - 1][1]]))

        elif square + move_dir - 1 == self.enpassant_square:
            if not piece_pinned or pin_direction == move_dir - 1:
                king_pos = self.white_king_location if self.is_white_turn else self.black_king_location

                # Check if the move would result in check
                self.board[square], self.board[square - 1] = '--', '--'
                self.board[self.enpassant_square] = f'{friendly_color}p'
                is_check = self.check_for_checks(king_pos)
                self.board[square], self.board[square - 1] = f'{friendly_color}p', f'{enemy_color}p'
                self.board[self.enpassant_square] = '--'

                if not is_check:
                    piece_increase = (s.piece_value_mid_game['p'][square + move_dir - 1] - s.piece_value_mid_game['p'][square]) * self.midgame + \
                                     (s.piece_value_end_game['p'][square + move_dir - 1] - s.piece_value_end_game['p'][square]) * self.endgame
                    moves.append((square, square + move_dir - 1, 'ep', piece_increase))

        # Capture, and enpassant to the right
        if self.board[square + move_dir + 1][0] == enemy_color:
            if not piece_pinned or pin_direction == move_dir + 1:
                piece_increase = (s.piece_value_mid_game['p'][square + move_dir + 1] - s.piece_value_mid_game['p'][square]) * self.midgame + \
                                 (s.piece_value_end_game['p'][square + move_dir + 1] - s.piece_value_end_game['p'][square]) * self.endgame
                if square + move_dir in end_row:
                    moves.append((square, square + move_dir + 1, 'pQ', piece_increase + s.mvv_lva_values['Q'] + s.mvv_lva_values[self.board[square + move_dir + 1][1]]))
                    moves.append((square, square + move_dir + 1, 'pR', piece_increase + s.mvv_lva_values['Q'] + s.mvv_lva_values[self.board[square + move_dir + 1][1]]))
                    moves.append((square, square + move_dir + 1, 'pB', piece_increase + s.mvv_lva_values['Q'] + s.mvv_lva_values[self.board[square + move_dir + 1][1]]))
                    moves.append((square, square + move_dir + 1, 'pN', piece_increase + s.mvv_lva_values['Q'] + s.mvv_lva_values[self.board[square + move_dir + 1][1]]))
                else:
                    moves.append((square, square + move_dir + 1, 'no', piece_increase + s.mvv_lva_values[self.board[square + move_dir + 1][1]]))

        elif square + move_dir + 1 == self.enpassant_square:
            if not piece_pinned or pin_direction == move_dir + 1:
                king_pos = self.white_king_location if self.is_white_turn else self.black_king_location

                # Check if the move would result in check
                self.board[square], self.board[square + 1] = '--', '--'
                self.board[self.enpassant_square] = f'{friendly_color}p'
                is_check = self.check_for_checks(king_pos)
                self.board[square], self.board[square + 1] = f'{friendly_color}p', f'{enemy_color}p'
                self.board[self.enpassant_square] = '--'

                if not is_check:
                    piece_increase = (s.piece_value_mid_game['p'][square + move_dir + 1] - s.piece_value_mid_game['p'][square]) * self.midgame + \
                                     (s.piece_value_end_game['p'][square + move_dir + 1] - s.piece_value_end_game['p'][square]) * self.endgame
                    moves.append((square, square + move_dir + 1, 'ep', piece_increase))

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
                piece_increase = (s.piece_value_mid_game['N'][end_square] - s.piece_value_mid_game['N'][square]) * self.midgame + \
                                 (s.piece_value_end_game['N'][end_square] - s.piece_value_end_game['N'][square]) * self.endgame
                moves.append((square, end_square, 'no', piece_increase + s.mvv_lva_values[self.board[end_square][1]]))

                '''# Add square to attacking squares king and center
                if self.is_white_turn:
                    if end_square in self.king_attack_squares[1]:
                        self.king_attacks_white += s.piece_king_attack['N']
                    self.center_attacks_white += s.center_attacks[end_square] * s.piece_center_attack['N']
                else:
                    if end_square in self.king_attack_squares[0]:
                        self.king_attacks_black += s.piece_king_attack['N']
                    self.center_attacks_black += s.center_attacks[end_square] * s.piece_center_attack['N']'''

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
                        piece_increase = (s.piece_value_mid_game['B'][end_square] - s.piece_value_mid_game['B'][square]) * self.midgame + \
                                         (s.piece_value_end_game['B'][end_square] - s.piece_value_end_game['B'][square]) * self.endgame
                        moves.append((square, end_square, 'no', piece_increase + s.mvv_lva_values[self.board[end_square][1]]))

                        '''# Add square to attacking squares king and center
                        if self.is_white_turn:
                            if end_square in self.king_attack_squares[1]:
                                self.king_attacks_white += s.piece_king_attack['B']
                            self.center_attacks_white += s.center_attacks[end_square] * s.piece_center_attack['B']
                        else:
                            if end_square in self.king_attack_squares[0]:
                                self.king_attacks_black += s.piece_king_attack['B']
                            self.center_attacks_black += s.center_attacks[end_square] * s.piece_center_attack['B']'''

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
                    if not piece_pinned or pin_direction in (d, -d):
                        piece_increase = (s.piece_value_mid_game['R'][end_square] - s.piece_value_mid_game['R'][square]) * self.midgame + \
                                         (s.piece_value_end_game['R'][end_square] - s.piece_value_end_game['R'][square]) * self.endgame
                        moves.append((square, end_square, 'no', piece_increase + s.mvv_lva_values[self.board[end_square][1]]))

                        '''# Add square to attacking squares king and center
                        if self.is_white_turn:
                            if end_square in self.king_attack_squares[1]:
                                self.king_attacks_white += s.piece_king_attack['R']
                            self.center_attacks_white += s.center_attacks[end_square] * s.piece_center_attack['R']
                        else:
                            if end_square in self.king_attack_squares[0]:
                                self.king_attacks_black += s.piece_king_attack['R']
                            self.center_attacks_black += s.center_attacks[end_square] * s.piece_center_attack['R']'''

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
                    if not piece_pinned or pin_direction in (-d, d):
                        piece_increase = (s.piece_value_mid_game['Q'][end_square] - s.piece_value_mid_game['Q'][square]) * self.midgame + \
                                         (s.piece_value_end_game['Q'][end_square] - s.piece_value_end_game['Q'][square]) * self.endgame
                        moves.append((square, end_square, 'no', piece_increase + s.mvv_lva_values[self.board[end_square][1]]))

                        '''# Add square to attacking squares king and center
                        if self.is_white_turn:
                            if end_square in self.king_attack_squares[1]:
                                self.king_attacks_white += s.piece_king_attack['Q']
                            self.center_attacks_white += s.center_attacks[end_square] * s.piece_center_attack['Q']
                        else:
                            if end_square in self.king_attack_squares[0]:
                                self.king_attacks_black += s.piece_king_attack['Q']
                            self.center_attacks_black += s.center_attacks[end_square] * s.piece_center_attack['Q']'''

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

                # Temporarily replace piece from the square and check all surrounding squares to see if it is attacked or not
                self.board[end_square] = '--'
                is_in_check = self.check_for_checks(end_square)
                self.board[end_square] = end_piece

                if not is_in_check:
                    piece_increase = (s.piece_value_mid_game['K'][end_square] - s.piece_value_mid_game['K'][square]) * self.midgame + \
                                     (s.piece_value_end_game['K'][end_square] - s.piece_value_end_game['K'][square]) * self.endgame
                    moves.append((square, end_square, 'no', piece_increase + s.mvv_lva_values[self.board[end_square][1]]))

        # Castling:
        # Can't castle if in check, if square between K or R is under attack, or if castling rights are broken
        if not self.is_in_check:
            king_castle = 'K' if self.is_white_turn else 'k'
            queen_castle = 'Q' if self.is_white_turn else 'q'

            # Castle King side
            if king_castle in self.castling_rights and all(x == '--' for x in (self.board[square + 1], self.board[square + 2])):

                # Check if squares are in check or not
                is_in_check_1 = self.check_for_checks(square + 1)
                is_in_check_2 = self.check_for_checks(square + 2)

                if not (is_in_check_1 or is_in_check_2):
                    moves.append((square, square + 2, 'ck', 40))

            # Castle Queen side
            if queen_castle in self.castling_rights and all(x == '--' for x in (self.board[square - 1], self.board[square - 2], self.board[square - 3])):

                # Check if squares are in check or not, king doesn't pass the knight square on queenside castle so no use in checking that square
                is_in_check_1 = self.check_for_checks(square - 1)
                is_in_check_2 = self.check_for_checks(square - 2)

                if not (is_in_check_1 or is_in_check_2):
                    moves.append((square, square - 2, 'cq', 40))

# ---------------------------------------------------------------------------------------------------------
#                        Special check for check function for speed up
# ---------------------------------------------------------------------------------------------------------

    # Checks if there are any pinned pieces or current checks
    def check_for_checks(self, square):

        enemy_color, friendly_color = ('b', 'w') if self.is_white_turn else ('w', 'b')

        # Check out from all directions from the king
        for i, d in enumerate(s.directions):
            for j in range(8):  # Check the entire row/column in that direction
                end_square = square + d*j
                piece_color, piece_type = self.board[end_square][0], self.board[end_square][1]
                if piece_type != 'F':
                    if piece_color == friendly_color and piece_type != 'K':
                        break
                    elif piece_color == enemy_color:
                        if (0 <= i <= 3 and piece_type == 'R') or \
                                (4 <= i <= 7 and piece_type == 'B') or \
                                (j == 1 and piece_type == 'p' and ((enemy_color == 'w' and 6 <= i <= 7) or (enemy_color == 'b' and 4 <= i <= 5))) or \
                                (piece_type == 'Q') or \
                                (j == 1 and piece_type == 'K'):
                            return True
                        else:  # Enemy piece that is not applying check or pin
                            break
                else:  # i, j is off board
                    break

        # Check for knight checks
        for d in s.knight_moves:
            end_piece = self.board[square + d]
            if end_piece != 'FF':
                if end_piece[0] == enemy_color and end_piece[1] == 'N':  # Enemy knight attacking king
                    return True

        return False
