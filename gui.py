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
import os
import sys
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
        self.is_started = self.running = True

        # Init Gamestate and AI
        self.gamestate = gs.GameState(self.start_fen, self.game_mode, self.is_ai_white, self.max_search_depth)

        # Flip board if AI is playing as white
        self.is_flipped = self.is_ai_white if self.game_mode == 'ai' else not self.is_white_turn

        # Flag for when a move is made by the human player
        self.move_made = self.is_ai_white if self.gamestate.is_white_turn else not self.is_ai_white

    def main(self):

        while self.running:

            self.clock.tick(s.fps)

            self.square_under_mouse, col, row = self.get_square_under_mouse()

            # Events happening in GUI
            for event in pygame.event.get():

                # Mouse events
                if event.type == pygame.MOUSEBUTTONDOWN:
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
            if self.running:
                self.draw(self.gamestate.get_valid_moves())

            # Able to quit GUI
            if event.type == pygame.QUIT:
                event = pop_up('Quit', 'Are you sure you want to quit?', True)
                if event == 'Yes':
                    pygame.quit()
                    self.running = False

            # Check if stalemated/checkmated and stop the game if so
            if self.gamestate.is_check_mate or self.gamestate.is_stale_mate:
                self.game_over_messages()

            # If move made and game not over, change to AI if that option is chosen.
            if (self.move_made, self.running, self.game_mode) == (True, True, 'ai'):
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
            self.screen.blit(s.info_edge, (s.width + s.sq_size - 4, 0.6 * s.height - 4))
            self.screen.blit(s.info_image, (s.width + s.sq_size, 0.6*s.height))

        # Text on surface
        self.draw_text()

    def draw_board(self, valid_moves):

        # Letters and numbers
        for char in range(8):
            real_char = 7 - char if self.is_flipped else char
            self.create_text(s.board_letters[char], s.board_font, s.gold, s.board_offset + 0.5*s.sq_size + real_char*s.sq_size, s.win_height - 0.5*s.board_offset, True)
            self.create_text(s.board_numbers[char], s.board_font, s.gold, 0.5*s.board_offset, s.board_offset + 0.5*s.sq_size + s.sq_size*real_char, True)

        # Board
        self.draw_on_squares(False)

        # Highlight squares if game is started
        if self.is_started:
            self.highlight_squares(valid_moves)

        # Pieces
        self.draw_on_squares(True)

        # Draw dragged piece
        if self.is_started:
            if self.is_dragging and self.gamestate.board[self.selected_square] not in ['--', 'FF']:
                piece = self.gamestate.board[self.selected_square]
                self.screen.blit(s.images[piece], pygame.Rect(self.x, self.y, s.sq_size, s.sq_size))

    def draw_on_squares(self, piece_drawing):

        real_square = 0
        for row in range(12):
            for col in range(10):
                if 2 <= row <= 9 and 1 <= col <= 8:
                    x, y, w = (s.sq_size * (col - 1) + s.board_offset, s.sq_size * (row - 2) + s.board_offset, s.sq_size) if not self.is_flipped \
                        else (s.sq_size * (8 - col) + s.board_offset, s.sq_size * (9 - row) + s.board_offset, s.sq_size)

                    if piece_drawing:
                        # Pieces
                        if self.is_started:
                            piece = self.gamestate.board[row * 10 + col]
                        else:
                            piece = s.start_board[row * 10 + col]
                        if piece != '--' and (row * 10 + col != self.selected_square or not self.is_dragging):
                            self.screen.blit(s.images[piece], pygame.Rect(x, y, w, w))
                    else:
                        # Squares
                        square = s.dark_square[real_square] if (row + col) % 2 == 0 else s.light_square[real_square]
                        self.screen.blit(square, pygame.Rect(x, y, w, w))
                        real_square += 1

    def highlight_squares(self, valid_moves):

        # Highlight if king is in check
        if self.gamestate.is_in_check:
            king_pos = self.gamestate.white_king_location if self.gamestate.is_white_turn else self.gamestate.black_king_location
            row, col = (king_pos // 10 - 2, king_pos % 10 - 1) if not self.is_flipped else (9 - king_pos // 10, 8 - king_pos % 10)
            self.draw_highlighting(s.check_red, s.check_red_t, col, row, 1)

        # Highlight latest move
        start_row, start_col = (self.latest_move[-1][0] // 10 - 2, self.latest_move[-1][0] % 10 - 1) if not self.is_flipped else \
                               (9 - self.latest_move[-1][0] // 10, 8 - self.latest_move[-1][0] % 10)
        end_row, end_col = (self.latest_move[-1][1] // 10 - 2, self.latest_move[-1][1] % 10 - 1) if not self.is_flipped else \
                           (9 - self.latest_move[-1][1] // 10, 8 - self.latest_move[-1][1] % 10)
        self.draw_highlighting(s.grey[1], s.grey_t[1], start_col, start_row, 1)
        self.draw_highlighting(s.grey[1], s.grey_t[1], end_col, end_row, 1)

        # Highlight when dragging a piece
        if self.is_dragging:
            square = self.selected_square
            row, col = (square // 10 - 2, square % 10 - 1) if not self.is_flipped else \
                       (9 - square // 10, 8 - square % 10)

            # Selected square
            if self.gamestate.board[square][0] == ('w' if self.gamestate.is_white_turn else 'b'):
                self.draw_highlighting(s.orange, s.orange_t, col, row, 1)

            # Possible moves
            for move in valid_moves:
                if move[0] == square:
                    row, col = (move[1] // 10 - 2, move[1] % 10 - 1) if not self.is_flipped else \
                               (9 - move[1] // 10, 8 - move[1] % 10)
                    self.draw_highlighting(s.green, s.green_t, col, row, 1)

    def draw_highlighting(self, color, color_t, col, row, thickness):
        surface = pygame.Surface((s.sq_size, s.sq_size), pygame.SRCALPHA)
        surface.fill(color_t)
        self.screen.blit(surface, (col * s.sq_size + s.board_offset, row * s.sq_size + s.board_offset))
        pygame.draw.rect(self.screen, color, (col * s.sq_size + s.board_offset, row * s.sq_size + s.board_offset, s.sq_size, s.sq_size), thickness, border_radius=1)

    def create_buttons(self, text, font, color, x, y):
        text = font.render(text, True, color)
        rect = text.get_rect()
        rect.center = (x, y)

        box = (rect[0] - s.sq_size/10, rect[1] - s.sq_size/10 / 2, rect[2] + s.sq_size/10 * 2, rect[3] + s.sq_size/10)
        pygame.draw.rect(self.screen, s.gold, box, 1)
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

        self.restart_text, self.restart_button = self.create_buttons('Restart', s.large_font, s.large_color, 1.25*s.width, 0.88*s.height)
        self.flip_text, self.flip_button = self.create_buttons('Flip Board', s.large_font, s.large_color, 1.25*s.width, 0.95*s.height)
        self.undo_text, self.undo_button = self.create_buttons('Undo move', s.large_font, s.large_color, 1.25*s.width, 1.02*s.height)

    def draw_text(self):

        # AI-related prints
        if self.game_mode == 'ai':

            # See if depth is reduced since quiescence search is not implemented
            if self.ai.real_depth != self.ai.max_depth:
                depth = f'Depth: {self.ai.max_depth} ({self.ai.real_depth})'
            else:
                depth = f'Depth: {self.ai.max_depth}'

            self.create_text('AI info', s.title_font, s.black, 1.2*s.width, 0.63*s.height, False)
            self.create_text(f'Level: {s.level[self.max_search_depth]}', s.info_font, s.black, 1.14*s.width, 0.63*s.height + 0.3*s.sq_size, False)
            self.create_text(depth, s.info_font, s.black, 1.14*s.width, 0.63*s.height + 0.58*s.sq_size, False)
            self.create_text(f'Eval: {self.evaluation}', s.info_font, s.black, 1.14*s.width, 0.63*s.height + 0.86*s.sq_size, False)
            self.create_text(f'Time: {round(self.ai.timer, 2)} s', s.info_font, s.black, 1.14 * s.width, 0.63 * s.height + 1.14*s.sq_size, False)

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
        self.gamestate.make_move(move)
        self.gamestate.move_counter += 0.5  # Increase move counter
        self.latest_move.append(move)
        self.add_move_to_list(move[0], move[1])  # Add move to list of made moves

        # Play a sound when a move is made
        if s.toggle_sound:
            sound = pygame.mixer.Sound('sounds/capture.wav') if self.gamestate.piece_captured != '--' else pygame.mixer.Sound('sounds/move.wav')
            sound.play()

        # Evaluate current position after the move is made and print the result
        if s.static_evaluation:
            evaluation = e.evaluate(self.gamestate, 0)
            print('(Static evaluation for ' + ('white: ' if not self.gamestate.is_white_turn else 'black: ') + str(evaluation if self.gamestate.is_white_turn else -evaluation) + ')')

        # Flip board if human vs human and if board is not already flipped in the right direction for player turn
        if self.game_mode == 'human':
            if (self.gamestate.is_white_turn and self.is_flipped) or (not self.gamestate.is_white_turn and not self.is_flipped):
                self.is_flipped = not self.is_flipped

        # Change move made variable
        self.move_made = not self.move_made

    def unmake_a_move(self):

        # Can't redo engines first move
        moves_made = 1 if (not self.is_ai_white or (not self.gamestate.is_ai_white and len(self.gamestate.move_log) == 2)) else 2

        if len(self.gamestate.move_log) > moves_made and not (not self.gamestate.is_ai_white and self.game_mode == 'ai' and len(self.gamestate.move_log) == 2):

            # Unmake twice if playing against the AI, if AI is black
            undo_move = 1 if self.game_mode == 'human' else 2

            for undo in range(0, undo_move):
                self.gamestate.move_counter -= 0.5
                self.moves_list.pop()

                self.gamestate.unmake_move()
                self.latest_move.pop()
                if self.game_mode == 'human':
                    if (self.gamestate.is_white_turn and self.is_flipped) or (not self.gamestate.is_white_turn and not self.is_flipped):
                        self.is_flipped = not self.is_flipped

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
            else (9 - (pos[0] + s.sq_size - s.board_offset) // s.sq_size, 11 - (pos[1] + 2 * s.sq_size - s.board_offset) // s.sq_size)  # Get corresponding square on chess board

        square_under_mouse = row * 10 + col  # Get corresponding square on the 10x12 board

        return square_under_mouse, col, row

    def restart_game(self):
        event = pop_up('Restart game', 'Are you sure you want to restart?', True)
        if event == 'Yes':
            self.running = False
            Gui().main()

    def game_over_messages(self):

        if self.gamestate.is_check_mate:
            event = pop_up('Checkmate', 'Checkmate! Do you want to play again?', True)
            self.running = False
            if event == 'Yes':
                Gui().main()
            else:
                pygame.quit()
        else:
            event = pop_up(self.gamestate.kind_of_stalemate, 'Game drawn! Do you want to play again?', True)
            self.running = False
            if event == 'Yes':
                Gui().main()
            else:
                pygame.quit()

    def chose_promotion_piece(self, possible_move):
        event, values = sg.Window('', [[sg.Text('Promote to:')],
                                       [sg.Listbox(['Q', 'R', 'B', 'N'], size=(20, 4), key='LB')],
                                       [sg.Button('Ok'), sg.Button('Cancel')]]).read(close=True)
        if event == 'Ok':
            move_type = f'p{values["LB"][0][0]}'
            self.process_move((possible_move[0], possible_move[1], move_type))

    def start_pop_up(self, wrong_fen=False):

        # Make a collapse menu to not show AI strength and who to play as if game_mode = 'human'
        def collapse(layouts, key):
            return sg.pin(sg.Column(layouts, key=key))

        collapsible = [[sg.Text('Play as:     '), sg.Radio('White', '2', default=True, size=(5, 1), key='white'), sg.Radio('Black', '2', key='black')],
                       [sg.Text('AI strength:'), sg.Radio('Hard', '3', default=True, size=(5, 1), key='hard'), sg.Radio('Normal', '3', key='normal'), sg.Radio('Easy', '3', key='easy')]]

        if wrong_fen:
            layout = [[sg.Text('Start FEN (Optional): ', size=(15, 1), pad=(5, (20, 5))), sg.InputText(size=(60, 1), key='fen', pad=(5, (20, 5)))],
                      [sg.Text('Please enter a valid FEN, or leave empty for start position.', text_color='red', pad=(5, (0, 10)))],
                      [sg.Text('Opponent: ', pad=(9, 0)), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai', enable_events=True),
                       sg.Radio('Human', '1', size=(5, 1), key='human', enable_events=True)],
                      [collapse(collapsible, '-SEC1-')],
                      [sg.Submit(pad=(10, 18))]]
        else:
            layout = [[sg.Text('Start FEN (Optional): ', size=(15, 1), pad=(5, 25)), sg.InputText(size=(60, 1), key='fen')],
                      [sg.Text('Opponent: ', pad=(9, 0)), sg.Radio('AI', '1', default=True, size=(5, 1), key='ai', enable_events=True),
                       sg.Radio('Human', '1', size=(5, 1), key='human', enable_events=True)],
                      [collapse(collapsible, '-SEC1-')],
                      [sg.Submit(pad=(10, 15))]]

        window = sg.Window('Please chose start settings', layout)

        # Event loop
        while True:

            event, values = window.read()

            if event == sg.WIN_CLOSED or event == 'Exit':
                self.game_mode = 'ai'
                self.is_ai_white = False
                self.max_search_depth = s.max_search_depth_hard
                break

            if event == 'human':
                opened1 = False
                window['-SEC1-'].update(visible=opened1)

            elif event == 'ai':
                opened1 = True
                window['-SEC1-'].update(visible=opened1)

            elif event == 'Submit':
                if values['ai']:
                    self.game_mode = 'ai'
                if values['human']:
                    self.game_mode = 'human'
                if values['white']:
                    self.is_ai_white = False
                if values['black']:
                    self.is_ai_white = True
                if values['hard']:
                    self.max_search_depth = s.max_search_depth_hard
                if values['normal']:
                    self.max_search_depth = s.max_search_depth_normal
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

                break

        window.close()


# --------------------------------------------------------------------------------
#                          Static functions
# --------------------------------------------------------------------------------

def pop_up(title, message, question):
    if question:
        layout = [[sg.Text(message)],
                  [sg.Button('Yes'), sg.Button('No')]]
        window = sg.Window(title, layout, element_justification='c', element_padding=(5, 10))
        event, values = window.read()
        window.close()
        return event
    else:
        layout = [[sg.Text(message)],
                  [sg.Button('Ok')]]
        window = sg.Window(title, layout, element_justification='c', element_padding=(5, 10))
        window.close()


# --------------------------------------------------------------------------------
#                         Run the game
# --------------------------------------------------------------------------------


if __name__ == '__main__':

    # Set the correct icon in Windows taskbar
    if sys.platform.startswith('win'):
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
