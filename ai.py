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

        # Transposition table init
        self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}

        self.valid_moves_history = {}

        # Opening related parameters
        self.df = pd.read_csv('opening_book/opening_book_1.csv', encoding='ISO-8859-1')
        self.openings = self.df['Moves'].tolist()
        self.opening_names = self.df['Opening name'].tolist()
        self.opening_name = ''
        self.is_in_opening = True

        self.counter = -1
        self.nodes = {}
        self.check_mate_counter = 0
        self.is_check_counter = 0
        self.capture_counter = 0

        self.best_moves = []

        self.timer = 0

    def ai_make_move(self, gamestate, moves_list):

        # AI level 3, Negamax
        if s.level == 3:

            # Init variables
            for depth in range(gamestate.max_search_depth + 1):
                self.killer_moves[depth] = []

            self.nodes = {}

            self.start_color = -1 if gamestate.is_ai_white else 1

            # Check if there is any opening moves to make
            if self.is_in_opening and gamestate.play_with_opening_book and gamestate.start_fen == s.start_fen:
                move = self.play_an_opening_move(gamestate, moves_list)
                evaluation = 0

            # Normal Negamax if not in opening
            if not self.is_in_opening or not gamestate.play_with_opening_book:

                # Init parameters for iterative deepening
                self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}
                self.best_moves = []

                # Iterative deepening
                time_start = time.time()
                for depth in range(1, gamestate.max_search_depth + 1):

                    move, evaluation = self.negamax(gamestate, depth, -math.inf, math.inf, self.start_color)
                    self.best_moves.append([move, evaluation])

                    time_end = time.time()
                    self.timer = time_end - time_start

                    self.nodes[depth] = self.counter - sum(self.nodes.values())
                    print('Depth: ', depth)
                    #print('Nodes searched: ', self.nodes[depth])
                    print('Time spent: ', round(self.timer, 2), 's\n')

                    self.counter = -1

                    # Break if time has run our, if reached at least min depth, or if finding a mate in lowest number of moves
                    if self.timer > s.max_search_time or depth >= s.min_search_depth or (evaluation / s.eval_level) > 100:
                        break

                # Always return moves from an even number of depth, helps in some situation since quiescence search is not implemented
                if len(self.best_moves) % 2 == 0:
                    move = self.best_moves[-1][0]
                    evaluation = self.best_moves[-1][1]
                else:
                    move = self.best_moves[-2][0]
                    evaluation = self.best_moves[-2][1]

        # AI level 0, 1 or 2
        elif s.level in [0, 1]:
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

        #self.counter += 1

        # Transposition table lookup (https://en.wikipedia.org/wiki/Negamax#Negamax_with_alpha_beta_pruning_and_transposition_tables)
        key = gamestate.zobrist_key
        if key in self.tt_entry and self.tt_entry[key]['depth'] >= depth:
            if self.tt_entry[key]['flag'] == 'exact':
                return self.tt_entry[key]['best move'], self.tt_entry[key]['value']
            elif self.tt_entry[key]['flag'] == 'lowerbound':
                alpha = max(alpha, self.tt_entry[key]['value'])
            elif self.tt_entry[key]['flag'] == 'upperbound':
                beta = min(beta, self.tt_entry[key]['value'])
            if alpha >= beta:
                return self.tt_entry[key]['best move'], self.tt_entry[key]['value']

        # If depth is 0, always evaluate leaf node
        if depth == 0:
            return None, e.evaluate(gamestate, depth) * color

        # Don't search valid moves again if it has been done in last iteration
        if key in self.valid_moves_history and self.valid_moves_history[key]:
            children = self.valid_moves_history[key]
        else:
            children = gamestate.get_valid_moves()
            self.valid_moves_history[key] = children

        # Need to calculate valid moves to know if there is a checkmate or stalemate
        if gamestate.is_check_mate or gamestate.is_stale_mate:
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
        children = self.sort_moves(gamestate, children, depth, color)

        # Negamax loop
        max_eval = -math.inf
        for child in reversed(children):

            gamestate.make_move(child[0], child[1], child[2])
            score = -self.negamax(gamestate, depth - 1, -beta, -alpha, -color)[1]
            gamestate.unmake_move()

            if score > max_eval:
                max_eval = score
                best_move = child
            alpha = max(alpha, max_eval)

            # Beta cutoff
            if beta <= alpha:

                # Killer moves
                if gamestate.piece_captured == '--':
                    self.killer_moves[depth].append(child)
                    if len(self.killer_moves[depth]) == s.no_of_killer_moves:  # Keep killer moves at a maximum of x per depth
                        self.killer_moves[depth].pop(0)
                break

        # Transposition table saving
        self.tt_entry[gamestate.zobrist_key] = {'value': max_eval}
        if max_eval <= alpha_original:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'upperbound'
        elif max_eval >= beta:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'lowerbound'
        else:
            self.tt_entry[gamestate.zobrist_key]['flag'] = 'exact'

        self.tt_entry[gamestate.zobrist_key]['depth'] = depth
        self.tt_entry[gamestate.zobrist_key]['best move'] = best_move

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
                if move[1] == gamestate.move_log[-1][0][1]:
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
                partition = '.' if gamestate.is_ai_white else ' '
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
                    return 25, 27, 'ck'
                elif chosen_move_text == 'O-O-O':
                    return 25, 23, 'cq'

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

                return start_square, end_square, 'no'

        self.is_in_opening = False
