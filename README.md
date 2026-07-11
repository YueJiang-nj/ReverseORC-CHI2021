# ReverseORC-CHI2021

This repository contains the hierarchical ReverseORC GUI layout solver for DOM-like widget trees. The hierarchical solver measures groups bottom-up and places them top-down, solving only siblings together. This keeps local solve sizes small while parent groups continue to coordinate the space assigned to their children.

The repository is organized into three directories:

```text
ReverseORC_CHI2021/
├── images/
├── ORCSolver/          # Original non-hierarchical solver (ORCSolver)
└── ReverseORCSolver/   # New hierarchical solver
```

## Requirements

The examples use Python 3, Tkinter, Pillow, CVXPY, and NumPy. Install the
Python packages with:

```bash
python -m pip install pillow cvxpy numpy
```

Tkinter is included with many Python distributions. Test it with
`python -m tkinter`; if that fails, install Tk support through your Python or
operating-system package manager. Image assets are loaded from `images/`:

```text
ReverseORC_CHI2021/
├── images/
├── ORCSolver/
└── ReverseORCSolver/
```

## Hierarchical examples

From the repository root, run the hierarchical examples with:

```bash
python ReverseORCSolver/hierarchical_teaser_example.py
python ReverseORCSolver/hierarchical_video_example.py
python ReverseORCSolver/hierarchical_simple_flow_pattern.py
python ReverseORCSolver/hierarchical_connected_flow_pattern.py
python ReverseORCSolver/hierarchical_optional_widgets_pattern.py
python ReverseORCSolver/hierarchical_balanced_flow_pattern.py
python ReverseORCSolver/hierarchical_flow_around_pattern.py
```


## Choosing the window size

Pass the width and height as positional arguments:

```bash
python ReverseORCSolver/hierarchical_teaser_example.py 1046 760
python ReverseORCSolver/hierarchical_video_example.py 400 640
```

If dimensions are omitted, each example uses its original default size. The
teaser default is 640×480.

## Running without a window

Use `--headless` to skip the GUI and print the solving time and every resulting
group/widget box:

```bash
python ReverseORCSolver/hierarchical_teaser_example.py 1046 760 --headless
```

Example output:

```text
pattern: teaser
window: 1046 x 760
solver_time_seconds: 0.000616626
local_solves: 7
levels: 5
result:
  canvas: left=0.000 top=0.000 width=1046.000 height=760.000
  HF1: left=0.000 top=0.000 width=80.000 height=760.000
  ...
```

Use `--time-only` for benchmarking. It opens no window and prints one numeric
line containing only the solver time in seconds:

```bash
python ReverseORCSolver/hierarchical_teaser_example.py 1046 760 --time-only
```

Example output:

```text
0.000773083
```

`--headless` and `--time-only` are mutually exclusive and are available on all
hierarchical example scripts.

## Original non-hierarchical examples

The original runnable examples support the same positional size arguments and
output modes:

```bash
python ORCSolver/teaser_example.py 640 480
python ORCSolver/video_example.py 400 640
python ORCSolver/simple_flow_pattern.py 640 320
python ORCSolver/connected_flow_pattern.py 640 240
python ORCSolver/optional_widgets_pattern.py 800 800
python ORCSolver/balanced_flow_pattern.py 240 500
python ORCSolver/flow_around_pattern.py 600 600
```

Run an original example without Tk windows and print its time and result:

```bash
python ORCSolver/video_example.py 890 365 --headless
```

Print only its solver time as one numeric line:

```bash
python ORCSolver/video_example.py 890 365 --time-only
```

These options apply to runnable example and pattern files. The original solver
is isolated in the `ORCSolver/` directory. Library modules such as
`ORCSolver/flow_solver.py`, `ORCSolver/orclayout_classes.py`,
`ReverseORCSolver/hierarchical_solver.py`, and `ORCSolver/legacy_cli.py` are
imported APIs and therefore do not expose example CLI options.

## Timing definition

Reported time includes only calls to `HierarchicalSolver.solve()`. It excludes:

- hierarchy and GUI construction;
- responsive pivot selection;
- PIL image loading and resizing;
- ImageTk conversion;
- Canvas drawing and window updates;
- terminal result formatting.

For the teaser, both responsive root-pivot candidates are solved. The reported
solver time is the sum of those solver calls; construction and selection of the
winning candidate remain excluded.

## Using the hierarchical solver directly

Run this example from the `ReverseORCSolver` directory:

```bash
cd ReverseORCSolver
```

```python
from hierarchical_solver import Group, HierarchicalSolver, Size, Widget

first_toolbar = Group(
    "group_1",
    [Widget(f"widget_{i}", Size(40, 80, 120), Size(40, 60, 80))
     for i in range(1, 6)],
    direction="horizontal_flow",
    gap=8,
)

second_toolbar = Group(
    "group_2",
    [Widget(f"widget_{i}", Size(40, 80, 120), Size(40, 60, 80))
     for i in range(6, 11)],
    direction="horizontal_flow",
    gap=8,
)

dom = Group("canvas", [first_toolbar, second_toolbar], direction="column")
result = HierarchicalSolver().solve(dom, width=500, height=180)

print(result.boxes["group_1"])
print(result.boxes["widget_1"])
```

Existing `ORCWidget` instances can be adapted with:

```python
hierarchical_widget = Widget.from_orc_widget(existing_orc_widget)
```

`LayoutResult.legacy_boundaries()` returns `name_l`, `name_r`, `name_t`, and
`name_b` values compatible with the original example result format.

## Tests

From the repository root, run both test suites with:

```bash
python -m unittest discover -s ORCSolver -v
python -m unittest discover -s ReverseORCSolver -v
```

The tests cover hierarchical containment, weighted allocation, flow wrapping,
legacy boundary output, all visual patterns, responsive teaser pivots,
corresponding-element size equality, image availability, custom window sizes,
and time-only output.

More implementation details are available in
[`HIERARCHICAL_SOLVER.md`](ReverseORCSolver/HIERARCHICAL_SOLVER.md).
