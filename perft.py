import board as b


def perft(depth: int, board: chess.Board) -> int:
    if depth == 1:
        return board.get_possible_moves().count()
    elif depth > 1:
        count = 0

        for move in board.get_possible_moves():
            board.make_move(move)
            count += perft(depth - 1, board)
            board.unmake_move()

        return count
    else:
        return 1

gamestate = b.GameState()
counter = perft(a, 3, 0)
print(counter)
