#  --------------------------------------------------------------------------------------------------
#                                Perft testing
#
#  Test some critical test cases with test_file 'short'.
#  This runs in about 5 minutes.
#
#  For a full run of around 6500 random positions, change test_file to 'full'
#  This runs in about 24 hours.
#
#  Any failed test case(s) will be printed to 'failed_tests.csv' in the root directory.
#  ---------------------------------------------------------------------------------------------------

import settings as s
import gamestate as gs

import pandas as pd
import csv
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

test_file = 'short'


class Perft:

    def __init__(self):

        self.test_failed = False

        self.columns = ['Test case', 'Depth', 'Nodes searched', 'Real answer']
        self.df = pd.DataFrame(columns=self.columns)

    def run_perft(self):

        for j, test_case in enumerate(test_positions):

            answers = test_case.split()[-1].split(',')[1:]
            fen = ' '.join([test_case.split()[0], test_case.split()[1], test_case.split()[2], test_case.split()[3].split(',')[0]])

            gamestate = gs.GameState(fen, 'ai', False, 0)

            gamestate.is_white_turn = True if 'w' in fen else False

            # Run perft test with iterative deepening to test all depths
            for i in range(0, len(answers)):
                if int(answers[i]) <= 1e7:

                    nodes = self.perft(gamestate, i+1)

                    if int(answers[i]) != int(nodes) and answers[i] != '0':
                        new_df = pd.DataFrame([[test_case, i, nodes, answers[i]]], columns=self.columns)
                        self.df = pd.concat([self.df, new_df])
                        self.df.to_csv('failed_tests.csv', index=False)
                        self.test_failed = True
                        print('Test failed:')
                        print(test_case)
                        print('Nodes searched:', nodes)
                        print('Answer:', answers[i])
                        print('---------------------------')

            print(f'{j+1}/{len(test_positions)} tests performed.')

        print('Perft failed, see "failed_tests.csv" for more information about the failed test cases.') if self.test_failed else print('Perft completed successfully.')

        # Play a sound when finished
        sound = pygame.mixer.Sound('sounds/ding.wav')
        sound.play()

    def perft(self, gamestate, depth):

        if depth == 0:
            return 0

        if depth == 1:
            return len(gamestate.get_valid_moves())

        children = gamestate.get_valid_moves()

        tot = 0
        for child in children:

            gamestate.make_move(child)
            tot += self.perft(gamestate, depth - 1)
            gamestate.unmake_move()

        return tot


#  --------------------------------------------------------------------------------
#                             Run perft tests
#  --------------------------------------------------------------------------------

pygame.init()
tests = f'test_positions/{test_file}.txt'
temp = open(tests, "r")
test_positions = temp.readlines()
Perft().run_perft()
