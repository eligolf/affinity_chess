# --------------------------------------------------------------------------------
#            GUI file running the game
# --------------------------------------------------------------------------------
import board as b
import settings as s
import ai
import evaluation as e

import tkinter as tk
from tkinter import messagebox
import cProfile
import os
import sys
import copy
import time
import random
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
        self.screen = pygame.display.set_mode((s.width, s.height))

        # Moves
        self.moves_list = ''
        self.latest_move = (-100, -100)

        # Init Gamestate and AI
        self.gamestate = b.GameState()
        self.ai = ai.Ai()

        # Keep track of mouse button presses and mouse movements
        self.is_dragging = False
        self.square_under_mouse = 0
        self.x, self.y = 0, 0
        self.selected_square = 0

    def main(self):

        # Flag for when a move is made
        move_made = s.is_ai_white

        running = True
        while running:

            self.clock.tick(s.fps)

            self.square_under_mouse = self.get_square_under_mouse()

            # Events happening in GUI
            for event in pygame.event.get():

                # Able to quit GUI
                if event.type == pygame.QUIT:
                    answer = pop_up('Quit', 'Are you sure you want to quit?', True)
                    if answer == 'yes':
                        pygame.quit()
                        running = False

                # Mouse events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.is_dragging = True
                        if self.gamestate.board[self.square_under_mouse][0] == ('w' if self.gamestate.is_white_turn else 'b'):
                            self.selected_square = self.square_under_mouse
                        else:
                            self.selected_square = 0
                        self.x, self.y = pygame.mouse.get_pos()[0] - s.sq_size // 2, pygame.mouse.get_pos()[1] - s.sq_size // 2

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.is_dragging = False
                        start_square, end_square = self.selected_square, self.get_square_under_mouse()
                        move = (start_square, end_square)
                        if move in self.gamestate.get_valid_moves():
                            move_made = True
                            self.process_move(move)

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging:
                        self.x, self.y = pygame.mouse.get_pos()[0] - s.sq_size // 2, pygame.mouse.get_pos()[1] - s.sq_size // 2

                # Keyboard events
                elif event.type == pygame.KEYDOWN:

                    # Unmake move by pressing 'z'-key
                    if event.key == pygame.K_z:
                        self.gamestate.unmake_move()

                    # Restart game with 'r'-key
                    elif event.key == pygame.K_r:
                        answer = pop_up('Restart game', 'Are you sure you want to restart?', True)
                        if answer == 'yes':
                            Gui().main()

            # Update game and screen after human move
            self.draw(self.gamestate.get_valid_moves())

            # Check if stalemated/checkmated and stop the game if so
            if self.gamestate.is_check_mate or self.gamestate.is_stale_mate:
                running = False
                game_over_messages(self.gamestate.is_check_mate, self.gamestate.white_wins, self.gamestate.kind_of_stalemate)

            # If move made and game not over, change to AI if that option is chosen. Otherwise human vs human.
            if (move_made, running, s.game_mode) == (True, True, 'ai'):
                move, evaluation = self.ai.ai_make_move(self.gamestate, self.moves_list)
                self.process_move(move)
                self.print_eval(evaluation)

            # Change turns
            move_made = False

# --------------------------------------------------------------------------------
#                      Draw everything in GUI
# --------------------------------------------------------------------------------

    def draw(self, valid_moves):

        # Draw the board
        for row in range(12):
            for col in range(10):
                if 2 <= row <= 9 and 1 <= col <= 8:
                    x, y, w = s.sq_size * (col - 1), s.sq_size * (row - 2), s.sq_size

                    # Squares
                    square_color = s.board_colors[(row + col) % 2]
                    pygame.draw.rect(self.screen, square_color, pygame.Rect(x, y, w, w))

                    # Highlight squares
                    self.highlight_squares(valid_moves)

                    # Pieces
                    piece = self.gamestate.board[row * 10 + col]
                    if piece != '--' and (row * 10 + col != self.selected_square or not self.is_dragging):
                        self.screen.blit(s.images[piece], pygame.Rect(x, y, w, w))

        # Draw dragged piece
        if self.is_dragging and self.gamestate.board[self.selected_square] not in ['--', 'FF']:
            piece = self.gamestate.board[self.selected_square]
            self.screen.blit(s.images[piece], pygame.Rect(self.x, self.y, s.sq_size, s.sq_size))

        # Update screen
        pygame.display.flip()

    def highlight_squares(self, valid_moves):

        # Highlight if king is in check
        if self.gamestate.is_in_check:
            king_pos = self.gamestate.white_king_location if self.gamestate.is_white_turn else self.gamestate.black_king_location
            row, col = king_pos // 10 - 2, king_pos % 10 - 1  # Row = 1st number of sq_sel - 2, col = 2nd number of sq_sel - 1
            pygame.draw.rect(self.screen, s.check_red, (col * s.sq_size, row * s.sq_size, s.sq_size - 1, s.sq_size - 1), 3)

        # Highlight latest move
        start_row, start_col = self.latest_move[0] // 10 - 2, self.latest_move[0] % 10 - 1
        end_row, end_col = self.latest_move[1] // 10 - 2, self.latest_move[1] % 10 - 1
        pygame.draw.rect(self.screen, s.grey[3], (start_col * s.sq_size, start_row * s.sq_size, s.sq_size - 1, s.sq_size - 1), 4)
        pygame.draw.rect(self.screen, s.grey[3], (end_col * s.sq_size, end_row * s.sq_size, s.sq_size - 1, s.sq_size - 1), 4)

        # Highlight when dragging a piece
        if self.is_dragging:
            square = self.selected_square
            row, col = square // 10 - 2, square % 10 - 1

            # Selected square
            if self.gamestate.board[square][0] == ('w' if self.gamestate.is_white_turn else 'b'):
                pygame.draw.rect(self.screen, s.orange, (col * s.sq_size, row * s.sq_size, s.sq_size - 2, s.sq_size - 2), 5)

            # Possible moves
            for move in valid_moves:
                if move[0] == square:
                    row, col = move[1] // 10 - 2, move[1] % 10 - 1
                    pygame.draw.rect(self.screen, s.green, (col * s.sq_size, row * s.sq_size, s.sq_size - 2, s.sq_size - 2), 4)

    def print_eval(self, evaluation):
        evaluation = -evaluation if s.is_ai_white else evaluation

        if self.ai.is_in_opening and s.play_with_opening_book:
            evaluation = '0.00 (Opening: ' + str(self.ai.opening_name) + ')'
        else:
            if evaluation > 1e6:
                evaluation = 'AI wins'
            elif evaluation < -1e6:
                evaluation = 'Human wins'
            else:
                evaluation = round(evaluation / s.eval_level, 2)

        print('-------------------------')
        print(self.moves_list)
        print('')
        print('Evaluation: ' + str(evaluation))
        print('AI level: ' + str(s.level))
        print('-------------------------\n')

