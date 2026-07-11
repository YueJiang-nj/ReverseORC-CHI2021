import unittest

from hierarchical_solver import Group, HierarchicalSolver, Size, Widget


def widget(name, pref=50):
    return Widget(name, Size(20, pref, 100), Size(20, 30, 60))


class HierarchicalSolverTests(unittest.TestCase):
    def test_two_groups_are_solved_inside_parent_boxes(self):
        first = Group("first", [widget("w%d" % i) for i in range(1, 6)],
                      "horizontal_flow", gap=5)
        second = Group("second", [widget("w%d" % i) for i in range(6, 11)],
                       "horizontal_flow", gap=5)
        root = Group("canvas", [first, second], "column", gap=10)
        result = HierarchicalSolver().solve(root, 180, 150)

        self.assertEqual(result.local_solves, 3)
        self.assertEqual(result.levels_solved, 3)
        self.assertLessEqual(result.boxes["first"].bottom, result.boxes["second"].top)
        for number in range(1, 6):
            child = result.boxes["w%d" % number]
            parent = result.boxes["first"]
            self.assertGreaterEqual(child.left, parent.left)
            self.assertLessEqual(child.right, parent.right + 1e-7)

    def test_weighted_parent_allocation_preserves_high_priority_preference(self):
        important = Group("important", [widget("a", 80)], "row", weight=100)
        flexible = Group("flexible", [widget("b", 80)], "row", weight=1)
        root = Group("root", [important, flexible], "row")
        result = HierarchicalSolver().solve(root, 120, 40)
        self.assertGreater(result.boxes["important"].width,
                           result.boxes["flexible"].width)

    def test_rejects_infeasible_canvas(self):
        root = Group("root", [widget("a"), widget("b")], "row", gap=5)
        with self.assertRaises(ValueError):
            HierarchicalSolver().solve(root, 40, 30)

    def test_legacy_boundary_adapter(self):
        root = Group("root", [widget("a")], "row")
        result = HierarchicalSolver().solve(root, 50, 30)
        self.assertEqual(result.legacy_boundaries()["a_r"], 50)

    def test_wrapped_flow_reserves_multiple_rows_in_column(self):
        flow = Group("flow", [widget("w%d" % i, 50) for i in range(6)],
                     "horizontal_flow")
        root = Group("root", [flow, widget("content")], "column")
        result = HierarchicalSolver().solve(root, 150, 200)
        tops = {round(result.boxes["w%d" % i].top, 5) for i in range(6)}
        self.assertGreater(len(tops), 1)
        self.assertLessEqual(max(result.boxes["w%d" % i].bottom for i in range(6)),
                             result.boxes["flow"].bottom + 1e-7)


if __name__ == "__main__":
    unittest.main()
