"""Python API for the native C++ hierarchical ReverseORC solver."""

from dataclasses import dataclass, field
from math import inf
from typing import Dict, List, Union

import _reverse_orc_cpp


@dataclass(frozen=True)
class Size:
    minimum: float
    preferred: float
    maximum: float = inf

    def __post_init__(self):
        if not (0 <= self.minimum <= self.preferred <= self.maximum):
            raise ValueError("sizes must satisfy 0 <= minimum <= preferred <= maximum")


@dataclass
class Widget:
    name: str
    width: Size
    height: Size
    weight: float = 1.0

    @classmethod
    def from_orc_widget(cls, widget):
        return cls(
            widget.name,
            Size(widget.width_min, widget.width_pref, widget.width_max),
            Size(widget.height_min, widget.height_pref, widget.height_max),
            widget.weight,
        )


Node = Union[Widget, "Group"]


@dataclass
class Group:
    name: str
    children: List[Node]
    direction: str = "row"
    gap: float = 0.0
    weight: float = 1.0
    fill: bool = False
    uniform: bool = False
    balanced: bool = False

    def __post_init__(self):
        valid = {"row", "column", "horizontal_flow", "vertical_flow"}
        if self.direction not in valid:
            raise ValueError("direction must be one of %s" % sorted(valid))
        if not self.children:
            raise ValueError("a group must contain at least one child")
        if self.gap < 0:
            raise ValueError("gap cannot be negative")


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    width: float
    height: float

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


@dataclass
class LayoutResult:
    boxes: Dict[str, Box] = field(default_factory=dict)
    objective: float = 0.0
    levels_solved: int = 0
    local_solves: int = 0
    solver_seconds: float = 0.0

    def legacy_boundaries(self):
        result = {}
        for name, box in self.boxes.items():
            result.update({
                name + "_l": round(box.left),
                name + "_r": round(box.right),
                name + "_t": round(box.top),
                name + "_b": round(box.bottom),
            })
        return result


def _size(size):
    return (size.minimum, size.preferred, size.maximum)


def _serialize(node):
    if isinstance(node, Widget):
        return {
            "kind": "widget",
            "name": node.name,
            "width": _size(node.width),
            "height": _size(node.height),
            "weight": node.weight,
        }
    if not isinstance(node, Group):
        raise TypeError("root and children must be Widget or Group instances")
    return {
        "kind": "group",
        "name": node.name,
        "children": [_serialize(child) for child in node.children],
        "direction": node.direction,
        "gap": node.gap,
        "weight": node.weight,
        "fill": node.fill,
        "uniform": node.uniform,
        "balanced": node.balanced,
    }


class HierarchicalSolver:
    """API-compatible wrapper whose solving implementation is native C++."""

    def solve(self, root, width, height, left=0.0, top=0.0):
        if not isinstance(root, Group):
            raise TypeError("root must be a Group")
        native = _reverse_orc_cpp.solve(_serialize(root), width, height, left, top)
        return LayoutResult(
            boxes={name: Box(*values) for name, values in native["boxes"].items()},
            objective=native["objective"],
            levels_solved=native["levels_solved"],
            local_solves=native["local_solves"],
            solver_seconds=native["solver_seconds"],
        )
