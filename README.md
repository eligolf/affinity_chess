# Introduction
Affinity Chess is a chess program/engine written in Python as a hobby project to learn more about programming in general. The program includes a GUI in which you can play against another human or against the built in AI.

# Getting started
**Use in external GUI:** In the exe-folder you find the .exe file which you can use to install the engine in an external GUI. You can find all communication and logic in the uci.py file.

**Use in own GUI:** To use the own GUI you need to download and install the module Pygame. The program should be independent on OS, but please let me know if any issues arise if you run it in any other OS than Windows. 

# Start playing
Playing Affinity Chess is very simple. You can run the command "python gui.py" in the terminal, in the folder where the game is located. Or you can open up gui.py in your favorite IDE and play from there.
<figure>
    <img src='https://user-images.githubusercontent.com/59540119/100571413-5c1fac80-32d3-11eb-9225-5ee58f2c2cd6.png' alt='missing' width="70%" height="70%" />
    <figcaption><i>Sample view of the Affinity Chess GUI during a game against the AI in the opening stage.</i></figcaption>
  <br>
  <br>
</figure>

You move a piece by dragging and dropping it in the GUI with your mouse. When you grab a piece, all legal squares for that piece will light up, shown in the image above.

Useful keyboard shortcuts:
- **r-key**: Restart the game.
- **f-key**: Flip the board.
- **z-key**: Undo the latest move.

# Game features
Affinity Chess supports the rules of normal chess.
- [X] Checkmate and stalemate detection
- [X] Castling
- [X] Enpassant
- [X] Pawn promotion to Queen, Rook, Bishop, or Knight
- [X] Draw by:
  - 3 fold repetition
  - Insufficient material
  - 50 move rule
  
# AI
The AI is based on a Negamax algorithm with the following features currently included:
- [X] Alpha-beta pruning
- [X] Iterative deepening
- [X] Transposition Table
- [X] Move ordering:
  - Best move from previous iterations
  - Killer moves
  - MVV/LVA
- [X] Null move
- [X] Syzygy 3, 4 and 5 man endgame tablesbases 

You also have the ability to let the AI use the built in opening books. If you want you can add your own polyglot opening book (.bin) to the 'opening_books' folder and use that one instead.  

Future implementation ideas:
- [ ] Quiscience search
- [ ] Hash moves move ordering
- [ ] Late move reduction (LMR)
- [ ] Obtain the PV line

### Evaluation function

The evaluation function is located in evaluation.py. Some parameters for the evaluation are updated in the move/unmake move functions in gamestate.py. 

Note that the evaluation score given by the AI in the GUI is always from the AI perspective. A positive score means the AI thinks its winning and a negative score means it thinks the human is winning, no matter what color it plays. 

Currently the following parameters are considered when the AI evaluates a position:  
- [X] Checkmate and stalemate
- [X] Interpolation between midgame and endgame phase
- [X] Basic piece values, same in mid- and endgame
- [X] Piece-Square dependent values, interpolated between mid- and endgame.
- [X] Static bishop pair bonus
- [X] Static double pawn punishment
- [X] Static isolated pawn punishment
- [X] Knights worth slightly less in endgame, bishops slightly more
- [X] Rook on open or semi open file bonus
- [X] Punishment for having a piece in front of undeveloped d- and e-pawns
- [X] Punishment for not developing pieces
- [X] Attack the enemy king
- [X] Attack the center squares
- [X] Bishops and rooks punished with lots of pawns, knights better

Future implementation ideas:
- [ ] Passed pawns
- [ ] Favor to trade material when being up in material, and vise versa
- [ ] Mobility

# Tests

### Perft
If you make changes to the code you can test that the legal move generator is working properly through perft.py. You have two options to chose from: 

1. A shorter version with some critical test positions including castling prevented king and queen side, promotion, promotion in/out of check, enpassant moves, discovered checks, double checks and more. The positions are found in 'test_positions/test_positions_short.txt'. The test takes around 3 minutes to run. 

2. A complete test including around 6500 randomly selected test positions, found in 'test_positions/test_positions_full.txt'. The test takes around 24 hours to run.

To change to the full test you simply change the test_file variable at the top of perft.py to 'full' and run as normal.

### Engine speed/performance
In the file engine_speed_test.py you can run some test cases for a number of times and calculates the average time per test case. The function also calculates the the average time for the complete test run. The purpose is to measure if changes in the code lead to improvements in calculation speed.

All positions in the file 'test_positions/engine_performance.txt' are tested. In the default file there are 8 test cases:

 - 2 opening positions
 - 2 midgame positions
 - 2 endgame positions
 - 2 late endgame positions

The results are saved in a csv file in the folder 'test_positions/timing'.



