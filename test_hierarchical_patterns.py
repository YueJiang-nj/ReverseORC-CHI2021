import unittest

from hierarchical_patterns import (IMAGE_DIRECTORY, SCENARIOS, pattern_asset,
                                   print_time, solve_pattern, solve_teaser,
                                   teaser_asset, walk)
from contextlib import redirect_stdout
from io import StringIO
from hierarchical_solver import HierarchicalSolver


class HierarchicalPatternTests(unittest.TestCase):
    def test_every_visual_pattern_solves_at_its_default_window_size(self):
        for name, build in SCENARIOS.items():
            with self.subTest(pattern=name):
                _title, root, width, height = build()
                result = HierarchicalSolver().solve(root, width, height)
                self.assertIn("canvas", result.boxes)
                self.assertGreater(result.local_solves, 0)

    def test_teaser_matches_original_default_geometry_and_assets(self):
        _title, root, width, height = SCENARIOS["teaser"]()
        result = HierarchicalSolver().solve(root, width, height)
        expected = {
            "HF1": (0, 0, 640, 80),
            "HF2": (0, 80, 640, 240),
            "HF3": (0, 320, 640, 160),
            "CHI2020": (0, 80, 320, 240),
            "CHI2019": (320, 80, 320, 240),
            "message": (0, 320, 160, 80),
            "blank1": (160, 320, 320, 80),
            "send": (480, 320, 160, 80),
            "email": (0, 400, 160, 80),
            "blank2": (160, 400, 320, 80),
            "clear": (480, 400, 160, 80),
        }
        for name, geometry in expected.items():
            box = result.boxes[name]
            self.assertEqual(tuple(round(value) for value in
                                   (box.left, box.top, box.width, box.height)), geometry)
        for name in ["tool_%d" % i for i in range(1, 9)] + list(expected)[3:]:
            filename, _size = teaser_asset(name)
            self.assertTrue((IMAGE_DIRECTORY / filename).is_file(), filename)

    def test_every_widget_has_its_legacy_image_asset(self):
        for scenario, build in SCENARIOS.items():
            with self.subTest(pattern=scenario):
                _title, root, _width, _height = build()
                for node in walk(root):
                    if hasattr(node, "children"):
                        continue
                    asset = pattern_asset(scenario, node.name)
                    self.assertIsNotNone(asset, node.name)
                    self.assertTrue((IMAGE_DIRECTORY / asset[0]).is_file(), asset[0])

    def test_teaser_matches_legacy_landscape_pivot_at_1046_by_760(self):
        layout, result = solve_teaser(1046, 760)
        self.assertEqual(layout.direction, "row")
        expected = {
            "HF1": (0, 0, 80, 760),
            "HF2": (80, 0, 1046, 240),
            "HF3": (80, 240, 1046, 760),
        }
        for name, geometry in expected.items():
            box = result.boxes[name]
            self.assertEqual(tuple(round(value) for value in
                                   (box.left, box.top, box.right, box.bottom)), geometry)
        for index in range(1, 9):
            box = result.boxes["tool_%d" % index]
            self.assertEqual(round(box.width), 80)
            self.assertEqual(round(box.height), 95)

    def test_teaser_preserves_legacy_group_priority_at_400_square(self):
        layout, result = solve_teaser(400, 400)
        self.assertEqual(layout.direction, "column")
        expected = {
            "HF1": (0, 0, 400, 160),
            "HF2": (0, 160, 400, 400),
            "HF3": (0, 400, 400, 400),
        }
        for name, geometry in expected.items():
            box = result.boxes[name]
            self.assertEqual(tuple(round(value) for value in
                                   (box.left, box.top, box.right, box.bottom)), geometry)

    def test_teaser_action_rows_keep_corresponding_controls_equal(self):
        for width, height in [(640, 480), (1046, 760), (760, 1046), (1200, 400)]:
            with self.subTest(size=(width, height)):
                _layout, result = solve_teaser(width, height)
                for first, second in [("message", "email"),
                                      ("blank1", "blank2"),
                                      ("send", "clear")]:
                    first_box, second_box = result.boxes[first], result.boxes[second]
                    self.assertAlmostEqual(first_box.width, second_box.width)
                    self.assertAlmostEqual(first_box.height, second_box.height)
                first_row, second_row = result.boxes["message_row"], result.boxes["email_row"]
                self.assertAlmostEqual(first_row.bottom, second_row.top)
                self.assertEqual(first_row.left, second_row.left)
                self.assertEqual(first_row.right, second_row.right)

    def test_teaser_peer_logos_always_have_equal_boxes(self):
        sizes = [(400, 400), (640, 480), (1046, 760), (1200, 400),
                 (2048, 1117), (760, 1046)]
        for width, height in sizes:
            with self.subTest(size=(width, height)):
                _layout, result = solve_teaser(width, height)
                first = result.boxes["CHI2020"]
                second = result.boxes["CHI2019"]
                self.assertAlmostEqual(first.width, second.width)
                self.assertAlmostEqual(first.height, second.height)

    def test_timed_api_returns_solver_only_time_and_requested_size(self):
        _layout, result, solver_seconds = solve_pattern("teaser", 1046, 760)
        self.assertGreaterEqual(solver_seconds, 0)
        self.assertEqual(result.boxes["canvas"].width, 1046)
        self.assertEqual(result.boxes["canvas"].height, 760)

    def test_time_only_output_is_a_single_numeric_line(self):
        output = StringIO()
        with redirect_stdout(output):
            print_time("teaser", 640, 480)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertGreaterEqual(float(lines[0]), 0)

    def test_repeated_peer_elements_are_equal_in_other_patterns(self):
        peer_sets = {
            "simple_flow": [["top_%d" % i for i in range(1, 9)],
                            ["left_%d" % i for i in range(1, 7)]],
            "connected_flow": [["top_%d" % i for i in range(1, 7)],
                               ["left_%d" % i for i in range(1, 5)]],
            "optional_widgets": [["left_%d" % i for i in range(1, 7)]],
            "balanced_flow": [["balanced_%d" % i for i in range(1, 7)]],
            "video": [["top_%d" % i for i in range(1, 11)],
                      ["left_%d" % i for i in range(1, 7)],
                      ["CHI2020", "CHI2019"]],
            "flow_around": [[prefix + "_%d" % i
                             for prefix, count in [("fruit_upper", 24),
                                                   ("fruit_left", 18),
                                                   ("fruit_right", 18),
                                                   ("fruit_lower", 40)]
                             for i in range(1, count + 1)]],
        }
        for pattern, groups in peer_sets.items():
            _title, _root, width, height = SCENARIOS[pattern]()
            _layout, result, _seconds = solve_pattern(pattern, width, height)
            for peers in groups:
                with self.subTest(pattern=pattern, peers=peers[:2]):
                    reference = result.boxes[peers[0]]
                    for name in peers[1:]:
                        self.assertAlmostEqual(reference.width, result.boxes[name].width)
                        self.assertAlmostEqual(reference.height, result.boxes[name].height)

    def test_video_matches_original_geometry_at_400_by_640(self):
        _layout, result, _seconds = solve_pattern("video", 400, 640)
        expected_groups = {
            "HF": (0, 0, 400, 160),
            "VF": (0, 160, 80, 640),
            "VL": (80, 160, 400, 640),
        }
        for name, geometry in expected_groups.items():
            box = result.boxes[name]
            self.assertEqual(tuple(round(value) for value in
                                   (box.left, box.top, box.right, box.bottom)), geometry)
        for index in range(1, 11):
            box = result.boxes["top_%d" % index]
            self.assertEqual((round(box.width), round(box.height)), (80, 80))
        for index in range(1, 7):
            box = result.boxes["left_%d" % index]
            self.assertEqual((round(box.width), round(box.height)), (80, 80))
        self.assertEqual(
            tuple(round(value) for value in
                  (result.boxes["CHI2020"].width, result.boxes["CHI2020"].height)),
            (320, 240),
        )
        self.assertEqual(round(result.boxes["CHI2019"].top), 400)

    def test_video_matches_original_geometry_at_890_by_365(self):
        _layout, result, _seconds = solve_pattern("video", 890, 365)
        expected_groups = {
            "HF": (0, 0, 890, 80),
            "VF": (0, 80, 160, 365),
            "VL": (160, 80, 890, 365),
        }
        for name, geometry in expected_groups.items():
            box = result.boxes[name]
            self.assertEqual(tuple(round(value) for value in
                                   (box.left, box.top, box.right, box.bottom)), geometry)
        for index in range(1, 11):
            box = result.boxes["top_%d" % index]
            self.assertEqual((round(box.width), round(box.height)), (89, 80))
        for index in range(1, 7):
            box = result.boxes["left_%d" % index]
            self.assertEqual((round(box.width), round(box.height)), (80, 95))
        for name in ("CHI2020", "CHI2019"):
            box = result.boxes[name]
            self.assertEqual((round(box.width), round(box.height)), (365, 285))


if __name__ == "__main__":
    unittest.main()
