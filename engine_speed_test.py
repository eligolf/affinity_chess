#  -----------------------------------------------------------------------------------------------------------
#                                Engine speed test
#
#  The purpose of this test run is to test the engine performance. It runs some test cases
#  for a number of times and calculates the average time per test case. It also calculates the
#  the average time for the complete test run. The purpose is to measure if changes in the code
#  lead to improvements in calculation speed.
#
#  All positions in the file 'engine_performance.txt' in the folder test_positions are tested.
#  In the default file there are 8 test cases:
#
#  2 opening positions
#  2 midgame positions
#  2 endgame positions
#  2 late endgame positions
#
#  The results are saved to 'test_timings_{today's date_time}.csv' in the folder '/test_positions/timing'.
#
#  -------------------------------------------------------------------------------------------------------------

import gamestate as gs
import ai

import pandas as pd
import csv
import re
import time
from datetime import datetime

test_file = 'engine_performance'
runs_per_game = 5  # Run the test cases this many games and get the average timing


class Performance:

    def __init__(self):

        self.columns = ['Test case', 'Depth', 'Number of runs', 'Average time']
        self.df = pd.DataFrame(columns=self.columns)

    def run_test(self):

        for j, test_case in enumerate(test_positions):

            # Get information from the test case
            depth = int(re.findall(r'\d+', test_case)[-1])
            fen = ' '.join([test_case.split()[0], test_case.split()[1], test_case.split()[2], test_case.split()[3].split(',')[0]])
            white_turn = True if 'w' in fen else False

            # Init AI function and the gamestate
            current_ai = ai.Ai(depth)
            gamestate = gs.GameState(fen, 'ai', white_turn, depth)
            gamestate.is_white_turn = white_turn

            timing = 0
            for run in range(runs_per_game):
                time_start = time.time()

                # Run the AI make move module for the given gamestate
                current_ai.ai_make_move(gamestate)

                timing += time.time() - time_start

            # Calculate the average time fo the runs and print it to the larger data frame
            average_time = round(timing/runs_per_game, 2)
            new_df = pd.DataFrame([[test_case, depth, runs_per_game, average_time]], columns=self.columns)
            self.df = pd.concat([self.df, new_df])

        # Add a last row with the complete average time
        total_average = self.df['Average time'].mean()
        new_df = pd.DataFrame([['Complete average time', '-', '-', total_average]], columns=self.columns)
        self.df = pd.concat([self.df, new_df])

        # Create a test result file from the complete self.df
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.df.to_csv(f'test_positions/timing/test_timings_{current_time}.csv', index=False)


#  --------------------------------------------------------------------------------
#                      Run engine performance test
#  --------------------------------------------------------------------------------

tests = f'test_positions/{test_file}.txt'
temp = open(tests, "r")
test_positions = temp.readlines()
number_of_tests = len(test_positions)
Performance().run_test()
