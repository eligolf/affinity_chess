# Introduction
Affinity Chess is a chess program/engine written in Python, supporting both play against a human or an AI. 

# Before you start playing
In the file settings.py you will find a lot of settings for the game and GUI in general. Here are some of the most important settings to know of before you start playing:
- game_mode: 'ai' to play against the AI, 'human' to play human vs human.
- is_ai_white: True if AI is playing as white, False if AI is black.
- max_search_time: After this time runs out, the AI returns the move from the current depth. 
- min_search_depth: Search for at least this depth before returning a move (overrides max_search_time).
- max_search_depth: Stops when it reaches this depth, or if max_search_time has run out before that. Must be set larger than min_search_depth.

Other variables are changed at own risk. However, they are all explained more or less thoroughly in the comments in the code.

# How to play
Playing is very simple. You can run the command "python gui.py" in the terminal, in the folder where you downloaded the game. Or you can open up gui.py in your favorite IDE and play from there.

<div style="text-align:center"><img src="https://i.ibb.co/37CLGHL/gui-image.png" /><br></div>

You move a piece by dragging and dropping it in the GUI with your mouse. When you grab a piece, all legal squares for that piece will light up, shown in the image above.

Useful commands:
- z-key: Undo the latest move.
- r-key: Restart the game with the initial settings.

# Game features
Affinity Chess supports the rules of normal chess.
- [X] Castling
- [X] Enpassant
- [X] Pawn promotion to a queen
- [X] Draw by 3 fold repetition
- [X] Draw by insufficient material
- [X] Draw by 50 move rule
- [X] Checkmate and stalemate detection

Deviations to be implemented in the future: 
- [ ] Possibility to promote to other pieces than queen.

# Other features
- [X] Simple GUI with drag and drop piece movement.
- [X] Ability to chose AI level (see AI features below).
- [X] Ability to play again when game is over.
- [X] Restart game when pressing r-key.
- [X] Undo move with 'z'-key.
- [X] Sound effects when making a move.

Future implementation ideas:
- [ ] Start up window to set initial paramters such as:
  - Human or AI opponent.
  - AI level.
  - Max/min search depth.
  - Max search time.
  - AI playing with opening book or not.
- [ ] Ability to flip board.
- [ ] Different sound for different type of moves (capture piece, castling etc).
  
# AI features
Three different levels:
<ol start="0">
<li>Picks a random move from all valid moves.</li>
<li>Looks 1 half move ahead, makes an evaluation, and picks the top move.</li>
<li>TBD.</li>
<li>Full Negamax algorithm.</li>
</ol>

Level 3 information:
-
The Level 3 AI is based on a Negamax algorithm with the following features included:
- [X] Alpha-beta pruning
- [X] Iterative deepening
- [X] Transposition Table
- [X] Move ordering:
  - Best move from previous iterations
  - Killer moves
  - MVV/LVA
  - Internal Iterative Deepening

There is also a small opening book included which you decide if the AI should use or not. 

Future implementation ideas:
- [ ] Make negamax stop at exactly the maximum search time and return the best move from the previous iteration
- [ ] Bitboard representation
- [ ] Hash moves move ordering
- [ ] Larger opening book/other opening concept
- [ ] Null move
- [ ] Quiscience search
- [ ] Late move reduction (LMR)
- [ ] Print out the PV line that AI think is best

# Evaluation function
You have the ability to chose the level of evaluation in the settings file. Features for the level 2 evaluation function are as follows:
- [X] Checkmate and stalemate
- [X] Interpolation between midgame and endgame phase
- [X] Basic piece values, same in mid- and endgame
- [X] Piece-Square dependent values, interpolated between mid- and endgame.
- [X] Castling bonus in opening
- [X] Static bishop pair bonus
- [X] Static double pawn punishment
- [X] Static isolated pawn punishment
- [X] Knights worth slightly less in endgame, bishops slightly more
- [X] Rook on open or semi open file bonus
- [X] Punishment for having a piece in front of un-developed d- and e-pawn

Future implementation ideas:
- [ ] Bonus for attacks around the enemy king
- [ ] Bonus for attacks in the center
- [ ] Bonus for passed pawns
- [ ] Bonus for trading material when being up in material
- [ ] Bonus for mobility
- [ ] Punishment for not developing pieces



