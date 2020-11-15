# Introduction
Affinity Chess is a chess program/engine written in Python, supporting both play against a human or an AI. 

# How to play

# Most important settings to chose in settings.py

# Game features
Affinity Chess supports the rules of normal chess, including:
- Castling
- Enpassant
- Pawn promotion to a queen
- Draw by 3 fold repetition
- Draw by insufficient material
- Draw by 50 move rule
- Checkmate and stalemate detection

Deviations to be implemented in the future: 
- Possibility to promote to other pieces than queen.

# Other features
- Simple GUI with drag and drop piece movement
- Ability to chose AI level (see AI features below)
- Ability to play again when game is over
- Restart game when pressing r-key
- Undo move with 'z'-key.
- Sound effects when making a move

Future implementation ideas:
- Start up window to set initial paramters such as:
  - Human or AI opponent
  - AI level
  - Max/min search depth
  - Max search time
  - AI playing with opening book or not
- Different sound for different type of moves (capture piece, castling etc)
  
# AI features
Three different levels:
0: Picks a random move from all valid moves.
1: Looks 1 half move ahead, makes an evaluation, and picks the top move.
2: TBD
3: Full Negamax algorithm, see features below.

Level 3 information:
-
The Level 3 AI is based on a Negamax algorithm with the following features included:
- Alpha-beta pruning
- Iterative deepening
- Transposition Table
- Move ordering:
  - Best move from previous iterations
  - Killer moves
  - MVV/LVA
  - Internal Iterative Deepening

There is also a small opening book included which you decide if the AI should use or not. 

Future implementation ideas:
- Bitboard representation
- Hash moves move ordering
- Larger opening book/other opening concept
- Null move
- Quiscience search
- Late move reduction (LMR)
- Print out the PV line that AI think is best

# Evaluation function
You have the ability to chose the level of evaluation in the settings file. Features for the level 2 evaluation function are as follows:
- Checkmate and stalemate
- Interpolation between midgame and endgame phase
- Basic piece values, same in mid- and endgame
- Piece-Square dependent values, interpolated between mid- and endgame.
- Castling bonus in opening
- Static bishop pair bonus
- Static double pawn punishment
- Static isolated pawn punishment
- Knights worth slightly less in endgame, bishops slightly more
- Rook on open or semi open file bonus



