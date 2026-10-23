"""Run a patrol and write the hash-chained records the dashboard reads.

Usage:
    python -m terrascout_rover.patrol run --out records.jsonl      # simulated patrol
    python -m terrascout_rover.patrol verify records.jsonl         # check the chain
    python -m terrascout_rover.patrol tamper records.jsonl 5       # edit record #5 (demo)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from . import sensors
from .audit import AuditLog
from .config import BIRD_MIN_CONFIDENCE, status_of
from .greenness import greenness

# Route events by position along the loop (0-1), matching the demo park.
SAPLINGS = [("TS-%02d" % (i + 1), t) for i, t in enumerate([.07, .13, .22, .29, .38, .46, .56, .61, .70, .77, .86, .93])]
SIM_GREENNESS = {"TS-03": .57, "TS-07": .41, "TS-11": .08}
SOUND_STATIONS = [("S1", .33), ("S2", .72)]
CANOPY = [(.17, .33), (.53, .63), (.83, .90)]


def in_canopy(t: float) -> bool:
    return any(a <= t <= b for a, b in CANOPY)


def run_patrol(log: AuditLog, start: datetime) -> list[dict]:
    """Drive the route once. Returns the tickets raised."""
    events = [(t, "sap", tag) for tag, t in SAPLINGS] + [(t, "bird", sid) for sid, t in SOUND_STATIONS]
    events += [(round(.03 + .04 * k, 2), "heat", None) for k in range(24)]
    tickets = []
    for t, kind, ref in sorted(events, key=lambda e: e[0]):
        ts = (start + timedelta(minutes=80 * t)).isoformat(timespec="seconds").replace("+00:00", "Z")
        if kind == "sap":
            frame = sensors.capture_photo(SIM_GREENNESS.get(ref, .82))
            tag = sensors.read_marker(frame, expected=ref)
            g = greenness(frame)
            log.append("sapling_check", {"tag": tag, "g": g, "status": status_of(g), "photo": f"TS1_{tag}_{ts[11:16].replace(':', '')}.jpg"}, ts)
            if status_of(g) == "stressed":
                tickets.append({"tag": tag, "title": "Stressed sapling: leaves yellowing", "greenness": g, "opened": ts})
        elif kind == "bird":
            for species, conf in sensors.detect_birds():
                if conf >= BIRD_MIN_CONFIDENCE:
                    log.append("bird_audio", {"station": ref, "species": species, "conf": conf}, ts)
        else:
            air, refT = sensors.read_air_temp(t * 30, in_canopy(t)), sensors.read_reference_temp(t * 30)
            log.append("heat", {"t": t, "air": air, "ref": refT, "delta": round(air - refT, 1), "canopy": in_canopy(t)}, ts)
    n_photos = len(SAPLINGS) * 3
    log.append("sync", {"photos": n_photos}, (start + timedelta(minutes=82)).isoformat(timespec="seconds").replace("+00:00", "Z"))
    return tickets


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="terrascout-patrol")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--out", default="records.jsonl"); r.add_argument("--append", action="store_true")
    v = sub.add_parser("verify"); v.add_argument("path")
    m = sub.add_parser("tamper"); m.add_argument("path"); m.add_argument("seq", type=int)
    a = p.parse_args(argv)

    if a.cmd == "run":
        log = AuditLog.load(a.out) if a.append else AuditLog()
        tickets = run_patrol(log, datetime.now(timezone.utc).replace(microsecond=0))
        log.save(a.out)
        print(f"Patrol done: {len(log.records)} records in {a.out}")
        for tk in tickets:
            print("Ticket:", json.dumps(tk))
        return 0
    log = AuditLog.load(a.path)
    if a.cmd == "tamper":
        rec = log.records[a.seq - 1]
        rec.data = dict(rec.data, tampered=True)
        log.save(a.path)
        print(f"Edited record #{a.seq} without re-hashing it.")
        return 0
    bad = log.verify()
    if bad is None:
        print(f"Chain intact: {len(log.records)} records.")
        return 0
    print(f"Chain broken at record #{bad + 1}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
