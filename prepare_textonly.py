"""
prepare_textonly.py — Infrastructure for text-only drawing experiment.

Imports scoring from prepare.py and adds:
  - Stroke budget enforcement (50 strokes max)
  - Multi-target averaged scoring (across all 3 targets)
  - Anti-cheat: static source check + runtime file-access restriction

Do not modify this file.
"""

import os
import builtins
from pathlib import Path

from prepare import (
    launch_browser,
    get_canvas_bbox,
    compute_draw_loss,
    save_experiment_screenshot,
    cleanup,
    screenshot_canvas,
    SCREENSHOT_DIR,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_STROKES = 50
TARGET_IMAGES = [
    "targets/dog_in_snow.png",
    "targets/summer_night.png",
    "targets/pencil_portrait.png",
]
SCREENSHOT_DIR_TEXTONLY = "screenshots_textonly"


# ---------------------------------------------------------------------------
# Stroke budget enforcement
# ---------------------------------------------------------------------------

class StrokeBudgetExceeded(Exception):
    pass


class StrokeCountingMouse:
    """
    Wraps Playwright's page.mouse to count drawing strokes inside the canvas.

    A "stroke" = one mouse-down event inside the canvas bounding box.
    Tool/palette clicks outside the canvas are free and don't count.
    """

    def __init__(self, real_mouse, canvas_bbox, max_strokes=MAX_STROKES):
        self._real_mouse = real_mouse
        self._canvas_bbox = canvas_bbox
        self.max_strokes = max_strokes
        self.stroke_count = 0

    def _in_canvas(self, x, y):
        b = self._canvas_bbox
        return (b["x"] <= x <= b["x"] + b["width"]
                and b["y"] <= y <= b["y"] + b["height"])

    def _check_budget(self):
        if self.stroke_count > self.max_strokes:
            raise StrokeBudgetExceeded(
                f"Exceeded {self.max_strokes}-stroke budget "
                f"(attempted stroke #{self.stroke_count})"
            )

    def down(self, **kwargs):
        # Every mouse-down counts as a stroke start
        # (we count here because down() is always called for drawing)
        self.stroke_count += 1
        self._check_budget()
        return self._real_mouse.down(**kwargs)

    def up(self, **kwargs):
        return self._real_mouse.up(**kwargs)

    def move(self, x, y, **kwargs):
        return self._real_mouse.move(x, y, **kwargs)

    def click(self, x, y, **kwargs):
        if self._in_canvas(x, y):
            self.stroke_count += 1
            self._check_budget()
        return self._real_mouse.click(x, y, **kwargs)

    def dblclick(self, x, y, **kwargs):
        if self._in_canvas(x, y):
            self.stroke_count += 1
            self._check_budget()
        return self._real_mouse.dblclick(x, y, **kwargs)

    def wheel(self, delta_x, delta_y, **kwargs):
        return self._real_mouse.wheel(delta_x, delta_y, **kwargs)


# ---------------------------------------------------------------------------
# Screenshot helper
# ---------------------------------------------------------------------------

def save_textonly_screenshot(page, experiment_num):
    """Save screenshot to screenshots_textonly/experiment_{num:03d}.png."""
    os.makedirs(SCREENSHOT_DIR_TEXTONLY, exist_ok=True)
    path = os.path.join(SCREENSHOT_DIR_TEXTONLY, f"experiment_{experiment_num:03d}.png")
    screenshot_canvas(page, path)
    return path


# ---------------------------------------------------------------------------
# Multi-target scoring
# ---------------------------------------------------------------------------

def compute_multitarget_loss(result_path):
    """
    Score the drawing against all target images.
    Returns (avg_loss, per_target_dict) where per_target_dict maps
    target basename -> draw_loss.
    """
    per_target = {}
    for target in TARGET_IMAGES:
        name = Path(target).stem
        loss = compute_draw_loss(result_path, target)
        per_target[name] = loss

    avg_loss = sum(per_target.values()) / len(per_target)
    return avg_loss, per_target


# ---------------------------------------------------------------------------
# Anti-cheat: static source check
# ---------------------------------------------------------------------------

FORBIDDEN_PATTERNS = [
    "Image.open",
    "imread",
    "targets/",
    "dog_in_snow",
    "summer_night",
    "pencil_portrait",
    ".png",
    "target_arr",
]


def check_draw_source(filepath="draw_textonly.py"):
    """
    Scan draw_textonly.py for patterns that suggest target-image access.
    Raises RuntimeError if any are found.
    """
    source = Path(filepath).read_text()
    violations = [p for p in FORBIDDEN_PATTERNS if p in source]
    if violations:
        raise RuntimeError(
            f"draw_textonly.py contains forbidden patterns: {violations}\n"
            "Text-only mode: you may NOT reference or load target images."
        )


# ---------------------------------------------------------------------------
# Anti-cheat: runtime file-access restriction
# ---------------------------------------------------------------------------

_original_open = builtins.open


def _restricted_open(path, *args, **kwargs):
    """Block opening any file inside targets/."""
    path_str = str(path)
    # Block any access to the targets directory
    if os.sep + "targets" + os.sep in path_str or path_str.startswith("targets"):
        raise PermissionError(
            f"Text-only mode: cannot open target images ({path_str})"
        )
    return _original_open(path, *args, **kwargs)


def enable_file_restrictions():
    """Monkey-patch builtins.open to block target image access."""
    builtins.open = _restricted_open


def disable_file_restrictions():
    """Restore original builtins.open (used for scoring after drawing)."""
    builtins.open = _original_open
