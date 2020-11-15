#  --------------------------------------------------------------------------------
#                                AI Brain
#  --------------------------------------------------------------------------------

import settings as s
from board import *
import evaluation as e

import pandas as pd
import time
import random
import copy
import math


class Ai:

    def __init__(self):

        self.killer_moves = {}
        for depth in range(s.max_search_depth + 1):
            self.killer_moves[depth] = []

        # Transposition table init
        self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}

        self.valid_moves_history = {}

        # Opening related parameters
        self.df = pd.read_csv('opening_book/opening_book_1.csv', encoding='ISO-8859-1')
        self.openings = self.df['Moves'].tolist()
        self.opening_names = self.df['Opening name'].tolist()
        self.opening_name = ''
        self.is_in_opening = True

        self.not_PV = False

        self.counter = -1
        self.check_mate_counter = 0
        self.is_check_counter = 0
        self.capture_counter = 0

    def ai_make_move(self, gamestate, moves_list):

        # AI level 3, Negamax
        if s.level == 3:

            # Check if there is any opening moves to make
            if self.is_in_opening and s.play_with_opening_book:
                move = self.play_an_opening_move(gamestate, moves_list)
                evaluation = 0

            # Normal Negamax if not in opening
            if not self.is_in_opening or not s.play_with_opening_book:

                # Init parameters for iterative deepening
                self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}

                # Iterative deepening
                time_start = time.time()
                for depth in range(1, s.max_search_depth + 1):

                    move, evaluation = self.negamax(gamestate, depth, -math.inf, math.inf, s.start_color)

                    time_end = time.time()
                    timer = time_end - time_start
                    print('---------------------------------------------')
                    print('Depth: ', depth, '\nTime spent: ', str(round(timer, 2)) + ' s\n')
                    print('Nodes searched: ' + str(self.counter))
                    print('Check mates: ' + str(self.check_mate_counter))
                    print('Checks: ' + str(self.is_check_counter))
                    print('Captures: ' + str(self.capture_counter))
                    print('---------------------------------------------')
                    self.counter = -1
                    self.check_mate_counter = 0
                    self.is_check_counter = 0
                    self.capture_counter = 0

                    # Break if time has run our, if reached at least min depth, or if finding a mate in lowest number of moves
                    if (timer > s.max_search_time and depth >= s.min_search_depth) or (evaluation / s.eval_level) > 100:
                        break

        # AI level 0, 1 or 2
        elif s.level in [0, 1, 2]:
            levels = {0: self.ai_random(gamestate),
                      1: self.ai_1_ahead(gamestate),
                      2: self.ai_1_ahead(gamestate)}

            move = levels[s.level]
            evaluation = e.evaluate(self.gamestate)

        return move, evaluation

#  --------------------------------------------------------------------------------
#          Level 3: Negamax function with alpha-beta pruning
#  --------------------------------------------------------------------------------

    def negamax(self, gamestate, depth, alpha, beta, color):
        alpha_original = alpha
        self.counter += 1

        '''# Transposition table lookup (https://en.wikipedia.org/wiki/Negamax#Negamax_with_alpha_beta_pruning_and_transposition_tables)
        key = gamestate.zobrist_key
        if key in self.tt_entry and self.tt_entry[key]['depth'] >= depth:
            if self.tt_entry[key]['flag'] == 'exact':
                return self.tt_entry[key]['best move'], self.tt_entry[key]['value']
            elif self.tt_entry[key]['flag'] == 'lowerbound':
                alpha = max(alpha, self.tt_entry[key]['value'])
            elif self.tt_entry[key]['flag'] == 'upperbound':
                beta = min(beta, self.tt_entry[key]['value'])
            if alpha >= beta:
                return self.tt_entry[key]['best move'], self.tt_entry[key]['value']'''

        # If depth is 0, always evaluate leaf node
        if depth == 0:
            return None, e.evaluate(gamestate, depth) * color

        '''# Don't search valid moves again if it has been done in last iteration
        if key in self.valid_moves_history and self.valid_moves_history[key]:
            children = self.valid_moves_history[key]
        else:
            children = gamestate.get_valid_moves()
            self.valid_moves_history[key] = children'''
        children = gamestate.get_valid_moves()

        if gamestate.is_in_check:
            self.is_check_counter += 1

        # Need to calculate valid moves to know if there is a checkmate or stalemate
        if gamestate.is_check_mate or gamestate.is_stale_mate:
            if gamestate.is_check_mate:
                self.check_mate_counter += 1
            return None, e.evaluate(gamestate, depth) * color

        # Null move logic here (https://hci.iwr.uni-heidelberg.de/system/files/private/downloads/1935772097/report_qingyang-cao_enhanced-forward-pruning.pdf,
        # http://mediocrechess.blogspot.com/2007/01/guide-null-moves.html)
        '''if allow_nullmove and depth >= 3 and self.not_PV:  # and not using PV line
            if not gamestate.is_in_check:
                gamestate.make_nullmove()
                evaluation = -self.negamax(gamestate, depth - 1 - s.R, -beta, -beta + 1, -color, False)[1]
                gamestate.unmake_nullmove()

                if evaluation >= beta:
                    return None, evaluation'''

        # Sort moves before Negamax
        #children = self.sort_moves(gamestate, children, depth, color)

        # Negamax loop
        max_eval = -math.inf
        for child in reversed(children):
            gamestate.make_move(child[0], child[1])

            if gamestate.piece_captured != '--':
                self.capture_counter += 1

            score = -self.negamax(gamestate, depth - 1, -beta, -alpha, -color)[1]

            gamestate.unmake_move()

            if score > max_eval:
                max_eval = score
                best_move = child
            alpha = max(alpha, max_eval)
            '''if beta <= alpha:
                # Killer moves
                if gamestate.piece_captured == '--':
                    self.killer_moves[depth].append(child)
                    if len(self.killer_moves[depth]) == s.no_of_killer_moves:  # Keep killer moves at a maximum of 2 per depth
                        self.killer_moves[depth].pop(0)
                break'''

        '''# Transposition table saving
        self.tt_entry[gamestate.zobrist_key] = {'value': max_eval}
        if max_eval <= alpha_original:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'upperbound'
        elif max_eval >= beta:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'lowerbound'
        else:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'exact'

        self.tt_entry[gamestate.zobrist_key]['depth'] = depth
        self.tt_entry[gamestate.zobrist_key]['best move'] = best_move'''

        return best_move, max_eval

    #  --------------------------------------------------------------------------------
    #             Sort moves for Negamax
    #  --------------------------------------------------------------------------------

    def sort_moves(self, gamestate, children, depth, color):
        # Killer moves
        if self.killer_moves[depth]:
            #children.sort(key=lambda x: x in self.killer_moves[depth])  # I think this works too, not much difference in speed though
            for move in self.killer_moves[depth]:
                if move in children:
                    children.remove(move)
                    children.append(move)

        # MVV-LVA sorting, store a maximum of the s.mvv_storing to children
        mvv_lva_values = []
        for move in children:
            if gamestate.board[move[1]] != '--':
                # If can capture last moved piece, then try this first
                if move[1] == gamestate.move_log[-1][1]:
                    mvv_lva_values.append([s.mvv_lva_values[gamestate.board[move[1]][1]] - s.mvv_lva_values[gamestate.board[move[0]][1]] + 1000, move])
                else:
                    mvv_lva_values.append([s.mvv_lva_values[gamestate.board[move[1]][1]] - s.mvv_lva_values[gamestate.board[move[0]][1]], move])
        mvv_lva_values.sort(reverse=True)
        top_values = mvv_lva_values[-min(s.mvv_storing, len(mvv_lva_values)):]
        for move_value in top_values:
            move = move_value[1]
            children.remove(move)
            children.append(move)

        # Best move from previous iteration is picked as best guess for next iteration
        if gamestate.zobrist_key in self.tt_entry:
            previous_best = self.tt_entry[gamestate.zobrist_key]['best move']
            if previous_best in children:
                children.remove(previous_best)
                children.append(previous_best)
        else:
            # Internal iterative deepening if not finding a best guess
            if depth >= 2:
                move = self.negamax(gamestate, depth - 2, -math.inf, math.inf, -color)[0]
                if move:
                    if move in children:
                        children.remove(move)
                        children.append(move)

        return children

