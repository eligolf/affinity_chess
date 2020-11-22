# Introduction
Affinity Chess is a chess program/engine written in Python as a hobby project to learn more about programming. The program allows you to play against another human or against the built in AI.

# Getting started
At start up you will be able to chose settings as in below image. You can put in a FEN position and use that as start position, or leave that field empty to use the normal start up position in chess. 

<figure>
    <img src='https://i.ibb.co/c1jtwCX/start-up.png' alt='missing' />
    <figcaption><i>The options available from the start-up screen.</i></figcaption>
  <br>
  <br>
</figure>

In the file settings.py you will find other settings for the game and GUI in general.

# Start playing
Playing is very simple. You can run the command "python gui.py" in the terminal, in the folder where you downloaded the game. Or you can open up gui.py in your favorite IDE and play from there.
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
- [X] Castling
- [X] Enpassant
- [X] Pawn promotion to all 4 piece types
- [X] Draw by 3 fold repetition
- [X] Draw by insufficient material
- [X] Draw by 50 move rule
- [X] Checkmate and stalemate detection

# Other features
- [X] Simple GUI with drag and drop piece movement.
- [X] Start up window to set:
  - Start FEN (optional)
  - Human or AI opponent.
  - Play as white or black.
  - AI level.
- [X] Sound effects when making a move.

Future implementation ideas:
- [ ] Make the GUI larger to include printing e.g. AI evaluation and the current move log.
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

There is also a small opening book included. 

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
- [X] Punishment for having a piece in front of undeveloped d- and e-pawns
- [X] Punishment for not developing pieces

Future implementation ideas:
- [ ] Bonus for attacks around the enemy king
- [ ] Bonus for attacks in the center
- [ ] Bonus for passed pawns
- [ ] Bonus for trading material when being up in material
- [ ] Bonus for mobility




