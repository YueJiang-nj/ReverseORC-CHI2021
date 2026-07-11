import unittest

from hierarchical_solver_cpp import Group, HierarchicalSolver, Size, Widget


def widget(name, preferred=50):
    return Widget(name, Size(20, preferred, 100), Size(20, 30, 60))


class CppSolverTests(unittest.TestCase):
    def test_nested_groups_and_wrapping(self):
        first = Group("first", [widget(f"w{i}") for i in range(1, 6)],
                      "horizontal_flow", gap=5)
        second = Group("second", [widget(f"w{i}") for i in range(6, 11)],
                       "horizontal_flow", gap=5)
        root = Group("canvas", [first, second], "column", gap=10)
        result = HierarchicalSolver().solve(root, 180, 150)
        self.assertEqual(result.local_solves, 3)
        self.assertEqual(result.levels_solved, 3)
        self.assertGreaterEqual(result.solver_seconds, 0)
        self.assertLessEqual(result.boxes["first"].bottom, result.boxes["second"].top)

    def test_weighted_allocation(self):
        important = Group("important", [widget("a", 80)], "row", weight=100)
        flexible = Group("flexible", [widget("b", 80)], "row", weight=1)
        result = HierarchicalSolver().solve(
            Group("root", [important, flexible], "row"), 120, 40)
        self.assertGreater(result.boxes["important"].width,
                           result.boxes["flexible"].width)

    def test_rejects_infeasible_canvas(self):
        root = Group("root", [widget("a"), widget("b")], "row", gap=5)
        with self.assertRaises(ValueError):
            HierarchicalSolver().solve(root, 40, 30)

    def test_legacy_boundaries(self):
        result = HierarchicalSolver().solve(Group("root", [widget("a")]), 50, 30)
        self.assertEqual(result.legacy_boundaries()["a_r"], 50)


if __name__ == "__main__":
    unittest.main()
