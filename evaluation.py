#  --------------------------------------------------------------------------------
#                 Evaluates a given board and returns a score
#  --------------------------------------------------------------------------------
import settings as s


def evaluate(gamestate, depth):

    # Initialize scores and other parameters
    white_score = black_score = 0

    # If check mate return large value, if draw return 0.
    if gamestate.is_check_mate:
        return 1e9 + depth if gamestate.is_white_turn else -1e9 - depth
    if gamestate.is_stale_mate:
        return 0

    white_score += gamestate.piece_values[0]
    black_score += gamestate.piece_values[1]

    # Give bonus for bishop pair
    if gamestate.piece_dict[0]['B'] == 2:
        white_score += s.bishop_pair_bonus
    if gamestate.piece_dict[1]['B'] == 2:
        black_score += s.bishop_pair_bonus

    # Double pawn punishment
    white_pawns, black_pawns = set(gamestate.pawn_columns_list[0]), set(gamestate.pawn_columns_list[1])
    white_score += (len(gamestate.pawn_columns_list[0]) - len(white_pawns)) * s.double_pawn_punishment
    black_score += (len(gamestate.pawn_columns_list[1]) - len(black_pawns)) * s.double_pawn_punishment

    # Isolated pawn punishment
    white_score += len([i for i in white_pawns if i - 1 not in white_pawns and i + 1 not in white_pawns]) * s.isolated_pawn_punishment
    black_score += len([i for i in black_pawns if i - 1 not in black_pawns and i + 1 not in black_pawns]) * s.isolated_pawn_punishment

    # Rook on open and semi-open file bonus
    for rook in gamestate.rook_columns_list[0]:
        if rook not in white_pawns:
            white_score += s.rook_on_semi_open_file_bonus
            if rook not in black_pawns:
                white_score += s.rook_on_open_file_bonus
    for rook in gamestate.rook_columns_list[1]:
        if rook not in black_pawns:
            black_score += s.rook_on_semi_open_file_bonus
            if rook not in white_pawns:
                black_score += s.rook_on_open_file_bonus

    # Opening dependent bonuses/punishment
    if len(gamestate.move_log) < 30:

        # Punishment for pieces in front of d and e pawns
        if gamestate.board[84] == 'wp' and gamestate.board[74] != '--':
            white_score += s.blocking_d_e_pawn_punishment
        if gamestate.board[85] == 'wp' and gamestate.board[75] != '--':
            white_score += s.blocking_d_e_pawn_punishment
        if gamestate.board[34] == 'bp' and gamestate.board[44] != '--':
            black_score += s.blocking_d_e_pawn_punishment
        if gamestate.board[34] == 'bp' and gamestate.board[44] != '--':
            black_score += s.blocking_d_e_pawn_punishment

    # Bonus for attacking squares around the enemy king

    # Endgame related functions
    if gamestate.endgame == 1:

        # Knights are worth slightly less in endgame
        white_score += gamestate.piece_dict[0]['N'] * s.knight_endgame_punishment
        black_score += gamestate.piece_dict[1]['N'] * s.knight_endgame_punishment

        # Bishops are worth slightly more in endgame
        white_score += gamestate.piece_dict[0]['B'] * s.bishop_endgame_bonus
        black_score += gamestate.piece_dict[1]['B'] * s.bishop_endgame_bonus

        # Move towards the other king if the other side has no queen and rooks, and you have queen or rooks
        # Also no pawns on the board
        if gamestate.piece_dict[0]['p'] == 0 and gamestate.piece_dict[1]['p'] == 0:

            # White advantage
            if gamestate.piece_dict[1]['R'] == 0 and gamestate.piece_dict[1]['Q'] == 0:
                if gamestate.piece_dict[0]['R'] >= 1 or gamestate.piece_dict[0]['Q'] >= 1:
                    white_score += (14 - gamestate.kings_distance) * 4
            # Black advantage
            elif gamestate.piece_dict[0]['R'] == 0 and gamestate.piece_dict[0]['Q'] == 0:
                if gamestate.piece_dict[1]['R'] >= 1 or gamestate.piece_dict[1]['Q'] >= 1:
                    black_score += (14 - gamestate.kings_distance) * 4

    return black_score - white_score
