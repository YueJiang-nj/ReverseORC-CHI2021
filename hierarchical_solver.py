"""Fast, compositional layout solving.

The legacy ORC solver builds one constraint system along every root-to-leaf
path.  This module offers a complementary solver for layouts whose DOM/group
structure is known: a group is represented by one box at its parent level,
then its children are solved inside the box assigned to that group.

Only sibling boxes participate in the same numeric solve.  Consequently the
largest solve is bounded by the largest sibling set rather than by the total
number of widgets in the document.
"""

from dataclasses import dataclass, field
from math import inf
from typing import Dict, Iterable, List, Sequence, Tuple, Union


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
        """Create a hierarchical widget without changing the legacy class."""
        return cls(
            widget.name,
            Size(widget.width_min, widget.width_pref, widget.width_max),
            Size(widget.height_min, widget.height_pref, widget.height_max),
            widget.weight,
        )


Node = Union[Widget, "Group"]


@dataclass
class Group:
    """A DOM-like container.

    ``direction`` is ``row``, ``column``, ``horizontal_flow``, or
    ``vertical_flow``. Rows and columns never wrap; flows preserve child order
    and wrap greedily at preferred size while always respecting minimum size.
    """

    name: str
    children: List[Node]
    direction: str = "row"
    gap: float = 0.0
    weight: float = 1.0

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

    def legacy_boundaries(self):
        """Return the ``name_l/r/t/b`` dictionary used by ORC examples."""
        result = {}
        for name, box in self.boxes.items():
            result.update({
                name + "_l": round(box.left), name + "_r": round(box.right),
                name + "_t": round(box.top), name + "_b": round(box.bottom),
            })
        return result


def _sum_size(sizes: Iterable[Size], gaps: float) -> Size:
    sizes = list(sizes)
    return Size(
        sum(s.minimum for s in sizes) + gaps,
        sum(s.preferred for s in sizes) + gaps,
        sum(s.maximum for s in sizes) + gaps,
    )


def _max_size(sizes: Iterable[Size]) -> Size:
    sizes = list(sizes)
    return Size(
        max(s.minimum for s in sizes),
        max(s.preferred for s in sizes),
        max(s.maximum for s in sizes),
    )


def intrinsic(node: Node) -> Tuple[Size, Size]:
    """Compute the compact min/preferred/max proxy exposed to the parent."""
    if isinstance(node, Widget):
        return node.width, node.height
    child_sizes = [intrinsic(child) for child in node.children]
    gaps = node.gap * (len(node.children) - 1)
    if node.direction == "horizontal_flow":
        widths = [s[0] for s in child_sizes]
        heights = [s[1] for s in child_sizes]
        # A wrapping flow can be as narrow as its widest item. Its maximum
        # height allows the all-items-wrapped case; the parent refines this
        # estimate using its actual width during top-down allocation.
        return (
            Size(max(s.minimum for s in widths),
                 sum(s.preferred for s in widths) + gaps,
                 sum(s.maximum for s in widths) + gaps),
            Size(max(s.minimum for s in heights),
                 max(s.preferred for s in heights),
                 sum(s.maximum for s in heights) + gaps),
        )
    if node.direction == "vertical_flow":
        widths = [s[0] for s in child_sizes]
        heights = [s[1] for s in child_sizes]
        return (
            Size(max(s.minimum for s in widths),
                 max(s.preferred for s in widths),
                 sum(s.maximum for s in widths) + gaps),
            Size(max(s.minimum for s in heights),
                 sum(s.preferred for s in heights) + gaps,
                 sum(s.maximum for s in heights) + gaps),
        )
    horizontal = node.direction == "row"
    primary = _sum_size((s[0 if horizontal else 1] for s in child_sizes), gaps)
    cross = _max_size(s[1 if horizontal else 0] for s in child_sizes)
    return (primary, cross) if horizontal else (cross, primary)


def _allocate(sizes: Sequence[Size], weights: Sequence[float], available: float,
              fill: bool = True) -> List[float]:
    """Weighted least-squares projection onto bounds and an optional sum."""
    minimum = sum(s.minimum for s in sizes)
    maximum = sum(s.maximum for s in sizes)
    if available + 1e-8 < minimum:
        raise ValueError("container is smaller than the children's minimum size")
    target = min(available, maximum) if fill else min(available, sum(s.preferred for s in sizes))
    target = max(target, minimum)

    # x_i = clamp(pref_i + lambda/(2*w_i), min_i, max_i). Bisection finds
    # lambda. This is the exact convex optimum but avoids constructing CVXPY.
    safe_weights = [max(float(w), 1e-12) for w in weights]
    lo, hi = -1.0, 1.0

    def values(lam):
        return [min(s.maximum, max(s.minimum, s.preferred + lam / (2 * w)))
                for s, w in zip(sizes, safe_weights)]

    while sum(values(lo)) > target:
        lo *= 2
    while sum(values(hi)) < target:
        hi *= 2
    for _ in range(70):
        mid = (lo + hi) / 2
        if sum(values(mid)) < target:
            lo = mid
        else:
            hi = mid
    return values((lo + hi) / 2)


