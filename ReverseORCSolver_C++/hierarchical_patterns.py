"""Hierarchical versions of the original ORC visual examples.

Every scenario uses the same solver and renderer.  Resize the window to solve
the hierarchy again; the status line reports elapsed time and local solve count.
"""

import sys
import tkinter as tk
import argparse
from pathlib import Path

from PIL import Image, ImageTk

from hierarchical_solver_cpp import Box, Group, HierarchicalSolver, Size, Widget


BUTTON = (Size(40, 80, 120), Size(40, 80, 120))
FLEX = Size(0, 300, float("inf"))


def widgets(prefix, count, width=BUTTON[0], height=BUTTON[1], weight=1.0):
    return [Widget("%s_%d" % (prefix, i + 1), width, height, weight) for i in range(count)]


def simple_flow():
    top = Group("top_toolbar", widgets("top", 8), "horizontal_flow", gap=3,
                uniform=True, balanced=True)
    left = Group("left_toolbar", widgets("left", 6), "vertical_flow", gap=3,
                 uniform=True, balanced=True)
    content = Widget("text_area", FLEX, FLEX, 0.00001)
    body = Group("body", [left, content], "row", gap=4)
    return "Simple flow pattern", Group("canvas", [top, body], "column", gap=4), 640, 320


def connected_flow():
    # The common body parent coordinates the two toolbars, replacing the
    # legacy solver's explicit connected-flow pointer.
    top = Group("connected_top", widgets("top", 6), "horizontal_flow", gap=3,
                uniform=True, balanced=True)
    left = Group("connected_left", widgets("left", 4), "vertical_flow", gap=3,
                 uniform=True, balanced=True)
    content = Widget("text_area", FLEX, FLEX, 0.00001)
    body = Group("connected_body", [left, content], "row", gap=4)
    return "Connected flow pattern", Group("canvas", [top, body], "column", gap=4), 640, 240


def optional_widgets():
    # Low-priority items have zero minimum size, so they yield space before the
    # required controls while remaining visible whenever capacity permits.
    required_top = widgets("required_top", 8)
    optional_top = widgets("optional_top", 4, Size(0, 60, 80), Size(0, 60, 80), 0.001)
    top = Group("optional_top_toolbar", required_top + optional_top,
                "horizontal_flow", gap=3)
    left = Group("optional_left_toolbar", widgets("left", 6), "vertical_flow", gap=3,
                 uniform=True, balanced=True)
    body = Group("body", [left, Widget("text_area", FLEX, FLEX, 0.00001)], "row", gap=4)
    return "Optional widgets pattern", Group("canvas", [top, body], "column", gap=4), 640, 400


def balanced_flow():
    # Six controls naturally choose balanced factor-like rows as the window
    # crosses 1x6, 2x3, and 3x2 capacities.
    toolbar = Group("balanced_toolbar", widgets("balanced", 6),
                    "horizontal_flow", gap=4, uniform=True, balanced=True)
    text = Widget("text_area", FLEX, FLEX, 0.00001)
    return "Balanced flow pattern", Group("canvas", [toolbar, text], "column", gap=4), 240, 500


def teaser():
    return "Teaser example", teaser_layout("column"), 640, 480


def teaser_layout(root_orientation="column"):
    # The legacy flow solver treats nominally fixed teaser dimensions as soft
    # bounds and stretches/shrinks them when the window changes. Zero/inf outer
    # bounds reproduce that behavior while retaining the same preferences.
    def soft(preferred):
        return Size(0, preferred, float("inf"))

    top_direction = "horizontal_flow" if root_orientation == "column" else "vertical_flow"
    if root_orientation == "column":
        top_width, top_height = soft(80), Size(80, 80, 80)
    else:
        top_width, top_height = Size(80, 80, 80), soft(80)
    top = Group("HF1", widgets("tool", 8, top_width, top_height), top_direction,
                fill=True, uniform=True, balanced=True)
    cards = Group("HF2", [
        Widget("CHI2020", soft(320), Size(0, 240, 240)),
        # These are peer logo cards. Equal specifications and weights ensure
        # neither card absorbs more resizing than the other.
        Widget("CHI2019", soft(320), Size(0, 240, 240)),
    ], "horizontal_flow", weight=1_000_000, fill=True,
       uniform=True, balanced=True)
    # These are semantic rows, not six interchangeable flow items. Explicit
    # row groups preserve correspondence across every window size:
    # message == email, entry1 == entry2, and send == clear.
    action_row_1 = Group("message_row", [
        Widget("message", soft(160), soft(80)),
        Widget("blank1", soft(320), soft(80)),
        Widget("send", soft(160), soft(80)),
    ], "row")
    action_row_2 = Group("email_row", [
        Widget("email", soft(160), soft(80)),
        Widget("blank2", soft(320), soft(80)),
        Widget("clear", soft(160), soft(80)),
    ], "row")
    actions = Group("HF3", [action_row_1, action_row_2], "column")
    main = Group("main", [cards, actions], "column")
    if root_orientation == "column":
        return Group("canvas", [top, cards, actions], "column")
    return Group("canvas", [top, main], "row")


