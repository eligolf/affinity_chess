#  --------------------------------------------------------------------------------
#                                AI Brain
#  --------------------------------------------------------------------------------

import settings as s
from gamestate import *
import evaluation as e
import opening_move as om
import syzygy as sy

import time
import math


class Ai:

    def __init__(self, min_search_depth=s.min_search_depth, is_playing_with_opening_book=s.play_with_opening_book):

        # Transposition table init
        self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None}
        self.tt_entry_q = {'value': 0, 'flag': ''}

        self.valid_moves_history = {}
        self.killer_moves = {}

        # Opening related parameters
        self.is_in_opening = is_playing_with_opening_book

        # Count the nodes searched, only for development purposes.
        self.counter = -1

        # Best moves from previous iterations
        self.best_moves = []

        # Used in the iterative deepening loop to stop after a certain time has passed
        self.timer = 0

        # To what depth it searched
        self.max_depth = 0
        self.real_depth = 0
        self.min_search_depth = min_search_depth

    def ai_make_move(self, gamestate):

        # Init variables
        nodes = {}
        self.valid_moves_history = {}

        for depth in range(gamestate.max_search_depth + 1):
            self.killer_moves[depth] = []

        start_color = -1 if gamestate.is_ai_white else 1

        # Don't try an opening move if the start position is not the standard start position
        if gamestate.start_fen != s.start_fen:
            self.is_in_opening = False

        # Check if there is any opening moves to make in the current position
        if self.is_in_opening:
            time_start = time.time()
            move = om.make_opening_move(gamestate)
            self.timer = time.time() - time_start
            evaluation = 0
            if not move or gamestate.move_counter >= 0.5 + s.max_opening_moves:
                self.is_in_opening = False

        # Negamax with iterative deepening if not in opening
        if not self.is_in_opening:

            # Try if position is in syzygy tablebase, only in endgames
            if not gamestate.midgame:
                # Only the 3, 4 and 5 piece tablebases are currently implemented
                if sum(gamestate.piece_dict[0].values()) + sum(gamestate.piece_dict[1].values()) <= 5:
                    endgame_move, evaluation, dtz = sy.find_endgame_move(gamestate)
                    if endgame_move:

                        start_time = time.time()
                        # Also first try if can find an easy mate, if so play that
                        if abs(dtz) <= 1:
                            mate_depth = gamestate.max_search_depth if gamestate.max_search_depth < 6 else 6
                            endgame_move_2, evaluation_2 = self.negamax(gamestate, mate_depth, -math.inf, math.inf, start_color, False)
                            self.timer = time.time() - start_time
                            if abs(evaluation_2) >= 1e6:
                                return endgame_move_2, evaluation_2

                        return endgame_move, evaluation

            # Init parameters for iterative deepening
            self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}
            self.best_moves = []

            # Iterative deepening
            time_start = time.time()
            for depth in range(1, gamestate.max_search_depth + 1):

                move, evaluation = self.negamax(gamestate, depth, -math.inf, math.inf, start_color, False)
                self.best_moves.append([move, evaluation])

                time_end = time.time()
                self.timer = time_end - time_start

                nodes[depth] = self.counter - sum(nodes.values())
                print('Depth: ', depth)
                #  print('Nodes searched: ', nodes[depth])
                print('Time spent: ', round(self.timer, 2), 's\n')

                self.counter = -1

                # Break if time has run out, if reached at least min depth, or if finding a mate in lowest number of moves
                if (self.timer > s.max_search_time and depth >= self.min_search_depth) or (evaluation / 100) > 100:
                    break
            print('----------------------------------')

            # Always return moves from an even number of depth, helps in some situation since quiescence search is not implemented
            self.max_depth = depth
            self.real_depth = self.max_depth
            if self.max_depth >= 2:
                evaluation = (self.best_moves[-1][1] + self.best_moves[-2][1]) / 2
                if len(self.best_moves) % 2 == 0:
                    move = self.best_moves[-1][0]
                else:
                    move = self.best_moves[-2][0]
                    self.max_depth -= 1

        return move, evaluation

