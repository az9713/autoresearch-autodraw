"""
draw.py — The drawing script. This is the ONLY file you edit.

Modify the draw() function to improve the drawing. Everything is fair game:
coordinates, colors, tool selection, stroke order, helper functions, etc.
Do NOT modify prepare.py or the structured output block at the bottom.
"""

import time
from prepare import (
    launch_browser, get_canvas_bbox,
    compute_draw_loss, save_experiment_screenshot, cleanup,
)

# ---------------------------------------------------------------------------
# Configuration — update TARGET_IMAGE and EXPERIMENT_NUM each iteration
# ---------------------------------------------------------------------------

TARGET_IMAGE   = "targets/dog_in_snow.png"
EXPERIMENT_NUM = 0   # increment each experiment for screenshot naming


# ---------------------------------------------------------------------------
# Drawing — EDIT THIS FUNCTION
# ---------------------------------------------------------------------------

def draw(page, canvas_bbox):
    """
    Draw on the JS Paint canvas using Playwright mouse/keyboard APIs.

    canvas_bbox: {x, y, width, height} — canvas position in the page.
    cx, cy = top-left corner of the canvas.

    Tool/color selection cheatsheet:
      - page.mouse.click(x, y)              — click at page coordinates
      - page.mouse.move(x, y)               — move mouse
      - page.mouse.down() / page.mouse.up() — press/release for strokes
      - page.keyboard.press("Escape")       — cancel tool / close dialogs

    JS Paint toolbar (approximate page coords, varies by viewport):
      Tools are in the left panel. Colors are in the bottom palette.
      Use get_canvas_bbox() for canvas origin; toolbar is to the left.

    Baseline: draws a single diagonal line across the canvas.
    """
    cx = canvas_bbox["x"]
    cy = canvas_bbox["y"]
    w  = canvas_bbox["width"]
    h  = canvas_bbox["height"]

    # Baseline: single diagonal line (pencil tool, default black)
    page.mouse.move(cx + 10, cy + 10)
    page.mouse.down()
    page.mouse.move(cx + w - 10, cy + h - 10)
    page.mouse.up()


# ---------------------------------------------------------------------------
# Main — do not modify the structure below
# ---------------------------------------------------------------------------

t_start = time.time()

pw, browser, page = launch_browser()
canvas_bbox = get_canvas_bbox(page)

draw(page, canvas_bbox)
drawing_time = time.time() - t_start

result_path  = save_experiment_screenshot(page, experiment_num=EXPERIMENT_NUM)
draw_loss    = compute_draw_loss(result_path, TARGET_IMAGE)
similarity   = 1.0 - draw_loss

cleanup(pw, browser)
total_seconds = time.time() - t_start

print("---")
print(f"draw_loss:        {draw_loss:.6f}")
print(f"similarity:       {similarity:.6f}")
print(f"drawing_seconds:  {drawing_time:.1f}")
print(f"total_seconds:    {total_seconds:.1f}")
print(f"screenshot:       {result_path}")
