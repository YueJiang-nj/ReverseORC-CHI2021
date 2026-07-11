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
from hierarchical_solver import Group, HierarchicalSolver, Size, Widget

def toolbar(name, first):
    items = [
        Widget(f"widget_{i}", Size(40, 80, 120), Size(40, 60, 80))
        for i in range(first, first + 5)
    ]
    return Group(name, items, direction="horizontal_flow", gap=8)

dom = Group(
    "canvas",
    [toolbar("group_1", 1), toolbar("group_2", 6)],
    direction="column",
    gap=12,
)
result = HierarchicalSolver().solve(dom, width=500, height=180)

print(result.boxes["group_1"])
print(result.boxes["widget_1"])
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
and automatically re-solve when it is resized:

```shell
python hierarchical_teaser_example.py
python hierarchical_video_example.py
python hierarchical_simple_flow_pattern.py
python hierarchical_connected_flow_pattern.py
python hierarchical_optional_widgets_pattern.py
python hierarchical_balanced_flow_pattern.py
python hierarchical_flow_around_pattern.py
```

The shared implementation is in `hierarchical_patterns.py`. Each window draws
group boundaries, widget boxes, and a status line containing solve time, number
of local group solves, and hierarchy depth.
