"""Tamper-evident audit log.

Every record stores the SHA-256 hash of its own content plus the previous
record's hash, so records form a chain. Editing any past record changes its
hash and breaks every link after it, which `verify()` reports.

The hashed body is the JSON array [seq, ts, type, data, prev] with compact
separators, the same structure the dashboard uses in the browser.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable

from .config import GENESIS_HASH


def _body(seq: int, ts: str, type_: str, data: Any, prev: str) -> str:
    return json.dumps([seq, ts, type_, data, prev], separators=(",", ":"), ensure_ascii=False)


@dataclass
class Record:
    seq: int
    ts: str
    type: str
    data: dict
    prev: str
    hash: str

    def expected_hash(self) -> str:
        return hashlib.sha256(_body(self.seq, self.ts, self.type, self.data, self.prev).encode()).hexdigest()


class AuditLog:
    def __init__(self, records: Iterable[Record] = ()):
        self.records: list[Record] = list(records)

    def append(self, type_: str, data: dict, ts: str | None = None) -> Record:
        ts = ts or datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        prev = self.records[-1].hash if self.records else GENESIS_HASH
        seq = len(self.records) + 1
        h = hashlib.sha256(_body(seq, ts, type_, data, prev).encode()).hexdigest()
        rec = Record(seq, ts, type_, data, prev, h)
        self.records.append(rec)
        return rec

    def verify(self) -> int | None:
        """Return the index of the first broken record, or None if the chain is intact."""
        prev = GENESIS_HASH
        for i, r in enumerate(self.records):
            if r.prev != prev or r.expected_hash() != r.hash:
                return i
            prev = r.hash
        return None

    # JSON Lines persistence: one record per line.
    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for r in self.records:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, path: str) -> "AuditLog":
        with open(path, encoding="utf-8") as f:
            return cls(Record(**json.loads(line)) for line in f if line.strip())
