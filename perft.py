#  --------------------------------------------------------------------------------
#                                Perft testing
#  --------------------------------------------------------------------------------

import settings as s
import board as b

import pandas as pd
import xlsxwriter as xlsw
import csv


class Perft:

    def __init__(self):
        self.node_counter = -1
        self.nodes = {}

        self.check_mate_counter = 0
        self.checkmates = {}

        self.stalemate_counter = 0
        self.stalemates = {}

        self.promotion_counter = 0
        self.promotions = {}

        self.is_check_counter = 0
        self.checks = {}

        self.capture_counter = 0
        self.captures = {}

        self.columns = ['Test case', 'Depth', 'Nodes searched', 'Real answer']
        self.df = pd.DataFrame([[0, 0, 0, 0]], columns=self.columns)

    def run_perft(self):

        for test_case in test_positions:

            answers = test_case.split()[-1].split(',')[1:]
            fen = ' '.join([test_case.split()[0], test_case.split()[1], test_case.split()[2], test_case.split()[3].split(',')[0]])

            self.nodes = {}

            gamestate = b.GameState(fen, 'ai', False, 0)

            gamestate.is_white_turn = True if 'w' in fen else False

            # Run perft test with iterative deepening
            for i in range(1, len(answers) + 1):
                if int(answers[i-1]) <= 1e7:
                    nodes = self.perft(gamestate, i)

                    self.nodes[i] = nodes
                    self.node_counter = -1

                    if int(answers[i-1]) != int(nodes) and answers[i-1] != '0':
                        new_df = pd.DataFrame([[test_case, i-1, list(self.nodes.values())[-1], answers[i-1]]], columns=self.columns)
                        self.df = pd.concat([self.df, new_df])
                        self.df.to_csv('faulty_positions.csv', index=False)

            print(test_case)
            self.node_counter = -1

        self.df.to_csv('faulty_positions.csv', index=False)

    def perft(self, gamestate, depth):

        if depth == 0:
            return 0

        if depth == 1:
            return len(gamestate.get_valid_moves())

        children = gamestate.get_valid_moves()

        tot = 0
        for child in children:

            gamestate.make_move(child[0], child[1], child[2])
            tot += self.perft(gamestate, depth - 1)
            gamestate.unmake_move()

        return tot


# Run perft tests
tests = "test_positions.txt"
temp = open(tests, "r")
test_positions = temp.readlines()
Perft().run_perft()
