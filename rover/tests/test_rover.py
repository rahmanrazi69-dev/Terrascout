from datetime import datetime, timezone

from terrascout_rover.audit import AuditLog
from terrascout_rover.config import status_of
from terrascout_rover.greenness import greenness
from terrascout_rover.patrol import main, run_patrol
from terrascout_rover.sensors import synthetic_leaf


def test_greenness_tracks_leaf_colour():
    assert abs(greenness(synthetic_leaf(0.82)) - 0.82) < 0.02
    assert abs(greenness(synthetic_leaf(0.41)) - 0.41) < 0.02
    assert status_of(greenness(synthetic_leaf(0.41))) == "stressed"


def test_thresholds():
    assert [status_of(g) for g in (0.9, 0.55, 0.3, 0.05)] == ["healthy", "watch", "stressed", "lost"]


def test_chain_detects_edits(tmp_path):
    log = AuditLog()
    for i in range(5):
        log.append("heat", {"delta": i})
    assert log.verify() is None
    path = tmp_path / "r.jsonl"
    log.save(path)
    again = AuditLog.load(path)
    assert again.verify() is None
    again.records[2].data["delta"] = -2
    assert again.verify() == 2


def test_patrol_flags_stressed_sapling():
    log = AuditLog()
    tickets = run_patrol(log, datetime(2026, 10, 19, 8, 0, tzinfo=timezone.utc))
    assert [t["tag"] for t in tickets] == ["TS-07"]
    assert log.verify() is None
    assert log.records[-1].type == "sync"


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "records.jsonl")
    assert main(["run", "--out", out]) == 0
    assert main(["verify", out]) == 0
    assert main(["tamper", out, "5"]) == 0
    assert main(["verify", out]) == 1
    assert "broken at record #5" in capsys.readouterr().out
