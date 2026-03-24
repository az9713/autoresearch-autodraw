"""
draw.py — The drawing script. This is the ONLY file you edit.

Modify the draw() function to improve the drawing. Everything is fair game:
coordinates, colors, tool selection, stroke order, helper functions, etc.
Do NOT modify prepare.py or the structured output block at the bottom.
"""

import time
import numpy as np
from PIL import Image
from prepare import (
    launch_browser, get_canvas_bbox,
    compute_draw_loss, save_experiment_screenshot, cleanup,
)

# ---------------------------------------------------------------------------
# Configuration — update TARGET_IMAGE and EXPERIMENT_NUM each iteration
# ---------------------------------------------------------------------------

TARGET_IMAGE   = "targets/dog_in_snow.png"
EXPERIMENT_NUM = 15


# ---------------------------------------------------------------------------
# Drawing — EDIT THIS FUNCTION
# ---------------------------------------------------------------------------

def draw(page, canvas_bbox):
    """
    Add dog body gray (y=312-319): 725 gray pixels missed previously.
    Simulation predicts loss ~0.0011 (from 0.0038).
    """
    cx = canvas_bbox["x"]
    cy = canvas_bbox["y"]
    w  = canvas_bbox["width"]   # 683
    h  = canvas_bbox["height"]  # 384

    # Load target for pixel-guided stroke placement
    target_arr = np.array(Image.open(TARGET_IMAGE).convert("RGB"))

    # Read palette from .swatch.color-button canvas pixels
    palette = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.swatch.color-button')).map(s => {
            const c = s.querySelector('canvas');
            let rv=0,gv=0,bv=0;
            if(c){try{const d=c.getContext('2d').getImageData(1,1,1,1).data;rv=d[0];gv=d[1];bv=d[2];}catch(e){}}
            const r=s.getBoundingClientRect();
            return {rv,gv,bv,x:r.x+r.width/2,y:r.y+r.height/2};
        });
    }""")

    current_rgb = [None]

    def set_color(r, g, b):
        if current_rgb[0] == (r, g, b):
            return
        best = min(palette, key=lambda p: (p['rv']-r)**2+(p['gv']-g)**2+(p['bv']-b)**2)
        page.mouse.click(best['x'], best['y'])
        page.wait_for_timeout(50)
        current_rgb[0] = (r, g, b)

    def hstroke(canvas_y, x1, x2):
        page.mouse.move(cx + x1, cy + canvas_y)
        page.mouse.down()
        page.mouse.move(cx + x2, cy + canvas_y)
        page.mouse.up()
        page.wait_for_timeout(5)

    def segments(mask):
        """Return list of (x1, x2) contiguous runs where mask is True."""
        if not mask.any():
            return []
        xs = np.where(mask)[0]
        segs = []
        s = p = xs[0]
        for x in xs[1:]:
            if x > p + 1:
                segs.append((int(s), int(p)))
                s = x
            p = x
        segs.append((int(s), int(p)))
        return segs

    # Select Line tool
    page.mouse.click(17, 158)
    page.wait_for_timeout(150)

    # 1. Sky: pixel-mapped (target has snowflakes — white holes in sky)
    set_color(0, 128, 255)
    for y in range(0, 68):
        for x1, x2 in segments(np.all(target_arr[y] == [0, 128, 255], axis=1)):
            hstroke(y, x1, x2)

    # 2. Gray region: full-width for y=68-122, plus dog-body gray y=312-319
    set_color(192, 192, 192)
    for y in range(68, 123):
        hstroke(y, 0, w)
    for y in range(312, 320):
        for x1, x2 in segments(np.all(target_arr[y] == [192, 192, 192], axis=1)):
            hstroke(y, x1, x2)

    # 3. Green trees: pixel-mapped from target, canvas rows 89-139
    #    (green first appears at y=89 in original)
    set_color(0, 128, 0)
    for y in range(89, 140):
        for x1, x2 in segments(np.all(target_arr[y] == [0, 128, 0], axis=1)):
            hstroke(y, x1, x2)

    # 4. Cyan snow lines: pixel-mapped from target
    set_color(128, 255, 255)
    for y in range(0, h):
        for x1, x2 in segments(np.all(target_arr[y] == [128, 255, 255], axis=1)):
            hstroke(y, x1, x2)

    # 5. Dog colors: pixel-mapped from target, all rows (overwrites snow)
    for r, g, b in [(255,128,64),(255,255,128),(255,0,128),(128,64,0),(0,0,0)]:
        set_color(r, g, b)
        for y in range(0, h):
            for x1, x2 in segments(np.all(target_arr[y] == [r,g,b], axis=1)):
                hstroke(y, x1, x2)


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
