import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class LegacyCliTests(unittest.TestCase):
    CASES = [
        ("ORCSolver/teaser_example.py", 640, 480),
        ("ORCSolver/video_example.py", 400, 640),
        ("ORCSolver/simple_flow_pattern.py", 640, 320),
        ("ORCSolver/connected_flow_pattern.py", 640, 240),
        ("ORCSolver/optional_widgets_pattern.py", 800, 800),
        ("ORCSolver/balanced_flow_pattern.py", 240, 500),
        ("ORCSolver/flow_around_pattern.py", 600, 600),
    ]

    def test_every_legacy_launcher_supports_custom_size_and_time_only(self):
        for filename, width, height in self.CASES:
            with self.subTest(filename=filename):
                completed = subprocess.run(
                    [sys.executable, filename, str(width), str(height), "--time-only"],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                lines = completed.stdout.splitlines()
                self.assertEqual(len(lines), 1)
                self.assertGreaterEqual(float(lines[0]), 0)

    def test_legacy_headless_prints_size_time_and_result(self):
        completed = subprocess.run(
            [sys.executable, "ORCSolver/video_example.py", "400", "640", "--headless"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        self.assertIn("Time:", completed.stdout)
        self.assertIn("window: 400 x 640", completed.stdout)
        self.assertIn("result:", completed.stdout)
        self.assertIn("HF_l:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
