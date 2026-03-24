"""
draw_textonly.py — Text-only drawing. This is the ONLY file you edit.

You must draw based on the TEXT PROMPT below. You have a 50-stroke budget.
You may NOT load, read, or access any image files. You may NOT reference
target filenames or paths. Any attempt to do so will be caught and blocked.

Your only information source is the text prompt and the scalar loss signal
you get back after each experiment. Use that signal to form and test
hypotheses about what the target images look like.
"""

# ---------------------------------------------------------------------------
# TEXT PROMPT — this is your only information about what to draw
# ---------------------------------------------------------------------------

TEXT_PROMPT = """
You are drawing on a 683×384 pixel canvas in JS Paint. Your drawing will be
scored against THREE different target images (averaged), so aim for a
generalist composition that scores reasonably across all of them:

1. A dog playing in snow — winter scene with a dog, snowy ground, trees,
   and a blue sky with snowflakes.
2. A summer night — an evening/night scene, possibly with a figure, warm
   and cool tones.
3. A pencil portrait — a monochrome face/head drawing, likely grayscale
   with line work.

You have exactly 50 strokes. Think strategically about what broad visual
features (background colors, large shapes, tonal distribution) will score
well across all three very different images.
"""

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXPERIMENT_NUM = 1


# ---------------------------------------------------------------------------
# Drawing — EDIT THIS FUNCTION
# ---------------------------------------------------------------------------

def draw(page, canvas_bbox):
    """
    Draw on the canvas using only the text prompt above.
    Budget: 50 strokes maximum (each mouse down→move→up = 1 stroke).
    Tool/color selection clicks outside the canvas are free.

    Hypothesis for experiment 1 (baseline):
    - Fill background with a neutral mid-tone gray (good average for all 3)
    - This establishes a baseline loss to improve from.
    """
    cx = canvas_bbox["x"]
    cy = canvas_bbox["y"]
    w  = canvas_bbox["width"]   # 683
    h  = canvas_bbox["height"]  # 384

    # Read palette swatches from DOM (this is UI inspection, not image access)
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
        """Select nearest palette color. Does NOT count as a stroke."""
        if current_rgb[0] == (r, g, b):
            return
        best = min(palette, key=lambda p: (p['rv']-r)**2+(p['gv']-g)**2+(p['bv']-b)**2)
        page.mouse.click(best['x'], best['y'])
        page.wait_for_timeout(50)
        current_rgb[0] = (r, g, b)

    def stroke(y, x1, x2):
        """One horizontal stroke. Costs 1 from the budget."""
        page.mouse.move(cx + x1, cy + y)
        page.mouse.down()
        page.mouse.move(cx + x2, cy + y)
        page.mouse.up()
        page.wait_for_timeout(5)

    # Select Line tool (toolbar click — free, outside canvas)
    page.mouse.click(17, 158)
    page.wait_for_timeout(150)

    # --- Baseline: single gray fill stroke across the middle ---
    # Just a starting point to measure. The agent loop will iterate from here.
    set_color(192, 192, 192)
    stroke(h // 2, 0, w)
