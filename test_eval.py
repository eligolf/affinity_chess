import evaluation as e
import board as b


# Tests whether evaluation is symmetrical or not
def eval_symmetry(gamestate):

    evaluation = e.evaluate(gamestate)
    gamestate.is_white_turn = False
    mirror_eval = -e.evaluate(gamestate)

    return evaluation == mirror_eval


if __name__ == "__main__":
    gamestate = b.GameState()  # Testing start position, change start position in settings file
    print(eval_symmetry(gamestate))
