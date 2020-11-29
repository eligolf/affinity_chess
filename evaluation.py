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

# -------------------------------------------------------------------------------------------------
#                          Up until endgame evaluation
# -------------------------------------------------------------------------------------------------

    if gamestate.midgame:

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

        # Piece values with base and piece-dependent values (updated in make/unmake move functions)
        white_score += gamestate.piece_values[0]
        black_score += gamestate.piece_values[1]

        # Bishop pair bonus
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

        # Bonus for attacking squares around the enemy king
        # ........

# -------------------------------------------------------------------------------------------------
#                         Endgame related functions (gamestate.endgame == 1)
# -------------------------------------------------------------------------------------------------

    else:

        # Knights are worth slightly less in endgame
        white_score += gamestate.piece_dict[0]['N'] * s.knight_endgame_punishment
        black_score += gamestate.piece_dict[1]['N'] * s.knight_endgame_punishment

        # Bishops are worth slightly more in endgame
        white_score += gamestate.piece_dict[0]['B'] * s.bishop_endgame_bonus
        black_score += gamestate.piece_dict[1]['B'] * s.bishop_endgame_bonus

        # Finding mate with no pawns on the board.
        if gamestate.piece_dict[0]['p'] == gamestate.piece_dict[1]['p'] == 0:

            # Add a small term for piece values, otherwise it sometimes sacrificed a piece for no reason.
            white_score = 0.05*gamestate.piece_values[0]
            black_score = 0.05*gamestate.piece_values[1]

            # White advantage (no rooks or queens on enemy side and a winning advantage)
            if gamestate.piece_dict[1]['R'] == gamestate.piece_dict[1]['Q'] == 0 and white_score > black_score:

                # Lone K vs K and (R, Q and/or at least 2xB). Only using mop-up evaluation (https://www.chessprogramming.org/Mop-up_Evaluation).
                if gamestate.piece_dict[0]['R'] >= 1 or gamestate.piece_dict[0]['Q'] >= 1 or gamestate.piece_dict[0]['B'] >= 2:
                    black_king_real_pos = s.real_board_squares.index(gamestate.black_king_location)
                    white_score += 4.7 * s.manhattan_distance[black_king_real_pos] + 1.6 * (14 - gamestate.kings_distance)

                # Lone K vs K, N and B
                if gamestate.piece_dict[0]['R'] == gamestate.piece_dict[0]['Q'] == 0 and gamestate.piece_dict[0]['B'] >= 1 and gamestate.piece_dict[0]['N'] >= 1:
                    pass

            # Black advantage (no rooks or queens on enemy side and a winning advantage)
            if gamestate.piece_dict[0]['R'] == gamestate.piece_dict[0]['Q'] == 0 and black_score > white_score:

                # Lone K vs K and (R, Q and/or at least 2xB). Only using mop-up evaluation (https://www.chessprogramming.org/Mop-up_Evaluation).
                if gamestate.piece_dict[1]['R'] >= 1 or gamestate.piece_dict[1]['Q'] >= 1 or gamestate.piece_dict[1]['B'] >= 2:
                    white_king_real_pos = s.real_board_squares.index(gamestate.white_king_location)
                    black_score += 4.7 * s.manhattan_distance[white_king_real_pos] + 1.6 * (14 - gamestate.kings_distance)

                # Lone K vs K, N and B
                if gamestate.piece_dict[1]['R'] == gamestate.piece_dict[1]['Q'] == 0 and gamestate.piece_dict[1]['B'] >= 1 and gamestate.piece_dict[1]['N'] >= 1:
                    pass

    return black_score - white_score