def solve_teaser(width, height, return_timing=False):
    """Evaluate the same two pivot levels as teaser_example.py."""
    candidates = []
    solver_seconds = 0.0
    for root_orientation in ("column", "row"):
        layout = teaser_layout(root_orientation)
        try:
            result = HierarchicalSolver().solve(layout, width, height)
            solver_seconds += result.solver_seconds
        except ValueError:
            continue
        top_loss = sum(
            (result.boxes["tool_%d" % index].width - 80) ** 2 +
            (result.boxes["tool_%d" % index].height - 80) ** 2
            for index in range(1, 9)
        )
        candidates.append((root_orientation, top_loss,
                           result.objective, layout, result))
    if not candidates:
        raise ValueError("no teaser pivot orientation is feasible")
    # Pivot gives the primary toolbar orientation decision priority. Compare
    # its distortion first and preserve the legacy column-first tie-break;
    # then use whole-tree loss to choose the nested action-flow pivot.
    best_top_loss = min(item[1] for item in candidates)
    tolerance = max(1e-7, best_top_loss * 1e-9)
    tied = [item for item in candidates if item[1] <= best_top_loss + tolerance]
    chosen_root = min(tied, key=lambda item: 0 if item[0] == "column" else 1)[0]
    root_candidates = [item for item in candidates if item[0] == chosen_root]
    _root, _top_loss, _loss, layout, result = min(
        root_candidates, key=lambda item: item[2]
    )
    if return_timing:
        return layout, result, solver_seconds
    return layout, result


def solve_pattern(name, width, height):
    """Solve a scenario and return (layout, result, solver-only seconds)."""
    if name not in SCENARIOS:
        raise ValueError("unknown scenario %r" % name)
    if name == "teaser":
        return solve_teaser(width, height, return_timing=True)
    _title, layout, _default_width, _default_height = SCENARIOS[name]()
    result = HierarchicalSolver().solve(layout, width, height)
    return layout, result, result.solver_seconds


def video():
    stretch_80 = Size(80, 80, float("inf"))
    fixed_80 = Size(80, 80, 80)
    soft_logo_width = Size(0, 320, float("inf"))
    soft_logo_height = Size(0, 240, float("inf"))
    # HF keeps its 80px thickness but its buttons stretch horizontally. VF
    # keeps 80px column widths but stretches buttons vertically. This matches
    # the legacy flow solver's soft bound behavior.
    top = Group("HF", widgets("top", 10, stretch_80, fixed_80),
                "horizontal_flow", uniform=True, balanced=True)
    left = Group("VF", widgets("left", 6, fixed_80, stretch_80),
                 "vertical_flow", uniform=True, balanced=True)
    logos = Group("VL", [
        Widget("CHI2020", soft_logo_width, soft_logo_height, 0.001),
        Widget("CHI2019", soft_logo_width, soft_logo_height, 0.001),
    ], "vertical_flow", uniform=True, balanced=True)
    return "Video example", Group("canvas", [top, Group("body", [left, logos], "row")], "column"), 400, 640


def flow_around():
    # Four DOM groups surround a fixed center region. This preserves the visual
    # intent of FlowAroundFix while keeping each region independently solvable.
    # A common fixed cell size keeps all 100 repeated fruit widgets identical,
    # including widgets assigned to different regions around the center.
    small = (Size(40, 40, 40), Size(40, 40, 40))
    upper = Group("upper_flow", widgets("fruit_upper", 24, *small), "horizontal_flow", gap=2,
                  uniform=True, balanced=True)
    left = Group("left_flow", widgets("fruit_left", 18, *small), "horizontal_flow", gap=2,
                 uniform=True, balanced=True)
    fixed = Widget("fixed_CHI2020", Size(140, 160, 200), Size(140, 160, 200), 100)
    right = Group("right_flow", widgets("fruit_right", 18, *small), "horizontal_flow", gap=2,
                  uniform=True, balanced=True)
    middle = Group("middle", [left, fixed, right], "row", gap=2)
    lower = Group("lower_flow", widgets("fruit_lower", 40, *small), "horizontal_flow", gap=2,
                  uniform=True, balanced=True)
    return "Flow around fixed area", Group("canvas", [upper, middle, lower], "column", gap=2), 600, 600


SCENARIOS = {
    "simple_flow": simple_flow,
    "connected_flow": connected_flow,
    "optional_widgets": optional_widgets,
    "balanced_flow": balanced_flow,
    "teaser": teaser,
    "video": video,
    "flow_around": flow_around,
}


