import chess
import chess.syzygy

import fen_handling as fh


def find_endgame_move(gamestate):

    # Get fen and Python-Chess board from the given gamestate
    fen = fh.gamestate_to_fen(gamestate)
    board = chess.Board(fen)

    with chess.syzygy.open_tablebase('syzygy') as tablebase:
        best_dtz = tablebase.get_dtz(board)
        best_wdl = tablebase.get_wdl(board)

    # If finding a winning position in the tablebases, find the move that lowers the distance to zero (DTZ)
    if best_wdl in (1, 2):

        # Find all possible moves and try them to see if it lowers original dtz
        valid_moves = gamestate.get_valid_moves()
        best_move = valid_moves[0]
        for move in valid_moves:

            piece_captured = gamestate.board[move[1]]
            gamestate.make_move(move)
            fen = fh.gamestate_to_fen(gamestate)
            board = chess.Board(fen)

            with chess.syzygy.open_tablebase('syzygy') as tablebase:
                new_dtz = tablebase.get_dtz(board)
                new_wdl = tablebase.get_wdl(board)

            # If winning position
            if new_wdl in (-1, -2):
                # If finding winning capture or pawn move, play that immediately
                if gamestate.piece_moved[1] == 'p' or piece_captured != '--':
                    gamestate.unmake_move()
                    return move, 1e9, best_dtz
                else:
                    if abs(new_dtz) <= abs(best_dtz):
                        best_dtz = new_dtz
                        best_move = move

            gamestate.unmake_move()

        return best_move, 1e9, best_dtz

    # If finding a losing position in the tablebases, try to play as difficult as possible
    if best_wdl in (-1, -2):

        # Find all possible moves and try them to see if it lowers original dtz
        valid_moves = gamestate.get_valid_moves()
        best_dtz = 0
        for move in valid_moves:

            gamestate.make_move(move)
            fen = fh.gamestate_to_fen(gamestate)
            board = chess.Board(fen)

            with chess.syzygy.open_tablebase('syzygy') as tablebase:
                new_dtz = tablebase.get_dtz(board)
                new_wdl = tablebase.get_wdl(board)

            # If suddenly winning, play that immediately
            if new_wdl in (0, -1, -2):
                gamestate.unmake_move()
                return move, -1e9, best_dtz

            # Else maximize DTZ
            if new_wdl in (1, 2):
                if abs(new_dtz) > abs(best_dtz):
                    best_dtz = new_dtz
                    best_move = move

            gamestate.unmake_move()

        return best_move, -1e9, best_dtz

    # If draw, find move that makes it winning, or keeps drawing
    if best_wdl == 0:

        # Find all possible moves and try them to see if it lowers original dtz
        valid_moves = gamestate.get_valid_moves()
        for move in valid_moves:

            gamestate.make_move(move)
            fen = fh.gamestate_to_fen(gamestate)
            board = chess.Board(fen)

            with chess.syzygy.open_tablebase('syzygy') as tablebase:
                new_wdl = tablebase.get_wdl(board)

            # If suddenly winning, play that immediately
            if new_wdl in (-1, -2):
                gamestate.unmake_move()
                return move, 0, 10

            # Else if finding a move that keeps eval at 0, save that move and play if not finding a winning move
            elif new_wdl == 0:
                best_move = move

            gamestate.unmake_move()

        return best_move, 0, 10

    return None, None
