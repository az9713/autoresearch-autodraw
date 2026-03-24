# autodraw — text-only

An autonomous drawing experiment where the agent learns to draw by iterating
against a scalar loss signal. The agent cannot see the target images — it
receives only a text description and must form hypotheses about what to draw.
Each experiment tests a hypothesis; the loss tells you if you were right.

## Constraints

1. **Text prompt only.** You cannot load, read, or reference any target image.
   This is enforced at runtime — any attempt to access `targets/` will raise
   an error.

2. **50-stroke budget.** Each `mouse.down()` or canvas `mouse.click()` inside
   the canvas counts as one stroke. Tool and palette clicks outside the canvas
   are free. When the budget is exceeded, drawing stops immediately and
   whatever you drew so far is scored.

3. **Multi-target scoring.** Your single drawing is scored against all 3 target
   images and the draw_loss is averaged. The three targets are very different
   from each other, so you cannot overfit to any one of them.

4. **SSIM/MSE/histogram metric.** The scoring function is:
   `0.5 × SSIM + 0.3 × (1 − normalized_MSE) + 0.2 × histogram_correlation`.
   draw_loss = 1 − similarity. Lower is better. 0.0 = pixel-perfect.

## Files

- `draw_textonly.py` — **the ONLY file you edit.** Contains the text prompt
  and your drawing code. Everything is fair game: coordinates, colors, tool
  selection, stroke order, fill strategy, helper functions.
- `run_textonly.py` — the runner. Do not modify.
- `prepare_textonly.py` — stroke counting, multi-target scoring, anti-cheat.
  Do not modify.
- `prepare.py` — base scoring infrastructure. Do not modify.

## Setup

1. **Agree on a run tag** with the user (e.g. `textonly-v1`).
2. **Create the branch**: `git checkout -b autodraw-textonly/<tag>` from main.
3. **Read the in-scope files.** The repo is small. Read:
   - `program_textonly.md` — these instructions.
   - `README.md` — repository context.
   - `prepare_textonly.py` — understand the stroke counter and scoring.
   - `draw_textonly.py` — the file you will modify.
   - `run_textonly.py` — understand the execution pipeline.
4. **Verify setup**: Run `uv run run_textonly.py` to confirm everything works
   and establish the baseline score.
5. **Initialize results_textonly.tsv** with just the header row.
6. **Confirm and go.** Once everything looks good, begin the experiment loop.

## The experiment loop

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on.
2. Edit `draw_textonly.py` with a new drawing hypothesis. Document the
   hypothesis in the `draw()` docstring so it shows up in the git log.
3. `git commit`.
4. Run the experiment: `uv run run_textonly.py > run.log 2>&1` (redirect
   everything — do NOT use tee or let output flood your context).
