# --------------------------------------------------------------------------------
#           Creating FEN from a board, or extracts the board from a FEN
# --------------------------------------------------------------------------------
import settings as s


def run_fen_to_board(fen):
    correct_fen = test_fen(fen)
    if not correct_fen:
        print('Incorrect FEN format, please chose a valid FEN')
        return None
    else:
        return fen_to_board(fen)


def test_fen(fen):

    # Test if a value is given at all
    if not fen:
        return False

    # Test board representation
    fen_board = fen.split(' ')[0]
    number = 0
    for item in fen_board:
        if item.isdigit():
            number = number + int(item)        
        elif item in 'pnbrqkPNBRQK':
            number += 1         
        elif item == '/':
            if number != 8:
                return False
            number = 0       
        else:
            return False

    # Test turn to move
    try:
        if fen.split(' ')[1] not in 'wb':
            return False
    except:
        return False

    # Test castling rights
    try:
        rights = fen.split(' ')[2]
        if not 0 < len(rights) <= 4:
            return False
        for right in rights:
            if right not in 'KQkq-':
                return False
    except:
        return False

    # Test enpassant square
    try:
        ep_square = fen.split(' ')[3]
        if not ep_square:
            return False
        if ep_square[0] not in '-abcdefgh':
            return False
        if len(ep_square) == 2:
            if ep_square[1] not in '3, 6':
                return False
        if len(ep_square) > 2:
            return False
    except:
        return False
        
    # If all conditions are good, return True
    return True


def fen_to_board(fen):

    # Gamestate variables:
    # Turn to move
    is_white_turn = True if 'w' in fen.split(' ')[1] else False

    # Castling rights
    castling_rights = [False, False, False, False]
    rights = fen.split(' ')[2]
    if 'K' in rights:
        castling_rights[0] = True
    if 'Q' in rights:
        castling_rights[1] = True
    if 'k' in rights:
        castling_rights[2] = True
    if 'q' in rights:
        castling_rights[3] = True

    # Enpassant square
    if fen.split(' ')[3] != '-':
        ep_square = int(s.fen_numbers[fen.split(' ')[3][1]] + s.fen_letters[fen.split(' ')[3][0]])
    else:
        ep_square = None

    # Get the board
    board = {}
    for square in range(120):
        if square in s.real_board_squares:
            board[square] = '--'
        else:
            board[square] = 'FF'

    # Remove the move counters at the end of the FEN if exists
    if fen[-1][0].isnumeric():
        fen = ' '.join(fen.split(' ')[:-2])

    # Extract the board representation and remove dashes
    fen_board_temp = fen.split(' ')[0]
    fen_board = fen_board_temp.replace('/', '')

    # Loop through the board representation
    number = 0
    for item in fen_board:

        # If it is a number, go corresponding numbers ahead in squares
        if item.isdigit():
            number = number + int(item)
        else:
            square = s.real_board_squares[number]
            board[square] = s.fen_to_piece[item]
            number += 1

    return board, castling_rights, ep_square, 0, is_white_turn


def gamestate_to_fen(board):

    # Go through board to find where all the pieces are located
    fen = ''
    number = 0
    temp_number = 0
    for square in board:
        if square != 'FF':
            if square == '--':
                temp_number += 1
                number += 1
            else:
                if temp_number:
                    fen += str(temp_number)
                    temp_number = 0
                fen += piece_to_fen[square]
                number += 1
            if number == 8:
                if temp_number:
                    fen += str(temp_number)
                fen += '/'
                number = temp_number = 0
                
    # Remove last '/'
    fen = fen[:-1]

    # Turn to move
    fen += ' w ' if is_white_turn else ' b '

    # Castling rights
    if castling_rights[0]:
        fen += 'K'
    if castling_rights[1]:
        fen += 'Q'
    if castling_rights[2]:
        fen += 'k'
    if castling_rights[3]:
        fen += 'q'

    # Enpassant square
    if not ep_square:
        fen += ' -'
    else:
        print(ep_square // 10, ep_square % 10)
        fen += ' ' + s.fen_letters_ep[ep_square % 10] + s.fen_numbers_ep[ep_square // 10]
                
    # Halfmove clock
    fen += ' ' + str(halfmove_clock)

    # Move counter
    fen += ' ' + str(move_counter)
            
    return fen





