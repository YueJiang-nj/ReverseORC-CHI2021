# ReverseORCSolver C++

This directory contains a native C++17 implementation of the hierarchical
ReverseORC solver. Python constructs the layout tree and calls a small CPython
extension; measurement, flow wrapping, weighted allocation, and box placement
all execute in C++.

The Python API mirrors the existing hierarchical solver: `Size`, `Widget`,
`Group`, `Box`, `LayoutResult`, and `HierarchicalSolver` are available from
`hierarchical_solver_cpp`.

## Build

Requirements:

- Python 3
- a C++17 compiler
- setuptools
- Pillow and Tkinter for the visual examples

Build the extension in place:

```bash
cd ReverseORCSolver_C++
python setup.py build_ext --inplace
```

No CVXPY, NumPy, or pybind11 dependency is required.

## Use from Python

```python
from hierarchical_patterns import teaser_layout
from hierarchical_solver_cpp import HierarchicalSolver

root = teaser_layout("column")
result = HierarchicalSolver().solve(root, width=640, height=480)
print(result.boxes["CHI2020"])
```

Run the complete example and tests:

```bash
python hierarchical_teaser_example.py 640 480 --headless
python -m unittest -v
```

## Visual patterns

The C++ backend includes the same seven responsive patterns as the Python
`ReverseORCSolver` implementation. Each opens the Tkinter canvas and timing
window and re-solves through the native extension when resized:

```bash
python hierarchical_teaser_example.py
python hierarchical_video_example.py
python hierarchical_simple_flow_pattern.py
python hierarchical_connected_flow_pattern.py
python hierarchical_optional_widgets_pattern.py
python hierarchical_balanced_flow_pattern.py
python hierarchical_flow_around_pattern.py
```

Every launcher accepts optional width and height arguments:

```bash
python hierarchical_teaser_example.py 640 480
```

Use `--headless` to print native solver results without opening windows, or
`--time-only` to print one numeric timing value:

```bash
python hierarchical_teaser_example.py 640 480 --headless
python hierarchical_teaser_example.py 640 480 --time-only
```

The reported time is measured with `std::chrono::steady_clock` immediately
around the native C++ `Solver::solve()` call. It excludes Python layout-tree
serialization, conversion into C++ nodes, conversion of result boxes back to
Python, GUI work, rendering, and output formatting. For the teaser, it is the
sum of the two native orientation solves.

## Files

- `cpp/hierarchical_solver.cpp`: C++ solver and CPython binding.
- `hierarchical_solver_cpp.py`: Python-facing data classes and serializer.
- `hierarchical_patterns.py`: shared C++-backed scenarios and GUI renderer.
- `hierarchical_*_example.py` and `hierarchical_*_pattern.py`: pattern launchers.
- `setup.py`: local native-extension build.
- `test_cpp_solver.py`: native solver behavior tests.
- `test_cpp_patterns.py`: visual geometry, assets, pivots, and timing tests.
