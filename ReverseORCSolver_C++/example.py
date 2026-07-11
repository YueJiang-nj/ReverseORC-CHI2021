from hierarchical_solver_cpp import Group, HierarchicalSolver, Size, Widget


def toolbar(name, first):
    return Group(
        name,
        [
            Widget(f"widget_{index}", Size(40, 80, 120), Size(40, 60, 80))
            for index in range(first, first + 5)
        ],
        direction="horizontal_flow",
        gap=8,
    )


root = Group(
    "canvas",
    [toolbar("group_1", 1), toolbar("group_2", 6)],
    direction="column",
    gap=12,
)
result = HierarchicalSolver().solve(root, width=500, height=180)

for name, box in result.boxes.items():
    print(name, box)
print("local solves:", result.local_solves)