5. Read out the results: `grep "^draw_loss" run.log`. This gives you the
   per-target losses AND the average.
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log`
   to read the Python stack trace and attempt a fix. If you can't get things
   to work after more than a few attempts, give up on that idea.
7. Record the results in `results_textonly.tsv` (do NOT commit this file —
   leave it untracked by git).
8. If draw_loss improved (lower): keep the commit, advance the branch.
9. If draw_loss is equal or worse: `git reset` back to where you started,
   discarding the attempt.

## Logging results

Log every experiment to `results_textonly.tsv` (tab-separated, NOT
comma-separated — commas break in descriptions).

Header row and 5 columns:

```
commit	draw_loss	strokes	status	description
```

1. git commit hash (short, 7 chars)
2. draw_loss achieved (averaged) — use 1.000000 for crashes
3. strokes used (e.g. 12/50)
4. status: `keep`, `discard`, or `crash`
5. short text description of what this experiment hypothesized

Example:

```
commit	draw_loss	strokes	status	description
a1b2c3d	0.750000	1/50	keep	baseline (single gray stroke)
b2c3d4e	0.680000	8/50	keep	hypothesis: blue sky top third + white bottom
c3d4e5f	0.710000	8/50	discard	hypothesis: green sky instead of blue — worse
d4e5f6g	1.000000	0/50	crash	syntax error in palette query
```

## Output format

The runner prints a summary like this:

```
---
draw_loss_dog_in_snow      : 0.XXXXXX
draw_loss_summer_night     : 0.XXXXXX
draw_loss_pencil_portrait  : 0.XXXXXX
draw_loss:                   0.XXXXXX
similarity:                  0.XXXXXX
strokes_used:                XX/50
budget_exceeded:             False
drawing_seconds:             XX.X
total_seconds:               XX.X
screenshot:                  screenshots_textonly/experiment_001.png
```

**Analyze per-target losses.** The individual losses tell you which targets
your changes helped or hurt. A change that improves dog_in_snow by 0.05 but
hurts pencil_portrait by 0.08 is a net negative — revert it. A change that
improves all three even slightly is gold — keep it.

## Strategy

Since you cannot see the targets, you must reason from text and loss signal:

- **Use the loss signal scientifically.** Each experiment tests a hypothesis.
  If adding blue sky to the top improves the average, that tells you at least
  one target probably has blue sky. If it hurts, it doesn't. Track your
  findings — build a mental model of all three targets from the signal alone.
- **SSIM dominates** (50% of the score). Large shapes in roughly the right
  positions matter more than fine details or exact colors.
- **Histogram correlation** (20%) penalizes wrong color distributions. Think
  about what colors are likely present across all three targets.
- **50 strokes = think big.** Fill bucket for backgrounds (1 click = 1 stroke
  for a huge area). Large line strokes for major regions. Don't waste strokes
  on small details until the big picture is right.
- **Divide the canvas into regions**: top (sky/background), middle
  (subject/midground), bottom (foreground/ground). Most images follow this.
- **The three targets are very different.** A winter landscape, a summer night
  scene, and a pencil portrait. Averaging means you need a generalist
  composition. Think about what visual features help across all three.

## Drawing tips

- The canvas is 683×384 pixels. Origin (0,0) is top-left.
- Colors: click palette swatches at the bottom of the JS Paint window.
- Tools: click tool icons in the left toolbar.
- Use `page.mouse.move()`, `page.mouse.down()`, `page.mouse.up()` for strokes.
- Use `page.mouse.click()` for tool/color selection and fill operations.
- Use `page.keyboard` for keyboard shortcuts if helpful.
- To discover exact positions of toolbar buttons and palette colors, use
  `page.evaluate()` to query element bounding rects from the DOM.
- The fill bucket is extremely stroke-efficient: one click fills a contiguous
  region of the same color.

## Anti-cheating rules

The drawing must be constructed from primitive mouse/keyboard operations
(strokes, clicks, tool selections). You may NOT:

- Load, open, or read any target image file.
- Paste an image via clipboard.
- Use File > Open to load an image.
- Inject image data into the canvas via JavaScript (e.g. drawImage).
- Use any method that bypasses actually drawing stroke by stroke.
- Bypass or disable the stroke counter.

These rules are enforced by static source scanning and runtime file-access
restrictions. Violations will cause the run to abort.

## Simplicity criterion

All else being equal, simpler is better. A small improvement that adds ugly
complexity is not worth it. Removing lines while maintaining the same score
is a win.

## Timeout

Each experiment should take well under a minute (50 strokes is fast). If a
run exceeds 5 minutes, kill it and treat it as a failure (discard and revert).

## Crashes

If a run crashes (Playwright error, timeout, a bug, etc.), use your judgment:
if it's something dumb and easy to fix (e.g. a typo, wrong coordinates), fix
it and re-run. If the idea itself is fundamentally broken, just skip it, log
`crash` as the status in the TSV, and move on to the next idea.

## NEVER STOP

Once the experiment loop has begun (after the initial setup), do NOT pause to
ask the human if you should continue. Do NOT ask "should I keep going?" or
"is this a good stopping point?". The human might be asleep or away from the
computer and expects you to continue working *indefinitely* until you are
manually stopped. You are autonomous.

If you run out of ideas, think harder. Try different color combinations. Try
different region sizes. Revisit hypotheses that were close. Try the fill
bucket vs line tool vs brush. Break the canvas into quadrants and optimize
each one. Try different background colors. Experiment with drawing order
(later strokes overwrite earlier ones). Use the per-target losses to isolate
which target a change helped or hurt, and form more targeted hypotheses.

The loop runs until the human interrupts you, period.

As an example: a user might leave you running while they sleep. Each
experiment takes roughly 30–60 seconds, so you can run 60–120 experiments
per hour. The user wakes up to a `screenshots_textonly/` folder showing the
drawing evolving over time and a `results_textonly.tsv` with every experiment
logged, each one a hypothesis tested and confirmed or rejected.
