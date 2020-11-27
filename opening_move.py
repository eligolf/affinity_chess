import chess
import chess.polyglot
import random
import os

import fen_handling as fh
import settings as s


def make_opening_move(gamestate):

    moves = []
    fen = fh.gamestate_to_fen(gamestate)

    board = chess.Board(fen)

    for subdir, dirs, files in os.walk('opening_book'):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext in '.bin':
                with chess.polyglot.open_reader(os.path.join(subdir, file)) as reader:
                    for i, entry in enumerate(reader.find_all(board)):
                        moves.append(entry.move)

                        # Only pick from the most common openings
                        if i == 4:
                            break

    # Pick a random move moves if exists, else return None
    if moves:
        random_move = random.choice(moves)
    else:
        return None

    move = process_move(gamestate, random_move)

    return move


def process_move(gamestate, move):

    move = str(move)
    move_type = 'no'
    start_square = s.convert_textual[move[1]] + int(s.fen_letters[move[0]])
    end_square = s.convert_textual[move[3]] + int(s.fen_letters[move[2]])

    piece = gamestate.board[start_square]

    if piece[1] == 'p' and abs(start_square - end_square) == 20:
        move_type = 'ts'
    if piece[1] == 'p' and (start_square % 10 - end_square % 10) != 0 and gamestate.board[end_square] == '--':
        move_type = 'ep'
    if piece[1] == 'p' and end_square in range(21, 29) or end_square in range(91, 99):
        move_type = 'pQ'
    if piece[1] == 'K' and start_square - end_square == 2:
        move_type = 'cq'
    if piece[1] == 'K' and start_square - end_square == -2:
        move_type = 'ck'

    return start_square, end_square, move_type





