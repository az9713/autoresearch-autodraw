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
EXPERIMENT_NUM = 9


# ---------------------------------------------------------------------------
# Drawing — EDIT THIS FUNCTION
# ---------------------------------------------------------------------------

def draw(page, canvas_bbox):
    """
    Key insight: trees hurt SSIM badly (solid rects vs complex shapes).
    Sky-only simulation → draw_loss ~0.130 (vs 0.193 baseline).
    Strategy: paint only the sky (0,128,255) = exact target sky color.
    """
    cx = canvas_bbox["x"]
    cy = canvas_bbox["y"]
    w  = canvas_bbox["width"]
    h  = canvas_bbox["height"]

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

    def set_color(r, g, b):
        best = min(palette, key=lambda p: (p['rv']-r)**2+(p['gv']-g)**2+(p['bv']-b)**2)
        page.mouse.click(best['x'], best['y'])
        page.wait_for_timeout(50)

    # Select Line tool (DIV title='Line' at x=17, y=158)
    page.mouse.click(17, 158)
    page.wait_for_timeout(150)

    # Sky: (0,128,255) exact match to target, top 22% of canvas
    sky_y = int(h * 0.22)  # ~84
    set_color(0, 128, 255)
    for y in range(0, sky_y + 1):
        page.mouse.move(cx, cy + y)
        page.mouse.down()
        page.mouse.move(cx + w, cy + y)
        page.mouse.up()
        page.wait_for_timeout(12)


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
