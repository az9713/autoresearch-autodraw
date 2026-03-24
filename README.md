# autodraw

Autonomous drawing research via JS Paint — an adaptation of [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) for browser-based drawing.

The idea: give Claude Code browser automation tools and a target image. It iterates on `draw.py`, runs headless JS Paint, screenshots the result, compares against the target, keeps improvements, reverts failures — exactly like autoresearch's training loop, but for drawing.

## How it works

The repo has three files that matter:

- **`prepare.py`** — fixed infrastructure: browser launch, canvas detection, screenshot capture, image scoring. Not modified.
- **`draw.py`** — the single file the agent edits. Contains the drawing commands: coordinates, colors, tool selections, stroke patterns. **This file is edited and iterated on by the agent**.
- **`program.md`** — instructions for the agent. Point Claude Code here and let it go.

The metric is **draw_loss** (= 1 - similarity) — lower is better, 0.0 = pixel-perfect.

## Quick start

```bash
# 1. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Install Playwright browser
uv run playwright install chromium

# 4. Verify setup (launches headless browser, screenshots blank canvas)
uv run prepare.py

# 5. Run baseline experiment
uv run draw.py > run.log 2>&1
grep "^draw_loss:" run.log
```

## Running the agent

Start Claude Code in this directory and prompt:

```
Read program.md and let's kick off a new experiment for targets/dog_in_snow.png!
```

The agent will set up a branch, run the baseline, and iterate autonomously.

## Targets

Three reference images in `targets/`:
- `dog_in_snow.png` — colorful geometric scene (easiest)
- `summer_night.png` — layered colorful scene with figure
- `pencil_portrait.png` — monochrome line art (hardest)

## Project structure

```
prepare.py     — fixed infrastructure (do not modify)
draw.py        — drawing script (agent modifies this)
program.md     — agent instructions
targets/       — reference images to reproduce
pyproject.toml — dependencies
```