# --------------------------------------------------------------------------------
#               Helper functions
# --------------------------------------------------------------------------------

    def process_move(self, move):

        # Make the move and update move info
        self.gamestate.make_move(move[0], move[1])
        self.latest_move = move
        self.add_move_to_list(move[0], move[1])  # Add move to list of made moves
        self.gamestate.move_counter += 0.5  # Increase move counter

        # Play a sound when a move is made
        if s.toggle_sound:
            playsound(s.sound_piece_moved)

        # Evaluate current position after the move is made
        if s.static_evaluation:
            evaluation = e.evaluate(self.gamestate)
            print('(Static evaluation for ' + ('white: ' if not self.gamestate.is_white_turn else 'black: ') + str(evaluation if self.gamestate.is_white_turn else -evaluation) + ')')

    def add_move_to_list(self, start_square, end_square):

        text = self.return_move_as_string(start_square, end_square)

        if float(self.gamestate.move_counter % 1000).is_integer():
            move_text = ' ' + str(int(self.gamestate.move_counter)) + '.' + text
        else:
            move_text = ' ' + text

        self.moves_list += move_text

    def return_move_as_string(self, start_square, end_square):

        # Get the squares corresponding row and col
        start_row, start_col = start_square // 10 - 2, start_square % 10 - 1
        end_row, end_col = end_square // 10 - 2, end_square % 10 - 1

        # Check if last move was to take a piece
        piece_taken = False
        if self.gamestate.piece_captured != '--':
            piece_taken = True

        # The piece that is moving
        piece = self.gamestate.piece_moved[1]

        # Pawn
        if piece == 'p':
            if piece_taken:
                text = s.letters[start_col] + 'x' + s.letters[end_col] + s.numbers[7-end_row]
            else:
                text = s.letters[end_col] + s.numbers[7-end_row]

        # Other pieces
        else:
            if piece_taken:
                text = piece + 'x' + s.letters[end_col] + s.numbers[7-end_row]
            else:
                text = piece + s.letters[end_col] + s.numbers[7-end_row]

            # Castling
            if piece == 'K':
                d = start_square - end_square
                # Long castle
                if d == 2:
                    text = 'O-O-O'
                # Short castle
                elif d == -2:
                    text = 'O-O'

        # Check if the move resulted in a check
        self.gamestate.get_valid_moves()
        if self.gamestate.is_in_check:
            text += '+'

        return text

    def get_square_under_mouse(self):
        pos = pygame.mouse.get_pos()  # (x, y) location of click
        col, row = (pos[0] + s.sq_size) // s.sq_size, (pos[1] + 2 * s.sq_size) // s.sq_size  # Get corresponding square
        square_under_mouse = row * 10 + col  # Get corresponding square in 10x12 board

        return square_under_mouse


# --------------------------------------------------------------------------------
#                          Static functions
# --------------------------------------------------------------------------------

def pop_up(title, message, question):
    tk.Tk().withdraw()
    if question:
        return messagebox.askquestion(title=title, message=message)
    else:
        messagebox.showinfo(title=title, message=message)


def game_over_messages(checkmate, white_wins, stalemate_type):

    if checkmate:
        winner = 'white' if white_wins else 'black'
        answer = pop_up('Checkmate', f'Checkmate, {winner} won!\n\nDo you want to play again?', True)
        if answer == 'yes':
            Gui().main()
        else:
            pygame.quit()
    else:
        answer = pop_up(stalemate_type, 'Game drawn!\n\nDo you want to play again?', True)
        if answer == 'yes':
            Gui().main()
        else:
            pygame.quit()

# --------------------------------------------------------------------------------
#                         Run main function
# --------------------------------------------------------------------------------


if __name__ == '__main__':

    if s.timing:
        pr = cProfile.Profile()
        pr.enable()
        Gui().main()
        pr.disable()
        pr.print_stats(sort=s.timing_sort)
    else:
        Gui().main()
