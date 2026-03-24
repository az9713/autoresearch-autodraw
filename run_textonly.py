"""
run_textonly.py — Runner for text-only drawing experiment.

Usage: uv run run_textonly.py

Orchestrates:
  1. Static source check (no target image references in draw_textonly.py)
  2. Runtime file-access restriction (blocks opening targets/)
  3. Browser launch + stroke-counted drawing
  4. Multi-target scoring (averaged across all 3 targets)
"""

import time
import sys

from prepare_textonly import (
    launch_browser,
    get_canvas_bbox,
    cleanup,
    StrokeCountingMouse,
    StrokeBudgetExceeded,
    PageWithCountedMouse,
    save_textonly_screenshot,
    compute_multitarget_loss,
    check_draw_source,
    enable_file_restrictions,
    disable_file_restrictions,
    MAX_STROKES,
)

# ---------------------------------------------------------------------------
# 1. Static source check — before importing draw_textonly
# ---------------------------------------------------------------------------

try:
    check_draw_source()
except RuntimeError as e:
    print(f"ANTI-CHEAT VIOLATION: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Runtime file-access restriction — before importing draw code
# ---------------------------------------------------------------------------

enable_file_restrictions()

# ---------------------------------------------------------------------------
# 3. Import draw function (restrictions are now active)
# ---------------------------------------------------------------------------

from draw_textonly import draw, EXPERIMENT_NUM  # noqa: E402

# ---------------------------------------------------------------------------
# 4. Launch browser and draw
# ---------------------------------------------------------------------------

t_start = time.time()

pw, browser, page = launch_browser()
canvas_bbox = get_canvas_bbox(page)

# Wrap page with stroke-counting mouse proxy
# (Playwright's page.mouse is read-only, so we wrap the page object instead)
counter = StrokeCountingMouse(page.mouse, canvas_bbox, MAX_STROKES)
counted_page = PageWithCountedMouse(page, counter)

budget_exceeded = False
try:
    draw(counted_page, canvas_bbox)
except StrokeBudgetExceeded as e:
    print(f"WARNING: {e}")
    print("Drawing stopped at stroke limit. Scoring what was drawn so far.")
    budget_exceeded = True

drawing_time = time.time() - t_start

# ---------------------------------------------------------------------------
# 5. Screenshot + multi-target scoring
# ---------------------------------------------------------------------------

result_path = save_textonly_screenshot(page, EXPERIMENT_NUM)

# Lift file restrictions so scoring can read target images
disable_file_restrictions()

avg_loss, per_target = compute_multitarget_loss(result_path)
similarity = 1.0 - avg_loss

cleanup(pw, browser)
total_seconds = time.time() - t_start

# ---------------------------------------------------------------------------
# 6. Structured output
# ---------------------------------------------------------------------------

print("---")
for name, loss in per_target.items():
    print(f"draw_loss_{name:20s}: {loss:.6f}")
print(f"draw_loss:                  {avg_loss:.6f}")
print(f"similarity:                 {similarity:.6f}")
print(f"strokes_used:               {counter.stroke_count}/{counter.max_strokes}")
print(f"budget_exceeded:            {budget_exceeded}")
print(f"drawing_seconds:            {drawing_time:.1f}")
print(f"total_seconds:              {total_seconds:.1f}")
print(f"screenshot:                 {result_path}")
