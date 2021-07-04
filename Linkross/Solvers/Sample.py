from ..Solver import SolverBase


class SampleSolver(SolverBase):
    def suitable(self, current_rules):
        return True

    def get_deck(self):
        return 0x107,0x106,0xe0,0xb1,0xd2

    def solve(self, game):
        return 5, 9