#  --------------------------------------------------------------------------------
#                            Negamax function
#  --------------------------------------------------------------------------------

    def negamax(self, gamestate, depth, alpha, beta, color, allow_nullmove):
        alpha_original = alpha

        #  self.counter += 1

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

        # Depth with quiescence search
        '''if depth == 0:
            if gamestate.piece_captured != '--':
                return None, self.quiescence(gamestate, -beta, -alpha, -color, 0)
            else:
                return None, e.evaluate(gamestate, depth) * color'''
        # Depth = 0 without quiescence search
        if depth == 0:
            return None, e.evaluate(gamestate, depth) * color

        # Don't search valid moves again if it has been done in last iteration
        if key in self.valid_moves_history and self.valid_moves_history[key]:
            children = self.valid_moves_history[key]
        else:
            children = gamestate.get_valid_moves()
            self.valid_moves_history[key] = children

        # Check if there is a checkmate or stalemate
        if gamestate.is_check_mate or gamestate.is_stale_mate:
            return None, e.evaluate(gamestate, depth) * color

        # Null move logic (https://hci.iwr.uni-heidelberg.de/system/files/private/downloads/1935772097/report_qingyang-cao_enhanced-forward-pruning.pdf,
        # http://mediocrechess.blogspot.com/2007/01/guide-null-moves.html)
        # https://open-chess.org/viewtopic.php?t=2994
        if allow_nullmove and depth - 1 - s.R >= 0:  # and e.evaluate(gamestate, depth) >= beta - 50:  # and not using PV line
            king_pos = gamestate.white_king_location if gamestate.is_white_turn else gamestate.black_king_location
            if not gamestate.check_for_checks(king_pos):
                gamestate.make_nullmove()
                evaluation = -self.negamax(gamestate, depth - 1 - s.R, -beta, -beta + 1, -color, False)[1]
                gamestate.unmake_nullmove()

                if evaluation >= beta:
                    return None, evaluation

        # Sort moves before Negamax
        children = self.sort_moves(gamestate, children, depth)

        # Negamax loop
        max_eval = -math.inf
        for child in reversed(children):

            gamestate.make_move(child)

            score = -self.negamax(gamestate, depth - 1, -beta, -alpha, -color, True)[1]
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
#                           Quiescence search
#  --------------------------------------------------------------------------------

    def quiescence(self, gamestate, alpha, beta, color, moves):

        moves += 1

        # Check if value is in table
        key = gamestate.zobrist_key
        if key in self.tt_entry_q:
            if self.tt_entry_q[key]['flag'] == 'exact':
                score = self.tt_entry_q[key]['value']
            else:
                score = color * e.evaluate(gamestate, 0)
                self.tt_entry_q[key] = {'flag': 'exact'}
                self.tt_entry_q[key]['value'] = score
        else:
            score = e.evaluate(gamestate, 0)
            self.tt_entry_q[key] = {'flag': 'exact'}
            self.tt_entry_q[key]['value'] = score

        big_delta = s.mvv_lva_values[gamestate.piece_captured[1]] + 200
        if score < alpha - big_delta:
            return alpha
        if score >= beta:
            return beta
        if alpha < score:
            alpha = score

        # If having looked through 2 moves then stop and return value
        if moves >= 3:
            return score

        # Don't search valid moves again if it has been done in last iteration
        if key in self.valid_moves_history and self.valid_moves_history[key]:
            children = self.valid_moves_history[key]
        else:
            children = gamestate.get_valid_moves()
            self.valid_moves_history[key] = children

        children = self.sort_moves(gamestate, children, 0)

        for child in children:

            # Only look at capture moves (and later checks)
            if gamestate.board[child[1]] != '--':
                gamestate.make_move(child)
                score = -self.quiescence(gamestate, -beta, -alpha, -color, moves)
                gamestate.unmake_move()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

        return alpha

#  --------------------------------------------------------------------------------
#                       Sort moves for Negamax
#  --------------------------------------------------------------------------------

    def sort_moves(self, gamestate, children, depth):

        # MVV sorting
        children.sort(key=lambda x: x[3])

        # Killer moves
        if self.killer_moves[depth]:
            for move in self.killer_moves[depth]:
                if move in children:
                    children.remove(move)
                    children.append(move)

        # Best move from previous iteration is picked as best guess for next iteration
        if gamestate.zobrist_key in self.tt_entry:
            previous_best = self.tt_entry[gamestate.zobrist_key]['best move']
            if previous_best in children:
                children.remove(previous_best)
                children.append(previous_best)

        return children
