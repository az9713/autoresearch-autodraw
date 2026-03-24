# autodraw — text-only experiment

This is the text-only variant of the autodraw experiment. The agent must draw
using **only a text description** — it cannot see or load the target images.
The drawing is scored against all 3 targets and the scores are averaged.

This turns every experiment into a genuine hypothesis: "I think the sky is
this shade of blue", "I think the dog is lower-center and roughly 150px wide".
The scalar loss signal tells you whether your hypothesis was right or wrong.

## Key constraints

1. **Text prompt only** — `draw_textonly.py` cannot load, read, or reference
   any target image. This is enforced by static source scanning AND runtime
   file-access restrictions. Any attempt to cheat will be caught.

2. **50-stroke budget** — Each `mouse.down()` or canvas `click()` counts as
   one stroke. Tool/palette selection outside the canvas is free. This forces
   strategic thinking: you must decide what broad visual features matter most.

3. **Multi-target scoring** — Your single drawing is scored against all 3
   target images and the loss is averaged. You cannot overfit to one target.
   The targets are very different (winter scene, summer night, pencil portrait),
   so you must find visual features that score well across all three.

4. **Same metric** — SSIM (50%), MSE (30%), histogram correlation (20%).
   The pixel-level metric is what makes this interesting: you must infer
   what pixels to produce from a text description and a scalar loss signal.

## Setup

1. **Agree on a run tag**: e.g. `textonly-v1`.
2. **Create the branch**: `git checkout -b autodraw-textonly/<tag>` from main.
3. **Read the files**:
   - `program_textonly.md` — these instructions (you're reading them now)
   - `prepare_textonly.py` — stroke counter, multi-target scoring, anti-cheat.
     Do not modify.
   - `draw_textonly.py` — the file you modify. Contains the text prompt and
     your drawing code. This is the ONLY file you edit.
   - `run_textonly.py` — the runner. Do not modify.
4. **Verify setup**: `uv run run_textonly.py` — should produce a baseline score.
5. **Initialize results.tsv**: Create with header row.
6. **Confirm and go**.

## What you CAN do

- Modify `draw_textonly.py` — everything is fair game: drawing coordinates,
  colors, tool selection, stroke patterns, fill order, helper functions,
  composition strategy, brush sizes. As long as you stay within 50 strokes
  and don't access target images.

## What you CANNOT do

- Modify `prepare_textonly.py`, `run_textonly.py`, or `prepare.py`.
- Load, read, or reference target images in any way.
- Install new packages or add dependencies.
- Bypass the stroke counter (it wraps page.mouse at runtime).

## Strategy tips

Since you can't see the targets, you must reason about what visual features
are likely to score well across three very different images:

- **Color distribution matters** (histogram correlation is 20% of the score).
  Think about what colors are likely present across all targets.
- **Structural similarity matters most** (SSIM is 50%). Large shapes in
  roughly the right positions help more than fine details.
- **Use the loss signal scientifically**. Each experiment tests a hypothesis.
  If adding blue sky to the top improves the score, that tells you at least
  one target probably has blue sky. If it hurts, it doesn't.
- **50 strokes = think big**. Fill bucket for backgrounds. Large line strokes
  for major regions. Don't waste strokes on small details early on.
- **The fill bucket is your friend**. One click fills a contiguous region —
  that's 1 stroke for a huge area. Use it for backgrounds.
- **Divide the canvas into regions**: sky/top, middle ground, foreground/bottom.
  Most landscape/portrait images follow this rough structure.
- **Track what works**: When a change improves the score, keep it. When it
  doesn't, revert. Build up a mental model of what the targets look like
  from the loss signal alone.

## Run command

```
uv run run_textonly.py > run.log 2>&1
```

Extract results:
```
grep "^draw_loss:" run.log
```

## Output format

```
---
draw_loss_dog_in_snow      : 0.XXXXXX
draw_loss_summer_night     : 0.XXXXXX
draw_loss_pencil_portrait  : 0.XXXXXX
draw_loss:                   0.XXXXXX  (averaged)
similarity:                  0.XXXXXX
strokes_used:                XX/50
budget_exceeded:             False
drawing_seconds:             XX.X
total_seconds:               XX.X
screenshot:                  screenshots_textonly/experiment_001.png
```

## Logging results

Log to `results_textonly.tsv` (tab-separated). Header and columns:

```
commit	draw_loss	strokes	status	description
```

Example:
```
commit	draw_loss	strokes	status	description
a1b2c3d	0.750000	1	keep	baseline (single gray stroke)
b2c3d4e	0.680000	5	keep	blue sky top third + white bottom
c3d4e5f	0.650000	12	keep	add gray mid-section + dark bottom
```

Do NOT commit results_textonly.tsv — leave it untracked.

## The experiment loop

LOOP FOREVER:

1. Look at git state: current branch/commit.
2. Edit `draw_textonly.py` with a new hypothesis about what to draw.
   Document your hypothesis in the draw() docstring.
3. `git commit`
4. `uv run run_textonly.py > run.log 2>&1`
5. `grep "^draw_loss" run.log` — read ALL per-target losses + average.
6. If empty output: run crashed. `tail -n 50 run.log` to diagnose.
7. Record in `results_textonly.tsv`.
8. If average draw_loss improved: keep the commit, advance.
9. If average draw_loss same/worse: `git reset`, discard.

**Analyze per-target losses**: The individual target losses tell you which
targets your changes helped or hurt. A change that improves dog_in_snow by
0.05 but hurts pencil_portrait by 0.08 is a net loss — revert it.
A change that improves all three (even slightly) is gold — keep it.

**Timeout**: Each run should take <60 seconds. Kill after 3 minutes.

**NEVER STOP**: Continue autonomously until manually interrupted.
