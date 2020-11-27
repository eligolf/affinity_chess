# --------------------------------------------------------------------------------
#                     GUI file running the game
# --------------------------------------------------------------------------------
import gamestate as gs
import settings as s
import ai
import evaluation as e
import fen_handling as fh

import PySimpleGUI as sg
import cProfile
import ctypes
import re
import os
import sys
import copy
import time
import random
import pandas as pd
from playsound import playsound
import contextlib
with contextlib.redirect_stdout(None):
    import pygame


# --------------------------------------------------------------------------------
#                           GUI Class
# --------------------------------------------------------------------------------

class Gui:

    def __init__(self):

        # General
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.display.set_caption(s.title)
        pygame.display.set_icon(s.icon)

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((s.win_width, s.win_height))

        self.ai = ai.Ai()

        # Moves
        self.moves_list = []
        self.latest_move = [(-100, -100, '')]
        self.evaluation = '-'

        # Game parameters
        self.start_fen = s.start_fen

        # Keep track of mouse button presses and mouse movements
        self.is_dragging = False
        self.square_under_mouse = 0
        self.x, self.y = 0, 0
        self.selected_square = 0

        # Start window to get user input for game settings
        self.is_started = False
        self.is_flipped = False
        self.game_mode = 'human'
        self.draw('')
        sg.theme('DarkAmber')
        self.start_pop_up()
        self.is_started = True

        # Init Gamestate and AI
        self.gamestate = gs.GameState(self.start_fen, self.game_mode, self.is_ai_white, self.max_search_depth)

        # Flip board if AI is playing as white
        self.is_flipped = self.is_ai_white if self.game_mode == 'ai' else not self.is_white_turn

        # Flag for when a move is made by the human player
        self.move_made = self.is_ai_white if self.gamestate.is_white_turn else not self.is_ai_white

    def main(self):

        running = True
        while running:

            self.clock.tick(s.fps)

            self.square_under_mouse, col, row = self.get_square_under_mouse()

            # Events happening in GUI
            for event in pygame.event.get():

                # Able to quit GUI
                if event.type == pygame.QUIT:
                    event = pop_up('Quit', 'Are you sure you want to quit?', True)
                    if event == 'Yes':
                        pygame.quit()
                        running = False

                # Mouse events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()

                    if event.button == 1:
                        self.is_dragging = True
                        if self.gamestate.board[self.square_under_mouse][0] == ('w' if self.gamestate.is_white_turn else 'b') and 1 <= col <= 8 and 2 <= row <= 9:
                            self.selected_square = self.square_under_mouse
                        else:
                            self.selected_square = 0
                        self.x, self.y = pygame.mouse.get_pos()[0] - s.sq_size // 2, pygame.mouse.get_pos()[1] - s.sq_size // 2

                    # Button clicks
                    if self.undo_button.collidepoint(pos):
                        self.unmake_a_move()

                    if self.restart_button.collidepoint(pos):
                        self.restart_game()

                    if self.flip_button.collidepoint(pos):
                        self.is_flipped = not self.is_flipped

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.is_dragging = False
                        move = (self.selected_square, self.get_square_under_mouse()[0])
                        valid_moves = self.gamestate.get_valid_moves()
                        for possible_move in valid_moves:

                            # Promotion moves
                            if move == (possible_move[0], possible_move[1]) and possible_move[2] in ['pQ', 'pR', 'pB', 'pN']:
                                self.chose_promotion_piece(possible_move)
                                break

                            # Other moves
                            elif move == (possible_move[0], possible_move[1]) and possible_move[2] not in ['pQ', 'pR', 'pB', 'pN']:
                                self.process_move(possible_move)
                                break

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging:
                        self.x, self.y = pygame.mouse.get_pos()[0] - s.sq_size // 2, pygame.mouse.get_pos()[1] - s.sq_size // 2

                # Keyboard events
                elif event.type == pygame.KEYDOWN:

                    # Unmake move by pressing 'z'-key
                    if event.key == pygame.K_z:
                        self.unmake_a_move()

                    # Restart game with 'r'-key
                    elif event.key == pygame.K_r:
                        self.restart_game()

                    # Flip screen with 'f'-key
                    elif event.key == pygame.K_f:
                        self.is_flipped = not self.is_flipped

            # Draw the screen after human move
            if running:
                self.draw(self.gamestate.get_valid_moves())

            # Check if stalemated/checkmated and stop the game if so
            if self.gamestate.is_check_mate or self.gamestate.is_stale_mate:
                running = False
                game_over_messages(self.gamestate.is_check_mate, self.gamestate.white_wins, self.gamestate.kind_of_stalemate)

            # If move made and game not over, change to AI if that option is chosen.
            if (self.move_made, running, self.game_mode) == (True, True, 'ai'):
                move, self.evaluation = self.ai.ai_make_move(self.gamestate)
                self.process_move(move)
                self.process_eval()