IMAGE_DIRECTORY = Path(__file__).resolve().parent.parent / "images"


def pattern_asset(scenario, name):
    """Return the same image assets used by the corresponding legacy demo."""
    if scenario == "teaser":
        return teaser_asset(name)
    if scenario == "simple_flow":
        if name.startswith("top_"):
            return "%d.png" % int(name.split("_")[-1]), None
        if name.startswith("left_"):
            return "%d.png" % int(name.split("_")[-1]), None
        if name == "text_area":
            return "text.jpg", None
    if scenario == "connected_flow":
        if name.startswith("top_"):
            return "%d.png" % int(name.split("_")[-1]), None
        if name.startswith("left_"):
            number = int(name.split("_")[-1])
            return "color%s.png" % (str(number) * 2), None
        if name == "text_area":
            return "text.jpg", None
    if scenario == "optional_widgets":
        if name.startswith("required_top_"):
            number = int(name.split("_")[-1])
            return "%d.png" % ((number - 1) % 10 + 1), None
        if name.startswith("optional_top_"):
            number = int(name.split("_")[-1]) + 8
            return "%d.png" % ((number - 1) % 10 + 1), None
        if name.startswith("left_"):
            number = int(name.split("_")[-1])
            return "%s.png" % (str(number) * 2), None
        if name == "text_area":
            return "text.jpg", None
    if scenario == "balanced_flow":
        if name.startswith("balanced_"):
            return "%d.png" % int(name.split("_")[-1]), None
        if name == "text_area":
            return "text.jpg", None
    if scenario == "video":
        if name.startswith("top_"):
            return "%d.png" % int(name.split("_")[-1]), None
        if name.startswith("left_"):
            number = int(name.split("_")[-1])
            return "%s.png" % (str(number) * 2), None
        if name in ("CHI2020", "CHI2019"):
            return name + ".png", None
    if scenario == "flow_around":
        if name.startswith("fruit_"):
            return "pineapple.jpg", None
        if name == "fixed_CHI2020":
            return "CHI2020.png", None
    return None


def teaser_asset(name):
    """Return the image and original display size used by teaser_example.py."""
    if name.startswith("tool_"):
        return "%d.png" % int(name.split("_")[-1]), (80, 80)
    return {
        "CHI2020": ("CHI2020.png", (305, 225)),
        "CHI2019": ("CHI2019.png", (305, 225)),
        "message": ("message_new.png", (165, 60)),
        "blank1": ("blank.png", (140, 60)),
        "send": ("send_new.png", (100, 43)),
        "email": ("email_new.png", (150, 50)),
        "blank2": ("blank.png", (140, 60)),
        "clear": ("clear_new.png", (100, 43)),
    }.get(name)


