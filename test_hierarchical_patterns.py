import unittest

from hierarchical_patterns import IMAGE_DIRECTORY, SCENARIOS, pattern_asset, teaser_asset, walk
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


if __name__ == "__main__":
    unittest.main()