# --------------------------------------------------------------------------------
#                      Draw everything in GUI
# --------------------------------------------------------------------------------

    def draw(self, valid_moves):

        # Background and board edge
        self.screen.blit(s.bg, (0, 0))
        self.screen.blit(s.board_edge, (s.board_offset - 4, s.board_offset - 4))

        # Board
        self.draw_board(valid_moves)

        # Info surface to the right of board with text
        self.draw_info_surface()

        # Buttons
        self.draw_buttons()

        # Update screen
        pygame.display.flip()

    def draw_info_surface(self):

        # Background
        if self.game_mode == 'ai':
            pygame.draw.rect(self.screen, s.info_surface_color, (s.width + s.sq_size, s.board_offset - 4, s.info_width, s.info_height))

        # Text on surface
        self.draw_text()

    def draw_board(self, valid_moves):

        # Letters and numbers
        for char in range(8):
            real_char = 7 - char if self.is_flipped else char
            self.create_text(s.board_letters[char], s.board_font, s.gold, s.board_offset + 0.5*s.sq_size + real_char*s.sq_size, s.win_height - 0.5*s.board_offset, True)
            self.create_text(s.board_numbers[char], s.board_font, s.gold, 0.5*s.board_offset, s.board_offset + 0.5*s.sq_size + s.sq_size*real_char, True)

        # Board
        real_square = 0
        for row in range(12):
            for col in range(10):
                if 2 <= row <= 9 and 1 <= col <= 8:
                    x, y, w = (s.sq_size * (col - 1) + s.board_offset, s.sq_size * (row - 2) + s.board_offset, s.sq_size) if not self.is_flipped \
                         else (s.sq_size * (8 - col) + s.board_offset, s.sq_size * (9 - row) + s.board_offset, s.sq_size)

                    # Squares
                    square = s.dark_square[real_square] if (row + col) % 2 == 0 else s.light_square[real_square]
                    self.screen.blit(square, pygame.Rect(x, y, w, w))
                    real_square += 1

                    # Highlight squares if game is started
                    if self.is_started:
                        self.highlight_squares(valid_moves)

                    # Pieces
                        piece = self.gamestate.board[row * 10 + col]
                    else:
                        piece = s.start_board[row * 10 + col]
                    if piece != '--' and (row * 10 + col != self.selected_square or not self.is_dragging):
                        self.screen.blit(s.images[piece], pygame.Rect(x, y, w, w))

        # Draw dragged piece
        if self.is_started:
            if self.is_dragging and self.gamestate.board[self.selected_square] not in ['--', 'FF']:
                piece = self.gamestate.board[self.selected_square]
                self.screen.blit(s.images[piece], pygame.Rect(self.x, self.y, s.sq_size, s.sq_size))

    def highlight_squares(self, valid_moves):

        # Highlight if king is in check
        if self.gamestate.is_in_check:
            king_pos = self.gamestate.white_king_location if self.gamestate.is_white_turn else self.gamestate.black_king_location
            row, col = (king_pos // 10 - 2, king_pos % 10 - 1) if not self.is_flipped else (9 - king_pos // 10, 8 - king_pos % 10)
            pygame.draw.rect(self.screen, s.check_red, (col * s.sq_size + s.board_offset, row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), 2)

        # Highlight latest move
        start_row, start_col = (self.latest_move[-1][0] // 10 - 2, self.latest_move[-1][0] % 10 - 1) if not self.is_flipped else \
                               (9 - self.latest_move[-1][0] // 10, 8 - self.latest_move[-1][0] % 10)
        end_row, end_col = (self.latest_move[-1][1] // 10 - 2, self.latest_move[-1][1] % 10 - 1) if not self.is_flipped else \
                           (9 - self.latest_move[-1][1] // 10, 8 - self.latest_move[-1][1] % 10)
        pygame.draw.rect(self.screen, s.grey[1], (start_col * s.sq_size + s.board_offset, start_row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), 3)
        pygame.draw.rect(self.screen, s.grey[1], (end_col * s.sq_size + s.board_offset, end_row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), 3)

        # Highlight when dragging a piece
        if self.is_dragging:
            square = self.selected_square
            row, col = (square // 10 - 2, square % 10 - 1) if not self.is_flipped else \
                       (9 - square // 10, 8 - square % 10)

            # Selected square
            if self.gamestate.board[square][0] == ('w' if self.gamestate.is_white_turn else 'b'):
                pygame.draw.rect(self.screen, s.orange, (col * s.sq_size + s.board_offset, row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), 4)

            # Possible moves
            for move in valid_moves:
                if move[0] == square:
                    row, col = (move[1] // 10 - 2, move[1] % 10 - 1) if not self.is_flipped else \
                               (9 - move[1] // 10, 8 - move[1] % 10)
                    pygame.draw.rect(self.screen, s.green, (col * s.sq_size + s.board_offset, row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), 4)

    def create_buttons(self, text, font, color, x, y):
        text = font.render(text, True, color)
        rect = text.get_rect()
        rect.center = (x, y)

        box = (rect[0] - s.sq_size/10, rect[1] - s.sq_size/10 / 2, rect[2] + s.sq_size/10 * 2, rect[3] + s.sq_size/10)
        pygame.draw.rect(self.screen, s.info_surface_color, box, int(s.sq_size/20 / 2))
        self.screen.blit(text, rect)

        return text, rect

    def create_text(self, text, font, color, x, y, center):
        text = font.render(text, True, color)
        rect = text.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.midleft = (x, y)
        self.screen.blit(text, rect)

    def draw_buttons(self):

        self.restart_text, self.restart_button = self.create_buttons('Restart', s.large_font, s.large_color, 1.25*s.width, 0.86*s.height)
        self.flip_text, self.flip_button = self.create_buttons('Flip Board', s.large_font, s.large_color, 1.25*s.width, 0.93*s.height)
        self.undo_text, self.undo_button = self.create_buttons('Undo move', s.large_font, s.large_color, 1.25*s.width, s.height)

    def draw_text(self):

        # AI-related prints
        if self.game_mode == 'ai':
            self.create_text('AI info', s.title_font, s.black, 1.14*s.width*1.05, 0.75*s.sq_size, False)
            self.create_text(f'Level: {s.level[self.max_search_depth]}', s.info_font, s.black, 1.14*s.width, 0.75*1.4*s.sq_size, False)
            self.create_text(f'Depth: {self.ai.max_depth}', s.info_font, s.black, 1.14*s.width, 0.75 * 1.8 * s.sq_size, False)
            self.create_text(f'Eval: {self.evaluation}', s.info_font, s.black, 1.14*s.width, 0.75*2.2*s.sq_size, False)

    def process_eval(self):

        if self.ai.is_in_opening:
            self.evaluation = 'Opening'
        else:
            if self.evaluation > 1e6:
                self.evaluation = 'AI wins'
            elif self.evaluation < -1e6:
                self.evaluation = 'Human wins'
            else:
                self.evaluation = round(self.evaluation / 100, 2)

# --------------------------------------------------------------------------------
#               Helper functions
# --------------------------------------------------------------------------------

    def process_move(self, move):

        # Make the move and update move info
        self.gamestate.make_move(move[0], move[1], move[2])
        self.gamestate.move_counter += 0.5  # Increase move counter
        self.latest_move.append(move)
        self.add_move_to_list(move[0], move[1])  # Add move to list of made moves

        # Play a sound when a move is made
        if s.toggle_sound:
            sound = pygame.mixer.Sound('sounds/capture.wav') if self.gamestate.piece_captured != '--' else pygame.mixer.Sound('sounds/move.wav')
            sound.play()

        # Evaluate current position after the move is made and print the result
        if s.static_evaluation:
            evaluation = e.evaluate(self.gamestate)
            print('(Static evaluation for ' + ('white: ' if not self.gamestate.is_white_turn else 'black: ') + str(evaluation if self.gamestate.is_white_turn else -evaluation) + ')')

        # Flip board if human vs human and if board is not already flipped in the right direction for player turn
        if self.game_mode == 'human':
            if (self.gamestate.is_white_turn and self.is_flipped) or (not self.gamestate.is_white_turn and not self.is_flipped):
                self.is_flipped = not self.is_flipped

        # Change move made variable
        self.move_made = not self.move_made

    def unmake_a_move(self):

        # Can't redo engines first move
        moves_made = 2 if self.is_ai_white else 1

        if len(self.gamestate.move_log) > moves_made:

            # Unmake twice if playing against the AI
            undo_move = 1 if self.game_mode == 'human' else 2

            for undo in range(0, undo_move):
                self.gamestate.move_counter -= 0.5
                self.moves_list.pop()

                self.gamestate.unmake_move()
                self.latest_move.pop()
                if self.game_mode == 'human':
                    if (self.gamestate.is_white_turn and self.is_flipped) or (not self.gamestate.is_white_turn and not self.is_flipped):
                        self.is_flipped = not self.is_flipped

    def restart_game(self):
        event = pop_up('Restart game', 'Are you sure you want to restart?', True)
        if event == 'Yes':
            Gui().main()

    def add_move_to_list(self, start_square, end_square):

        text = self.return_move_as_string(start_square, end_square)

        if float(self.gamestate.move_counter % 1000).is_integer():
            move_text = ' ' + str(int(self.gamestate.move_counter)) + '.' + text
        else:
            move_text = ' ' + text

        self.moves_list.append(move_text)

    def return_move_as_string(self, start_square, end_square):

        # Get the squares corresponding row and col
        start_row, start_col = start_square // 10 - 2, start_square % 10 - 1
        end_row, end_col = end_square // 10 - 2, end_square % 10 - 1

        # Check if last move was to take a piece
        piece_taken = True if self.gamestate.piece_captured != '--' else False

        # The piece that is moving
        piece = self.gamestate.piece_moved[1]

        # If same type of piece can reach same square, add some extra info
        letter = number = False
        extra_info = ''

        if piece != 'p':
            for move in self.gamestate.possible_moves:
                if move[1] == end_square and piece == self.gamestate.board[move[0]][1]:
                    if start_square // 10 in [move[0] // 10, move[1] // 10]:
                        letter = True
                    if start_square % 10 in [move[0] % 10, move[1] % 10]:
                        number = True
        if letter:
            extra_info = str(s.fen_letters_ep[start_square % 10])
        if number:
            extra_info += str(s.square_to_row[start_square // 10])

        # Pawn
        if piece == 'p':
            if piece_taken:
                text = s.letters[start_col] + 'x' + s.letters[end_col] + s.numbers[7-end_row]
            else:
                text = s.letters[end_col] + s.numbers[7-end_row]

            # Promotion
            if self.gamestate.move_log[-1][0][2] in ['pQ', 'pR', 'pB', 'pN']:
                promoted_piece = self.gamestate.move_log[-1][0][2][1]
                text += f'={promoted_piece}'

        # Other pieces
        else:
            if piece_taken:
                text = piece + extra_info + 'x' + s.letters[end_col] + s.numbers[7-end_row]
            else:
                text = piece + extra_info + s.letters[end_col] + s.numbers[7-end_row]

            # Castling
            if self.gamestate.move_log[-1][0][2] == 'ck':
                text = 'O-O'
            elif self.gamestate.move_log[-1][0][2] == 'cq':
                text = 'O-O-O'

        # Check if the move resulted in a check
        self.gamestate.get_valid_moves()
        if self.gamestate.is_in_check:
            text += '+'
        if self.gamestate.is_check_mate:
            text += '#'

        return text

    def get_square_under_mouse(self):
        pos = pygame.mouse.get_pos()  # (x, y) location of click
        col, row = ((pos[0] + s.sq_size - s.board_offset) // s.sq_size, (pos[1] + 2 * s.sq_size - s.board_offset) // s.sq_size) if not self.is_flipped \
            else (9 - (pos[0] + s.sq_size - s.board_offset) // s.sq_size, 11 - (pos[1] + 2 * s.sq_size - s.board_offset) // s.sq_size)  # Get corresponding square in chess board

        square_under_mouse = row * 10 + col  # Get corresponding square on the 10x12 board

        return square_under_mouse, col, row

    def chose_promotion_piece(self, possible_move):
        event, values = sg.Window('', [[sg.Text('Promote to:')],
                                       [sg.Listbox(['Q', 'R', 'B', 'N'], size=(20, 4), key='LB')],
                                       [sg.Button('Ok'), sg.Button('Cancel')]]).read(close=True)
        if event == 'Ok':
            move_type = f'p{values["LB"][0][0]}'
            self.process_move((possible_move[0], possible_move[1], move_type))

    def start_pop_up(self, wrong_fen=False):
        if wrong_fen:
            layout = [[sg.Text('')],
                      [sg.Text('Start FEN (Optional): ', size=(15, 1)), sg.InputText(size=(60, 1), key='fen')],
                      [sg.Text('Please enter a valid FEN, or leave empty for start position.', text_color='red')],
                      [sg.Text('')],
                      [sg.Text('Opponent:  '), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai'), sg.Radio('Human', '1', size=(5, 1), key='human')],
                      [sg.Text('Play as:     '), sg.Radio('White', '2', default=True, size=(5, 1), key='white'), sg.Radio('Black', '2', key='black')],
                      [sg.Text('AI strength:'), sg.Radio('Strong', '3', default=True, size=(5, 1), key='strong'), sg.Radio('Medium', '3', key='medium'), sg.Radio('Easy', '3', key='easy')],
                      [sg.Text('')],
                      [sg.Submit()]]
        else:
            layout = [[sg.Text('')],
                      [sg.Text('Start FEN (Optional): ', size=(15, 1)), sg.InputText(size=(60, 1), key='fen')],
                      [sg.Text('')],
                      [sg.Text('Opponent:  '), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai'), sg.Radio('Human', '1', size=(5, 1), key='human')],
                      [sg.Text('Play as:     '), sg.Radio('White', '2', default=True, size=(5, 1), key='white'), sg.Radio('Black', '2', key='black')],
                      [sg.Text('AI strength:'), sg.Radio('Strong', '3', default=True, size=(5, 1), key='strong'), sg.Radio('Medium', '3', key='medium'), sg.Radio('Easy', '3', key='easy')],
                      [sg.Text('')],
                      [sg.Submit(pad=(10, 18))]]

        window = sg.Window('Please chose start settings', layout)
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            self.game_mode = 'ai'
            self.is_ai_white = False
            self.max_search_depth = s.max_search_depth_strong
        if values['ai']:
            self.game_mode = 'ai'
        if values['human']:
            self.game_mode = 'human'
        if values['white']:
            self.is_ai_white = False
        if values['black']:
            self.is_ai_white = True
        if values['strong']:
            self.max_search_depth = s.max_search_depth_strong
        if values['medium']:
            self.max_search_depth = s.max_search_depth_medium
        if values['easy']:
            self.max_search_depth = s.max_search_depth_easy
        if values['fen']:
            if fh.test_fen(str(values['fen'])):
                self.start_fen = str(values['fen'])
                self.is_white_turn = True if 'w' in self.start_fen else False
            else:
                window.close()
                self.start_pop_up(True)
        else:
            self.is_white_turn = True

        window.close()


# --------------------------------------------------------------------------------
#                          Static functions
# --------------------------------------------------------------------------------

def pop_up(title, message, question):
    if question:
        layout = [[sg.Text(message, pad=(10, 10))],
                  [sg.Button('Yes', pad=(10, 10)), sg.Button('No', pad=(10, 10))]]
        window = sg.Window(title, layout, size=(350, 100))
        event, values = window.read()
        window.close()
        return event
    else:
        layout = [[sg.Text(message)],
                  [sg.Button('Ok')]]
        window = sg.Window(title, layout)
        window.close()


def game_over_messages(checkmate, white_wins, stalemate_type):

    if checkmate:
        winner = 'white' if white_wins else 'black'
        event = pop_up('Checkmate', f'Checkmate, {winner} won! Do you want to play again?', True)
        if event == 'Yes':
            Gui().main()
        else:
            pygame.quit()
    else:
        event = pop_up(stalemate_type, 'Game drawn! Do you want to play again?', True)
        if event == 'Yes':
            Gui().main()
        else:
            pygame.quit()

# --------------------------------------------------------------------------------
#                         Run the game
# --------------------------------------------------------------------------------


if __name__ == '__main__':

    # Set the correct icon in Windows taskbar
    myappid = u'_'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # If timing a game, run the cProfile module. Else run normally.
    if s.timing:
        pr = cProfile.Profile()
        pr.enable()
        Gui().main()
        pr.disable()
        pr.print_stats(sort=s.timing_sort)
    else:
        Gui().main()
