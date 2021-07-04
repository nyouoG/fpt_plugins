from ..Solver import SolverBase


class SampleSolver(SolverBase):
    def suitable(self, current_rules):
        return True

    def get_deck(self):
        return 0,0,0,0,0

    def solve(self, game):
        return 5, 9
