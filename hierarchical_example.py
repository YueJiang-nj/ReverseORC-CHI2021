"""Small headless example of two independently solved toolbar groups."""

from hierarchical_solver import Group, HierarchicalSolver, Size, Widget


def toolbar(name, start):
    widgets = [Widget("widget_%d" % i, Size(40, 80, 120), Size(40, 60, 80))
               for i in range(start, start + 5)]
    return Group(name, widgets, "horizontal_flow", gap=8)


if __name__ == "__main__":
    root = Group("canvas", [toolbar("group_1", 1), toolbar("group_2", 6)],
                 "column", gap=12)
    solved = HierarchicalSolver().solve(root, 500, 180)
    for name, box in solved.boxes.items():
        print(name, box)
    print("local solves:", solved.local_solves)

