# autodraw

This is an experiment to have the LLM learn to draw by iterating autonomously.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on the target image (e.g. `dog-in-snow`).
   The branch `autodraw/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autodraw/<tag>` from current main.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `prepare.py` — fixed constants, browser utils, image scoring. Do not modify.
   - `draw.py` — the file you modify. Drawing commands, coordinates, colors, tools.
   - The target image (set in `TARGET_IMAGE` in `draw.py`) — view it to understand
     what you are trying to reproduce.
4. **Verify setup**: Run `uv run prepare.py` to verify Playwright is installed and
   JS Paint is accessible.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row.
   The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment launches a headless browser, draws on JS Paint, screenshots the
result, and scores it against the target image. You launch it simply as:
`uv run draw.py`.

**What you CAN do:**
- Modify `draw.py` — this is the only file you edit. Everything is fair game:
  drawing coordinates, colors, tool selection, stroke patterns, fill order,
  helper functions, composition strategy, brush sizes, everything.

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation,
  browser utilities, and scoring function.
- Install new packages or add dependencies. You can only use what's already
  in `pyproject.toml`.
- Modify the scoring function. `compute_draw_loss` in `prepare.py` is the
  ground truth metric.

**The goal is simple: get the lowest draw_loss.** Since draw_loss = 1 - similarity,
a draw_loss of 0.0 means pixel-perfect reproduction. The baseline (diagonal line)
will typically score 0.7–0.9. Everything is fair game: change the drawing strategy,
the colors, the tools, the stroke order, the level of detail.

**Anti-cheating rules**: The drawing must be constructed from primitive mouse/keyboard
operations (strokes, clicks, tool selections). You may NOT:
- Paste the target image via clipboard
- Use File > Open to load the target image
- Inject the target image into the canvas via JavaScript (e.g. drawImage)
- Use any method that bypasses actually drawing stroke by stroke

**Simplicity criterion**: All else being equal, simpler is better. A small improvement
that adds ugly complexity is not worth it. Removing lines while maintaining the same
score is a win.

**Strategy tips for drawing**:
- Start by analyzing the target image: dominant colors, large regions, shapes
- Fill large background areas first (select fill bucket tool, select color, click)
- Then draw outlines and shapes (line tool, rectangle tool)
- Then add details (pencil tool, brush tool with small brush)
- Colors: click palette cells at bottom of JS Paint window
- Tools: click tool icons in the left toolbar
- The canvas origin (0,0) is top-left of the drawing area
- Use `page.mouse.move()`, `page.mouse.down()`, `page.mouse.up()` for strokes
- Use `page.mouse.click()` for tool/color selection and fill operations
- Use `page.keyboard` for keyboard shortcuts if helpful
- To discover exact pixel positions of toolbar buttons and palette colors:
  use `page.evaluate()` to query element bounding rects from the DOM

**The first run**: Your very first run should always be to establish the baseline,
so you will run the drawing script as is (no modifications).

## Output format

Once the script finishes it prints a summary like this:

```
---
draw_loss:        0.652100
similarity:       0.347900
drawing_seconds:  12.3
total_seconds:    15.7
screenshot:       screenshots/experiment_001.png
```

You can extract the key metric from the log file:

```
grep "^draw_loss:" run.log
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT
comma-separated — commas break in descriptions).

The TSV has a header row and 4 columns:

```
commit	draw_loss	status	description
```

1. git commit hash (short, 7 chars)
2. draw_loss achieved (e.g. 0.652100) — use 1.000000 for crashes
3. status: `keep`, `discard`, or `crash`
4. short text description of what this experiment tried

Example:

```
commit	draw_loss	status	description
a1b2c3d	0.850000	keep	baseline (diagonal line)
b2c3d4e	0.720000	keep	fill background blue + white ground
c3d4e5f	0.650000	keep	add green triangles for trees
d4e5f6g	1.000000	crash	syntax error in color selection
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autodraw/dog-in-snow`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `draw.py` with a drawing improvement by directly hacking the code.
3. git commit
4. Run the experiment: `uv run draw.py > run.log 2>&1` (redirect everything —
   do NOT use tee or let output flood your context)
5. Read out the results: `grep "^draw_loss:\|^similarity:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to
   read the Python stack trace and attempt a fix. If you can't get things to
   work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file,
   leave it untracked by git)
8. If draw_loss improved (lower), you "advance" the branch, keeping the git commit
9. If draw_loss is equal or worse, you git reset back to where you started

The idea is that you are a completely autonomous artist trying things out. If they
work, keep. If they don't, discard. And you're advancing the branch so that you
can iterate.

**Timeout**: Each experiment should take <60 seconds total. If a run exceeds 3
minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (Playwright error, timeout, a bug, etc.), use your
judgment: If it's something dumb and easy to fix (e.g. a typo, wrong coordinates),
fix it and re-run. If the idea itself is fundamentally broken, just skip it, log
"crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT
pause to ask the human if you should continue. Do NOT ask "should I keep going?" or
"is this a good stopping point?". The human might be asleep, or gone from a computer
and expects you to continue working *indefinitely* until you are manually stopped.
You are autonomous. If you run out of ideas, think harder — study the target image
more carefully, try different tool combinations, experiment with drawing order, try
finer details, adjust colors, break the image into quadrants, try different brush
sizes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. Each
experiment takes roughly 30–60 seconds, so you can run 60–120 experiments per hour.
The user wakes up to a `screenshots/` folder showing the drawing evolving over time
and a `results.tsv` with every experiment logged.
