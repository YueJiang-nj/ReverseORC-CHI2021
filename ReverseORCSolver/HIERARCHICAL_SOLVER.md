# Hierarchical solver

`hierarchical_solver.py` is a fast alternative for layouts that already have a
DOM-like grouping. It performs two passes:

1. Bottom-up measurement reduces every subtree to a min/preferred/max proxy.
2. Top-down placement optimizes only sibling proxy boxes, then solves each
   child group independently inside its allocated box.

This changes the numeric problem size from the total number of widgets to the
largest number of siblings at any one node. Parent solves still coordinate the
space given to groups, so independently solving toolbars does not mean choosing
their sizes independently.

```python
from hierarchical_patterns import teaser_layout
from hierarchical_solver import HierarchicalSolver

dom = teaser_layout("column")
result = HierarchicalSolver().solve(dom, width=640, height=480)

print(result.boxes["HF1"])
print(result.boxes["CHI2020"])
```

Existing `ORCWidget` objects can be reused:

```python
from hierarchical_solver import Widget

hierarchical_widget = Widget.from_orc_widget(existing_orc_widget)
```

## Quality behavior

- Sibling row/column sizing is the exact bounded, weighted least-squares
  optimum. Widget/group weights preserve priorities.
- A parent sees each child group's aggregate min/preferred/max size, preventing
  it from assigning space without considering the subtree.
- Flows preserve DOM order, wrap before preferred-size distortion, and reject
  assignments that violate minimum sizes.
- The result includes every group and widget box, an objective value, hierarchy
  depth, and the number of local solves. `legacy_boundaries()` returns the
  `name_l`, `name_r`, `name_t`, `name_b` keys used by the original examples.

The existing `ORCLayout.solve()` remains unchanged for layouts that need its
global pivot/connected-flow search. The hierarchical path is intended for the
common case where groups are known and cross-group constraints only concern the
groups' outer boxes.

## Visual examples

The hierarchical counterparts of every original example open a Tkinter window
and automatically re-solve when it is resized. Run these commands from the
`ReverseORCSolver` directory:

```shell
python hierarchical_teaser_example.py
python hierarchical_video_example.py
python hierarchical_simple_flow_pattern.py
python hierarchical_connected_flow_pattern.py
python hierarchical_optional_widgets_pattern.py
python hierarchical_balanced_flow_pattern.py
python hierarchical_flow_around_pattern.py
```

Each launcher also accepts optional width and height arguments. Use
`--headless` to print the layout without opening windows, or `--time-only` to
print only the solver time:

```shell
python hierarchical_teaser_example.py 640 480 --headless
python hierarchical_teaser_example.py 640 480 --time-only
```

## Tests

From the repository root, run the hierarchical tests with:

```shell
python -m unittest discover -s ReverseORCSolver -v
```

The shared implementation is in `hierarchical_patterns.py`. Each example uses
the same Tkinter structure as the teaser: a resizable `Canvas Layout` window
rendered with Pillow/ImageTk and a separate `Time` window reporting solver-only
time.