class PatternWindow:
    def __init__(self, scenario, width=None, height=None):
        self.scenario = scenario
        title, self.layout, default_width, default_height = SCENARIOS[scenario]()
        width = default_width if width is None else width
        height = default_height if height is None else height
        self.root = tk.Tk()
        self.root.title("Canvas Layout")
        self.canvas = tk.Canvas(self.root, background="#ffffff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        # Every pattern follows the original teaser UI: an exact-size canvas
        # plus a separate timing window. Toplevel keeps both windows in the
        # same Tk application and event loop.
        self.time_panel = tk.Toplevel(self.root)
        self.time_panel.title("Time")
        time_frame = tk.Frame(self.time_panel)
        time_frame.pack(side=tk.TOP)
        tk.Label(time_frame, text="Time: ", font="Times 30").pack(side=tk.LEFT)
        self.time_result = tk.Entry(time_frame, font="Helvetica 30", width=10)
        self.time_result.pack(side=tk.LEFT)
        self.root.geometry("%dx%d" % (width, height))
        self.root.minsize(160, 160)
        self.root.bind("<Configure>", self._schedule)
        self.root.bind("<ButtonRelease-1>", self._resize_finished)
        self._pending = None
        self._source_images = {}
        self._tk_images = []
        self.root.after(1, self.draw)

    def _schedule(self, event):
        if event.widget is not self.root:
            return
        if self._pending is not None:
            self.root.after_cancel(self._pending)
        self._pending = self.root.after(60, self.draw)

    def _resize_finished(self, _event):
        # Native window resizing is enabled. Solve immediately when the user
        # releases the mouse, like teaser_example.py's resize callback.
        if self._pending is not None:
            self.root.after_cancel(self._pending)
        self._pending = self.root.after_idle(self.draw)

    def draw(self):
        self._pending = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 2 or height < 2:
            return
        try:
            self.layout, result, solve_seconds = solve_pattern(self.scenario, width, height)
        except ValueError as error:
            self.canvas.delete("all")
            self.canvas.create_text(12, 12, anchor="nw", text="No feasible layout:\n" + str(error), fill="#c0392b")
            self.time_result.delete(0, tk.END)
            self.time_result.insert(0, "No solution")
            return
        self.canvas.delete("all")
        self._tk_images = []
        groups = {node.name for node in walk(self.layout) if isinstance(node, Group)}
        for index, (name, box) in enumerate(result.boxes.items()):
            if name in groups:
                if name != "canvas":
                    self.canvas.create_rectangle(box.left, box.top, box.right, box.bottom,
                                                 outline="#57606f", dash=(3, 2))
                    self.canvas.create_text(box.left + 3, box.top + 3, text=name,
                                            anchor="nw", fill="#2f3542", font=("TkDefaultFont", 8))
                continue
            self.canvas.create_rectangle(box.left + 1, box.top + 1, box.right - 1, box.bottom - 1,
                                         fill="#ffffff", outline="#2f3542")
            asset = pattern_asset(self.scenario, name)
            if asset is not None:
                self._draw_image(name, box, asset)
            elif box.width > 28 and box.height > 18:
                self.canvas.create_text(box.left + box.width / 2, box.top + box.height / 2,
                                        text=name, width=max(20, box.width - 6), font=("TkDefaultFont", 8))
        if self.scenario == "teaser" and "email_row" in result.boxes:
            row = result.boxes["email_row"]
            self.canvas.create_line(row.left, row.top, row.right, row.top,
                                    fill="#2f3542", width=3)
        self.time_result.delete(0, tk.END)
        self.time_result.insert(0, "%.6f" % solve_seconds)

    def _draw_image(self, name, box, asset):
        filename, original_size = asset
        path = IMAGE_DIRECTORY / filename
        if not path.is_file():
            self.canvas.create_text(box.left + box.width / 2, box.top + box.height / 2,
                                    text=name + "\n(missing " + filename + ")", justify="center")
            return
        if path not in self._source_images:
            with Image.open(path) as image:
                self._source_images[path] = image.convert("RGBA")
        if original_size is None:
            width = max(1, round(box.width) - 4)
            height = max(1, round(box.height) - 4)
        else:
            width = max(1, min(round(box.width), original_size[0]))
            height = max(1, min(round(box.height), original_size[1]))
        resized = self._source_images[path].resize((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        self._tk_images.append(photo)  # Tk does not retain image references.
        self.canvas.create_image(box.left + box.width / 2, box.top + box.height / 2,
                                 image=photo, anchor="center")

    def run(self):
        self.root.mainloop()


def walk(node):
    yield node
    if isinstance(node, Group):
        for child in node.children:
            yield from walk(child)


def print_result(name, width, height):
    """Headless CLI output for benchmarking and result inspection."""
    _layout, result, solver_seconds = solve_pattern(name, width, height)
    print("pattern: %s" % name)
    print("window: %d x %d" % (width, height))
    print("solver_time_seconds: %.9f" % solver_seconds)
    print("local_solves: %d" % result.local_solves)
    print("levels: %d" % result.levels_solved)
    print("result:")
    for node_name, box in result.boxes.items():
        print("  %s: left=%.3f top=%.3f width=%.3f height=%.3f" %
              (node_name, box.left, box.top, box.width, box.height))
    return result, solver_seconds


def print_time(name, width, height):
    """Solve without a GUI and print only solver time for easy benchmarking."""
    _layout, result, solver_seconds = solve_pattern(name, width, height)
    print("%.9f" % solver_seconds)
    return result, solver_seconds


def run(name, width=None, height=None, headless=False):
    if name not in SCENARIOS:
        raise ValueError("unknown scenario %r" % name)
    _title, _layout, default_width, default_height = SCENARIOS[name]()
    width = default_width if width is None else width
    height = default_height if height is None else height
    if width <= 0 or height <= 0:
        raise ValueError("window width and height must be positive")
    if headless:
        return print_result(name, width, height)
    PatternWindow(name, width, height).run()


def run_cli(name):
    """Common width/height/headless command line interface for every demo."""
    _title, _layout, default_width, default_height = SCENARIOS[name]()
    parser = argparse.ArgumentParser(description="Hierarchical %s example" % name)
    parser.add_argument("width", nargs="?", type=int, default=default_width,
                        help="initial canvas width (default: %d)" % default_width)
    parser.add_argument("height", nargs="?", type=int, default=default_height,
                        help="initial canvas height (default: %d)" % default_height)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--headless", action="store_true",
                        help="print solver time and boxes without opening windows")
    output.add_argument("--time-only", action="store_true",
                        help="print only solver time without opening windows")
    args = parser.parse_args()
    if args.time_only:
        return print_time(name, args.width, args.height)
    return run(name, args.width, args.height, args.headless)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "simple_flow")
