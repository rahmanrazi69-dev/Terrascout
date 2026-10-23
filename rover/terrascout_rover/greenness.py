"""Leaf greenness scoring: the quick health check that runs on the rover.

The photo is converted to HSV. Pixels that belong to the plant (enough colour
saturation and brightness) are split into healthy green and yellow/brown.
The score is the healthy share of plant pixels, from 0 to 1.
"""
from __future__ import annotations

import numpy as np

# Hue ranges on a 0-360 degree wheel.
GREEN_HUE = (70, 170)     # healthy leaf greens
YELLOW_BROWN_HUE = (15, 70)  # yellowing, browning, dry leaf
MIN_SATURATION = 0.25
MIN_VALUE = 0.15


def rgb_to_hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorised RGB (0-255, HxWx3) to hue (degrees), saturation and value (0-1)."""
    x = rgb.astype(np.float64) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    mx, mn = x.max(axis=-1), x.min(axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-9
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = (60 * ((g - b)[rm] / d[rm])) % 360
    h[gm] = 60 * ((b - r)[gm] / d[gm]) + 120
    h[bm] = 60 * ((r - g)[bm] / d[bm]) + 240
    s = np.where(mx > 0, d / np.where(mx > 0, mx, 1), 0)
    return h, s, mx


def greenness(rgb: np.ndarray) -> float:
    """Return the share of plant pixels that are healthy green (0-1).

    Returns 0.0 when no plant pixels are found (for example, a lost sapling).
    """
    h, s, v = rgb_to_hsv(rgb)
    plant = (s >= MIN_SATURATION) & (v >= MIN_VALUE)
    green = plant & (h >= GREEN_HUE[0]) & (h < GREEN_HUE[1])
    stressed = plant & (h >= YELLOW_BROWN_HUE[0]) & (h < YELLOW_BROWN_HUE[1])
    total = int(green.sum() + stressed.sum())
    return 0.0 if total == 0 else round(float(green.sum()) / total, 3)


def greenness_from_file(path: str) -> float:
    """Load an image file with Pillow and score it."""
    from PIL import Image

    with Image.open(path) as im:
        return greenness(np.asarray(im.convert("RGB")))
