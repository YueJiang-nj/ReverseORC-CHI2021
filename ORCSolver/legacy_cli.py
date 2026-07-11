"""Shared command-line options for the original (non-hierarchical) demos."""

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LegacyOptions:
    width: int
    height: int
    headless: bool
    time_only: bool
    show_window: bool

    def log(self, *values):
        if not self.time_only:
            print(*values)

    def report(self, seconds, result=None, loss=None):
        if self.time_only:
            print("%.9f" % seconds)
            return
        print("Time: %s" % seconds)
        if self.headless:
            print("window: %d x %d" % (self.width, self.height))
            print("loss: %s" % loss)
            print("result:")
            for name, value in sorted((result or {}).items()):
                print("  %s: %s" % (name, value))


def configure(default_width, default_height, default_show=True):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("width", nargs="?", type=int, default=default_width)
    parser.add_argument("height", nargs="?", type=int, default=default_height)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--headless", action="store_true",
                        help="do not open windows; print time and result")
    output.add_argument("--time-only", action="store_true",
                        help="do not open windows; print only solver time")
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0:
        parser.error("width and height must be positive")
    # Original examples use ../images paths. Anchor them to this script folder
    # so GUI assets work whether launched from ORCSolver, ReverseORCSolver, or
    # their common parent.
    os.chdir(Path(__file__).resolve().parent)
    return LegacyOptions(args.width, args.height, args.headless, args.time_only,
                         bool(default_show) and not (args.headless or args.time_only))
