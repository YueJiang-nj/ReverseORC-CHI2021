# Original ORC Solver

This directory contains the original, non-hierarchical ReverseORC solver and
its runnable examples. The hierarchical solver and its examples are kept at
the repository root.

## Contents

- `flow_solver.py` — flow-layout algorithms and loss calculations.
- `orclayout_classes.py` — ORC widgets, rows, columns, pivots, and flows.
- `legacy_cli.py` — shared command-line handling for the original examples.
- `teaser_example.py` — responsive teaser layout.
- `video_example.py` — toolbar and video/logo layout.
- `simple_flow_pattern.py` — horizontal and vertical flow example.
- `connected_flow_pattern.py` — connected toolbar flows.
- `optional_widgets_pattern.py` — optional-widget behavior.
- `balanced_flow_pattern.py` — balanced flow layout.
- `flow_around_pattern.py` — flow around a fixed region.

## Requirements

The examples use Python, Tkinter, Pillow, CVXPY, and NumPy. Run the examples
from the repository root so the existing `../images` asset paths resolve to the
sibling `images` directory:

```text
parent-directory/
├── images/
└── ReverseORCSolver/
    └── ORCSolver/
```

## Running the examples

From the `ReverseORCSolver` repository root:

```bash
python ORCSolver/teaser_example.py 640 480
python ORCSolver/video_example.py 400 640
python ORCSolver/simple_flow_pattern.py 640 320
python ORCSolver/connected_flow_pattern.py 640 240
python ORCSolver/optional_widgets_pattern.py 800 800
python ORCSolver/balanced_flow_pattern.py 240 500
python ORCSolver/flow_around_pattern.py 600 600
```

The two positional arguments are the requested window width and height. If
they are omitted, the example uses its original default dimensions.

## Output modes

Without an output flag, examples that enable their original GUI open the
Tkinter result and time windows.

Use `--headless` to open no windows and print solving time, loss, and result
variables:

```bash
python ORCSolver/video_example.py 890 365 --headless
```

Use `--time-only` to open no windows and print one numeric line containing only
the solver time in seconds:

```bash
python ORCSolver/video_example.py 890 365 --time-only
```

`--headless` and `--time-only` are mutually exclusive.

## Timing

The reported value measures the original layout solver call. GUI creation,
image loading, widget placement, result printing, and Tkinter event handling
are outside the measured interval.

## Importing the solver

`ORCSolver` is also a Python package. Classes can be imported from the package
root:

```python
from ORCSolver import ORCColumn, ORCRow, ORCWidget, HorizontalFlow, VerticalFlow
```

Direct module imports are also available:

```python
from ORCSolver.flow_solver import horizontal_flow
from ORCSolver.orclayout_classes import Pivot
```

## Tests

From the repository root, run:

```bash
python -m unittest discover -v
```

The legacy CLI tests verify custom window sizes, headless output, and
single-line time-only output for every original runnable example.
