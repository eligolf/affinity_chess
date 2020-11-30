import chess
import chess.syzygy

import fen_handling as fh


def find_endgame_move(gamestate):

    # Get fen and Python-Chess board from the given gamestate
    fen = fh.gamestate_to_fen(gamestate)
    board = chess.Board(fen)

    with chess.syzygy.open_tablebase('syzygy') as tablebase:
        original_dtz = tablebase.get_dtz(board)
        original_wdl = tablebase.get_wdl(board)

    # If position not in tablebase, return None
    if not original_dtz:
        return None, None

    # If finding a position in the tablebases, find the move that lowers the distance to zero (DTZ)
    if original_dtz and original_wdl in (1, 2):

        # Find all possible moves and try them to see if it lowers original dtz
        valid_moves = gamestate.get_valid_moves()
        for move in valid_moves:
            gamestate.make_move(move[0], move[1], move[2])
            fen = fh.gamestate_to_fen(gamestate)
            board = chess.Board(fen)

            with chess.syzygy.open_tablebase('syzygy') as tablebase:
                new_dtz = tablebase.get_dtz(board)
                new_wdl = tablebase.get_wdl(board)

            # If finding a move that lowers DTZ, return that move
            if abs(new_dtz) < original_dtz and new_wdl in (-1, -2):
                gamestate.unmake_move()
                distance_to_mate = (original_dtz + 1) // 2
                return move, distance_to_mate

            gamestate.unmake_move()

    return None, None


def check_for_draw(gamestate):

    # Get fen and Python-Chess board from the given gamestate
    fen = fh.gamestate_to_fen(gamestate)
    board = chess.Board(fen)

    with chess.syzygy.open_tablebase('syzygy') as tablebase:
        if tablebase.get_wdl(board) == 0:
            return True
    return False