class HierarchicalSolver:
    """Bottom-up measurement followed by top-down, level-local solving."""

    def solve(self, root: Group, width: float, height: float,
              left: float = 0.0, top: float = 0.0) -> LayoutResult:
        if width < 0 or height < 0:
            raise ValueError("canvas dimensions cannot be negative")
        root_width, root_height = intrinsic(root)
        if width < root_width.minimum or height < root_height.minimum:
            raise ValueError("canvas is smaller than the root's minimum intrinsic size")
        result = LayoutResult()
        self._place(root, Box(left, top, width, height), result, 0)
        return result

    def _place(self, node: Node, box: Box, result: LayoutResult, depth: int):
        if node.name in result.boxes:
            raise ValueError("node names must be unique: %s" % node.name)
        result.boxes[node.name] = box
        result.levels_solved = max(result.levels_solved, depth + 1)
        if isinstance(node, Widget):
            result.objective += node.weight * (
                (box.width - node.width.preferred) ** 2 +
                (box.height - node.height.preferred) ** 2)
            return

        result.local_solves += 1
        if node.direction in ("row", "column"):
            self._place_linear(node, box, result, depth)
        else:
            self._place_flow(node, box, result, depth)

    def _place_linear(self, group: Group, box: Box, result: LayoutResult, depth: int):
        horizontal = group.direction == "row"
        measured = [intrinsic(child) for child in group.children]
        # Refine a wrapping child's cross-axis proxy now that the parent has a
        # concrete cross-axis extent. This is what lets a column reserve two
        # toolbar rows when its width causes wrapping.
        for index, child in enumerate(group.children):
            if not isinstance(child, Group):
                continue
            if not horizontal and child.direction == "horizontal_flow":
                cross = self._flow_cross_size(child, box.width, True)
                measured[index] = (measured[index][0], cross)
            elif horizontal and child.direction == "vertical_flow":
                cross = self._flow_cross_size(child, box.height, False)
                measured[index] = (cross, measured[index][1])
        sizes = [item[0 if horizontal else 1] for item in measured]
        weights = [child.weight for child in group.children]
        extent = (box.width if horizontal else box.height) - group.gap * (len(sizes) - 1)
        allocated = _allocate(sizes, weights, extent)
        cursor = box.left if horizontal else box.top
        for child, length in zip(group.children, allocated):
            child_box = (Box(cursor, box.top, length, box.height) if horizontal else
                         Box(box.left, cursor, box.width, length))
            self._place(child, child_box, result, depth + 1)
            cursor += length + group.gap

    def _flow_cross_size(self, group: Group, capacity: float, horizontal: bool):
        lines = self._flow_lines(group, capacity, horizontal)
        line_sizes = []
        for line in lines:
            measured = [intrinsic(child) for child in line]
            line_sizes.append(_max_size(s[1 if horizontal else 0] for s in measured))
        gaps = group.gap * (len(lines) - 1)
        return _sum_size(line_sizes, gaps)

    def _flow_lines(self, group: Group, capacity: float, horizontal: bool):
        lines, current, used_min, used_pref = [], [], 0.0, 0.0
        for child in group.children:
            size = intrinsic(child)[0 if horizontal else 1]
            extra = group.gap if current else 0.0
            # Prefer wrapping before distortion, but never make a line whose
            # minimum cannot fit. This is the important quality/safety guard.
            if current and (used_pref + extra + size.preferred > capacity or
                            used_min + extra + size.minimum > capacity):
                lines.append(current)
                current, used_min, used_pref, extra = [], 0.0, 0.0, 0.0
            if size.minimum > capacity + 1e-8:
                raise ValueError("a flow child is wider/taller than its container")
            current.append(child)
            used_min += extra + size.minimum
            used_pref += extra + size.preferred
        if current:
            lines.append(current)
        return lines

    def _place_flow(self, group: Group, box: Box, result: LayoutResult, depth: int):
        horizontal = group.direction == "horizontal_flow"
        capacity = box.width if horizontal else box.height
        lines = self._flow_lines(group, capacity, horizontal)
        line_cross_sizes = []
        for line in lines:
            measured = [intrinsic(child) for child in line]
            line_cross_sizes.append(_max_size(s[1 if horizontal else 0] for s in measured))
        cross_capacity = (box.height if horizontal else box.width) - group.gap * (len(lines) - 1)
        line_extents = _allocate(line_cross_sizes, [1.0] * len(lines), cross_capacity)

        cross_cursor = box.top if horizontal else box.left
        for line, cross_extent in zip(lines, line_extents):
            measured = [intrinsic(child) for child in line]
            primary_sizes = [s[0 if horizontal else 1] for s in measured]
            primary_capacity = capacity - group.gap * (len(line) - 1)
            lengths = _allocate(primary_sizes, [child.weight for child in line],
                                primary_capacity, fill=False)
            cursor = box.left if horizontal else box.top
            for child, length in zip(line, lengths):
                child_box = (Box(cursor, cross_cursor, length, cross_extent) if horizontal else
                             Box(cross_cursor, cursor, cross_extent, length))
                self._place(child, child_box, result, depth + 1)
                cursor += length + group.gap
            cross_cursor += cross_extent + group.gap
