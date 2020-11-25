# Introduction
Affinity Chess is a chess program/engine written in Python as a hobby project to learn more about programming in general. The program includes a GUI in which you can play against another human or against the built in AI.

# Getting started
At start up you will be able to chose some initial settings for the game. You can use a custom FEN position as start position, or leave the field empty to use the normal initial chess position. 

<figure>
    <img src='https://i.ibb.co/c1jtwCX/start-up.png' alt='missing' />
</figure>

In the file settings.py you will find other settings for the game and GUI in general.

# Start playing
Playing Affinity Chess is very simple. You can run the command "python gui.py" in the terminal, in the folder where the game is located. Or you can open up gui.py in your favorite IDE and play from there.
<figure>
    <img src='https://i.ibb.co/37CLGHL/gui-image.png' alt='missing' />
    <figcaption><i>Sample view of the Affinity Chess GUI when dragging a piece.</i></figcaption>
  <br>
  <br>
</figure>

You move a piece by dragging and dropping it in the GUI with your mouse. When you grab a piece, all legal squares for that piece will light up, shown in the image above.

Useful commands:
- **z-key**: Undo the latest move.
- **r-key**: Restart the game.
- **f-key**: Flip the board.

# Game features
Affinity Chess supports the rules of normal chess.
- [X] Checkmate and stalemate detection
- [X] Castling
- [X] Enpassant
- [X] Pawn promotion to Queen, Rook, Bishop, or Knight
- [X] Draw by 3 fold repetition
- [X] Draw by insufficient material
- [X] Draw by 50 move rule

# Other features
- [X] Simple GUI with drag and drop piece movement.
- [X] Start up window to set:
  - Start position FEN (optional)
  - Human or AI opponent.
  - Play as white or black.
  - AI level.
- [X] Sound effects.

Future implementation ideas:
- [ ] Make the GUI larger to include printing e.g. AI evaluation and the current move log. Possibly change concept from Pygame to PySimpleGUI or some other more GUI friendly module. 
  
# AI
The AI is based on a Negamax algorithm with the following features currently included:
- [X] Alpha-beta pruning
- [X] Iterative deepening
- [X] Transposition Table
- [X] Move ordering:
  - Best move from previous iterations
  - Killer moves
  - MVV/LVA

You also have the ability to let the AI use the built in opening books. Or you can add your own polyglot opening book (.bin) to the 'opening_books' folder.  

Future implementation ideas:
- [ ] Quiscience search
- [ ] Hash moves move ordering
- [ ] Null move
- [ ] Late move reduction (LMR)
- [ ] Obtain the PV line
- [ ] Make negamax stop at exactly the maximum search time and return the best move from the previous iteration

### Evaluation function

The evaluation function is located in evaluation.py. Some parameters for the evaluation are updated in the move/unmake move functions in the GameState class. Currently the following parameters are considered when the AI evaluates a position.  
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

Future implementation ideas:
- [ ] Attack the enemy king
- [ ] Attack the center squares
- [ ] Passed pawns
- [ ] Trading material when being up in material
- [ ] Mobility
- [ ] Endgame related logic, especially for the king

# Testing/perft
If you make changes to the code you can test that the legal move generator is working properly through perft.py. You have two options to chose from: 

1. A shorter version with some critical test positions including castling prevented king and queen side, promotion, promotion in/out of check, enpassant moves, discovered checks, double checks and more. The positions are found in test_positions_short.txt. The test takes around 3 minutes to run on a normal computer. 

2. A complete test including around 6500 randomly selected test positions, found in test_positions_short.txt. The test takes around 24 hours to run on a normal computer.

To change to the full test you simply change the test file variable at the top of perft.py to 'test_positions_full.txt' and run as normal.




