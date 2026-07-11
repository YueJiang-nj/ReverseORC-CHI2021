"""Hierarchical versions of the original ORC visual examples.

Every scenario uses the same solver and renderer.  Resize the window to solve
the hierarchy again; the status line reports elapsed time and local solve count.
"""

import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from hierarchical_solver import Box, Group, HierarchicalSolver, Size, Widget


BUTTON = (Size(40, 80, 120), Size(40, 80, 120))
FLEX = Size(0, 300, float("inf"))


def widgets(prefix, count, width=BUTTON[0], height=BUTTON[1], weight=1.0):
    return [Widget("%s_%d" % (prefix, i + 1), width, height, weight) for i in range(count)]


def simple_flow():
    top = Group("top_toolbar", widgets("top", 8), "horizontal_flow", gap=3)
    left = Group("left_toolbar", widgets("left", 6), "vertical_flow", gap=3)
    content = Widget("text_area", FLEX, FLEX, 0.00001)
    body = Group("body", [left, content], "row", gap=4)
    return "Simple flow pattern", Group("canvas", [top, body], "column", gap=4), 640, 320


def connected_flow():
    # The common body parent coordinates the two toolbars, replacing the
    # legacy solver's explicit connected-flow pointer.
    top = Group("connected_top", widgets("top", 6), "horizontal_flow", gap=3)
    left = Group("connected_left", widgets("left", 4), "vertical_flow", gap=3)
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
    left = Group("optional_left_toolbar", widgets("left", 6), "vertical_flow", gap=3)
    body = Group("body", [left, Widget("text_area", FLEX, FLEX, 0.00001)], "row", gap=4)
    return "Optional widgets pattern", Group("canvas", [top, body], "column", gap=4), 640, 400


def balanced_flow():
    # Six controls naturally choose balanced factor-like rows as the window
    # crosses 1x6, 2x3, and 3x2 capacities.
    toolbar = Group("balanced_toolbar", widgets("balanced", 6),
                    "horizontal_flow", gap=4)
    text = Widget("text_area", FLEX, FLEX, 0.00001)
    return "Balanced flow pattern", Group("canvas", [toolbar, text], "column", gap=4), 240, 500


def teaser():
    top = Group("HF1", widgets("tool", 8, Size(40, 80, 80), Size(40, 80, 80)),
                "horizontal_flow")
    cards = Group("HF2", [
        Widget("CHI2020", Size(160, 320, 320), Size(120, 240, 240)),
        Widget("CHI2019", Size(0, 320, 320), Size(0, 240, 240), 0.000001),
    ], "horizontal_flow")
    actions = Group("HF3", [
        Widget("message", Size(80, 160, 160), Size(40, 80, 80)),
        Widget("blank1", Size(80, 320, 320), Size(40, 80, 80)),
        Widget("send", Size(80, 160, 160), Size(40, 80, 80)),
        Widget("email", Size(80, 160, 160), Size(40, 80, 80)),
        Widget("blank2", Size(80, 320, 320), Size(40, 80, 80)),
        Widget("clear", Size(80, 160, 160), Size(40, 80, 80)),
    ], "horizontal_flow")
    return "Teaser example", Group("canvas", [top, cards, actions], "column"), 640, 480


def video():
    top = Group("HF", widgets("top", 10, Size(20, 80, 80), Size(20, 80, 80)),
                "horizontal_flow")
    left = Group("VF", widgets("left", 6, Size(20, 80, 80), Size(20, 80, 80)),
                 "vertical_flow")
    logos = Group("VL", [
        Widget("CHI2020", Size(160, 320, 320), Size(120, 240, 240), 0.001),
        Widget("CHI2019", Size(0, 320, 320), Size(0, 240, 240), 0.00001),
    ], "vertical_flow")
    return "Video example", Group("canvas", [top, Group("body", [left, logos], "row")], "column"), 400, 640


def flow_around():
    # Four DOM groups surround a fixed center region. This preserves the visual
    # intent of FlowAroundFix while keeping each region independently solvable.
    small = (Size(20, 50, 80), Size(20, 50, 80))
    upper = Group("upper_flow", widgets("fruit_upper", 24, *small), "horizontal_flow", gap=2)
    left = Group("left_flow", widgets("fruit_left", 18, *small), "horizontal_flow", gap=2)
    fixed = Widget("fixed_CHI2020", Size(140, 160, 200), Size(140, 160, 200), 100)
    right = Group("right_flow", widgets("fruit_right", 18, *small), "horizontal_flow", gap=2)
    middle = Group("middle", [left, fixed, right], "row", gap=2)
    lower = Group("lower_flow", widgets("fruit_lower", 40, *small), "horizontal_flow", gap=2)
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
    COLORS = ("#70a1ff", "#7bed9f", "#ffa502", "#ff6b81", "#a29bfe", "#81ecec")

    def __init__(self, scenario):
        self.scenario = scenario
        title, self.layout, width, height = SCENARIOS[scenario]()
        self.root = tk.Tk()
        self.root.title("Hierarchical ORC — " + title)
        self.canvas = tk.Canvas(self.root, background="#f5f6fa", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.status = tk.StringVar()
        tk.Label(self.root, textvariable=self.status, anchor="w").pack(fill="x")
        self.root.geometry("%dx%d" % (width, height + 24))
        self.root.bind("<Configure>", self._schedule)
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

    def draw(self):
        self._pending = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 2 or height < 2:
            return
        started = time.perf_counter()
        try:
            result = HierarchicalSolver().solve(self.layout, width, height)
        except ValueError as error:
            self.canvas.delete("all")
            self.canvas.create_text(12, 12, anchor="nw", text="No feasible layout:\n" + str(error), fill="#c0392b")
            self.status.set("Resize the window to satisfy minimum sizes")
            return
        elapsed = (time.perf_counter() - started) * 1000
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
            color = self.COLORS[index % len(self.COLORS)]
            self.canvas.create_rectangle(box.left + 1, box.top + 1, box.right - 1, box.bottom - 1,
                                         fill=color, outline="#2f3542")
            asset = pattern_asset(self.scenario, name)
            if asset is not None:
                self._draw_image(name, box, asset)
            elif box.width > 28 and box.height > 18:
                self.canvas.create_text(box.left + box.width / 2, box.top + box.height / 2,
                                        text=name, width=max(20, box.width - 6), font=("TkDefaultFont", 8))
        self.status.set("%.2f ms  •  %d local group solves  •  %d levels" %
                        (elapsed, result.local_solves, result.levels_solved))

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


def run(name):
    if name not in SCENARIOS:
        raise ValueError("unknown scenario %r" % name)
    PatternWindow(name).run()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "simple_flow")