#  --------------------------------------------------------------------------------
#             Level 2: TBD
#  --------------------------------------------------------------------------------

    def ai_2(self, gamestate):

        pass

#  --------------------------------------------------------------------------------
#             Level 1: Look 1 half move ahead
#  --------------------------------------------------------------------------------

    def ai_1_ahead(self, gamestate):
        valid_moves = gamestate.get_valid_moves()

        if not valid_moves:
            print('No available moves')

        max_eval = -math.inf
        for move in valid_moves:
            board_copy = copy.deepcopy(gamestate)
            board_copy.make_move(move[0], move[1])

            evaluation = e.evaluate(board_copy)

            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move

        return best_move

#  --------------------------------------------------------------------------------
#             Level 0: Choose a random move from valid moves
#  --------------------------------------------------------------------------------

    def ai_random(self, gamestate):
        valid_moves = gamestate.get_valid_moves()
        ai_move = random.choice(valid_moves)

        return ai_move

#  --------------------------------------------------------------------------------
#                    Helper functions
#  --------------------------------------------------------------------------------

    def play_an_opening_move(self, gamestate, moves_list):

        # Find all opening candidates, openings starting with the moves_list move order. [opening, next move, index of opening, opening_name]
        opening_candidates = []

        for i, opening in enumerate(self.openings):
            if moves_list.lstrip() in opening:
                partition = '.' if s.is_ai_white else ' '
                next_move = opening[len(moves_list.lstrip()) + 1:].partition(partition)[0]
                opening_candidates.append((opening, next_move, i, self.opening_names[i]))

        #  Chose a random opening if an opening exists
        if opening_candidates:
            chosen_opening = random.choice(opening_candidates)
            chosen_move_text = chosen_opening[1]
            self.opening_name = chosen_opening[3]

            if chosen_move_text:
                # Castling
                if chosen_move_text == 'O-O':
                    return 25, 27
                elif chosen_move_text == 'O-O-O':
                    return 25, 23

                # Find what start_square and end_square the chosen_move corresponds to, different if last move was a checking move.
                if chosen_move_text[-1] == '+':
                    end_square = (8 - int(chosen_move_text[-2]) + 2) * 10 + s.letters.index(chosen_move_text[-3]) + 1
                else:
                    end_square = (8 - int(chosen_move_text[-1]) + 2) * 10 + s.letters.index(chosen_move_text[-2]) + 1

                valid_moves = gamestate.get_valid_moves()

                for move in valid_moves:
                    if move[1] == end_square:

                        if chosen_move_text[0] == gamestate.board[move[0]][1]:  # If it is a piece
                            start_square = move[0]
                            break

                        if gamestate.board[move[0]][1] == 'p':  # If it is a pawn
                            start_square = move[0]
                            break

                return start_square, end_square

        self.is_in_opening = False
