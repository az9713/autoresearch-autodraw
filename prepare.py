"""
prepare.py — Fixed infrastructure for autodraw. Do not modify.

Provides: browser launch/teardown, canvas detection, screenshot capture,
and the ground-truth scoring function (compute_draw_loss).
"""

import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from skimage.metrics import structural_similarity as ssim

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JSPAINT_URL   = "https://jspaint.app"
SCREENSHOT_DIR = "screenshots"
COMPARISON_SIZE = (400, 300)   # canonical size for scoring (width, height)


# ---------------------------------------------------------------------------
# Browser utilities
# ---------------------------------------------------------------------------

def launch_browser():
    """
    Launch headless Chromium, navigate to JS Paint, wait for canvas.
    Returns (pw, browser, page). Call cleanup(pw, browser) when done.
    """
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(JSPAINT_URL, wait_until="networkidle", timeout=30000)
    # Wait for the main canvas to appear
    page.wait_for_selector(".main-canvas", timeout=15000)
    # Dismiss any tooltip/welcome dialogs
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass
    return pw, browser, page


def cleanup(pw, browser):
    """Close browser and playwright context."""
    try:
        browser.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass


def get_canvas_bbox(page):
    """
    Return the bounding rect of the JS Paint canvas as a dict:
    {x, y, width, height} in page-level pixel coordinates.
    """
    bbox = page.evaluate("""
        (() => {
            const c = document.querySelector('.main-canvas');
            if (!c) return null;
            const r = c.getBoundingClientRect();
            return {x: r.x, y: r.y, width: r.width, height: r.height};
        })()
    """)
    if bbox is None:
        raise RuntimeError("Could not find .main-canvas element on the page")
    return bbox


def screenshot_canvas(page, path):
    """
    Screenshot only the canvas area (not the full page UI).
    Saves to path and returns the path string.
    """
    bbox = get_canvas_bbox(page)
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    page.screenshot(
        path=path,
        clip={
            "x": bbox["x"],
            "y": bbox["y"],
            "width": bbox["width"],
            "height": bbox["height"],
        }
    )
    return path


def save_experiment_screenshot(page, experiment_num):
    """
    Save a screenshot to screenshots/experiment_{num:03d}.png.
    Returns the file path.
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOT_DIR, f"experiment_{experiment_num:03d}.png")
    screenshot_canvas(page, path)
    return path


# ---------------------------------------------------------------------------
# Scoring — ground truth, do not modify
# ---------------------------------------------------------------------------

def _histogram_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """
    Per-channel histogram correlation averaged across R, G, B.
    Both arrays must be float64 in [0, 255], shape (H, W, 3).
    Returns a float in [0, 1].
    """
    scores = []
    for c in range(3):
        ha, _ = np.histogram(a[:, :, c], bins=256, range=(0, 256))
        hb, _ = np.histogram(b[:, :, c], bins=256, range=(0, 256))
        ha = ha.astype(float)
        hb = hb.astype(float)
        norm_a = np.linalg.norm(ha)
        norm_b = np.linalg.norm(hb)
        if norm_a == 0 or norm_b == 0:
            scores.append(0.0)
        else:
            corr = np.dot(ha / norm_a, hb / norm_b)
            scores.append(float(np.clip(corr, 0.0, 1.0)))
    return float(np.mean(scores))


def compute_similarity(result_path: str, target_path: str) -> float:
    """
    Compute similarity between two images. Returns float in [0, 1].
    Higher = more similar. Uses a weighted blend:
      0.5 × SSIM + 0.3 × (1 - normalized_MSE) + 0.2 × histogram_correlation
    """
    result_img = Image.open(result_path).convert("RGB").resize(COMPARISON_SIZE, Image.LANCZOS)
    target_img = Image.open(target_path).convert("RGB").resize(COMPARISON_SIZE, Image.LANCZOS)
    r = np.array(result_img, dtype=np.float64)
    t = np.array(target_img, dtype=np.float64)

    # SSIM
    ssim_score = float(ssim(r, t, channel_axis=2, data_range=255.0))
    ssim_score = max(0.0, ssim_score)

    # Normalized MSE
    mse = float(np.mean((r - t) ** 2))
    mse_score = 1.0 - (mse / (255.0 ** 2))
    mse_score = max(0.0, min(1.0, mse_score))

    # Histogram correlation
    hist_score = _histogram_correlation(r, t)

    return 0.5 * ssim_score + 0.3 * mse_score + 0.2 * hist_score


def compute_draw_loss(result_path: str, target_path: str) -> float:
    """
    Returns draw_loss = 1 - similarity. Lower is better (mirrors val_bpb).
    0.0 = pixel-perfect. 1.0 = completely different.
    """
    return 1.0 - compute_similarity(result_path, target_path)


# ---------------------------------------------------------------------------
# One-time setup / sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("autodraw prepare.py — verifying setup...")

    # Check that at least one target exists
    targets = list(Path("targets").glob("*.png")) if Path("targets").exists() else []
    if not targets:
        print("ERROR: No target images found in targets/")
        print("Copy your target PNGs to targets/ before starting.")
        sys.exit(1)
    print(f"  Found {len(targets)} target image(s): {[t.name for t in targets]}")

    # Launch browser and verify JS Paint loads
    print("  Launching headless browser...")
    try:
        pw, browser, page = launch_browser()
    except Exception as e:
        print(f"ERROR: Could not launch browser: {e}")
        print("Run: uv run playwright install chromium")
        sys.exit(1)

    print("  JS Paint loaded. Testing canvas detection...")
    try:
        bbox = get_canvas_bbox(page)
        print(f"  Canvas found at: x={bbox['x']:.0f} y={bbox['y']:.0f} "
              f"w={bbox['width']:.0f} h={bbox['height']:.0f}")
    except Exception as e:
        print(f"ERROR: Canvas detection failed: {e}")
        cleanup(pw, browser)
        sys.exit(1)

    # Screenshot blank canvas and score against first target
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    test_path = os.path.join(SCREENSHOT_DIR, "sanity_check.png")
    screenshot_canvas(page, test_path)
    cleanup(pw, browser)

    target_path = str(targets[0])
    loss = compute_draw_loss(test_path, target_path)
    print(f"  Blank canvas draw_loss vs {targets[0].name}: {loss:.6f}")
    print(f"  Screenshot saved to: {test_path}")
    print()
    print("Ready.")
