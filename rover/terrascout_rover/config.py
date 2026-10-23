"""Thresholds and settings shared by the rover modules and the dashboard."""

# Leaf greenness score (0-1): share of plant pixels that are healthy green.
HEALTHY_MIN = 0.60   # at or above: healthy
WATCH_MIN = 0.45     # 0.45-0.60: watch
LOST_MAX = 0.15      # below: sapling considered lost; 0.15-0.45: stressed

# Bird detections below this BirdNET confidence are discarded on the rover.
BIRD_MIN_CONFIDENCE = 0.60

# Hash of the "record before the first record" in the audit chain.
GENESIS_HASH = "0" * 64


def status_of(greenness: float) -> str:
    """Map a greenness score to the status shown on the dashboard."""
    if greenness < LOST_MAX:
        return "lost"
    if greenness < WATCH_MIN:
        return "stressed"
    if greenness < HEALTHY_MIN:
        return "watch"
    return "healthy"
