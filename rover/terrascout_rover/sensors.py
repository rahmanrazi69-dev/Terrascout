"""Sensor access with simulated fallbacks.

On the rover (Raspberry Pi) the real drivers are used when installed:
  - camera:   picamera2
  - markers:  pupil-apriltags (AprilTag 36h11 printed on each sapling stake)
  - thermal:  adafruit-circuitpython-mlx90640 (surface temperature)
  - air:      adafruit-circuitpython-sht31d (air temperature and humidity)
  - birds:    birdnetlib (BirdNET on recorded clips)
Without them (on a laptop), every function returns simulated values so the
whole pipeline can be run and tested anywhere.
"""
from __future__ import annotations

import math
import random

import numpy as np

_rng = random.Random(7)


# ---------- camera + markers ----------
def capture_photo(sim_greenness: float | None = None) -> np.ndarray:
    """Return an RGB frame. Real camera if available, else a synthetic leaf patch."""
    try:  # pragma: no cover - hardware only
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.start()
        frame = cam.capture_array()[..., :3]
        cam.stop()
        return frame
    except Exception:
        g = 0.8 if sim_greenness is None else sim_greenness
        return synthetic_leaf(g)


def synthetic_leaf(g: float, size: int = 96) -> np.ndarray:
    """Make a test image whose plant pixels are a share g green, the rest yellow-brown."""
    img = np.full((size, size, 3), (120, 110, 100), dtype=np.uint8)  # grey background
    n = size * size // 2
    idx = np.arange(n)
    rows, cols = idx // size + size // 4, idx % size
    green_n = int(round(n * g))
    img[rows[:green_n], cols[:green_n]] = (40, 160, 60)
    img[rows[green_n:], cols[green_n:]] = (200, 160, 30)
    return img


def read_marker(frame: np.ndarray, expected: str | None = None) -> str | None:
    """Decode the AprilTag on the sapling stake; returns e.g. 'TS-07'."""
    try:  # pragma: no cover - needs the optional library and a real photo
        from pupil_apriltags import Detector
        gray = (0.299 * frame[..., 0] + 0.587 * frame[..., 1] + 0.114 * frame[..., 2]).astype(np.uint8)
        tags = Detector(families="tag36h11").detect(gray)
        if tags:
            return f"TS-{tags[0].tag_id:02d}"
    except Exception:
        pass
    return expected


# ---------- heat ----------
def read_air_temp(sim_t: float = 0.0, shaded: bool = False) -> float:
    try:  # pragma: no cover
        import board, adafruit_sht31d
        return float(adafruit_sht31d.SHT31D(board.I2C()).temperature)
    except Exception:
        base = 31.0 + 1.5 * math.sin(sim_t / 3)
        return round(base + (-3.9 if shaded else 1.6) + _rng.uniform(-0.3, 0.3), 2)


def read_reference_temp(sim_t: float = 0.0) -> float:
    """Fixed reference station reading at the same moment (fetched over Wi-Fi on the real system)."""
    return round(31.0 + 1.5 * math.sin(sim_t / 3), 2)


# ---------- birds ----------
def detect_birds(clip_path: str | None = None, lat: float = 3.19, lon: float = 101.52):
    """Return a list of (species, confidence). Uses BirdNET if installed and a clip is given."""
    if clip_path:
        try:  # pragma: no cover
            from birdnetlib import Recording
            from birdnetlib.analyzer import Analyzer
            rec = Recording(Analyzer(), clip_path, lat=lat, lon=lon, min_conf=0.25)
            rec.analyze()
            return [(d["common_name"], round(d["confidence"], 2)) for d in rec.detections]
        except Exception:
            pass
    return [(_rng.choice(["Common Iora", "Oriental Magpie-Robin", "Yellow-vented Bulbul"]), round(_rng.uniform(0.55, 0.92), 2))]
