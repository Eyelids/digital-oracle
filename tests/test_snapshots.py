from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.snapshots import RecordingHttpClient, ReplayHttpClient, SnapshotMissError


class FakeJsonClient:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        return self.payload


class FakeTextClient:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_text(self, url: str, *, params: Mapping[str, object] | None = None) -> str:
        self.calls.append((url, params))
        return self.payload


class SnapshotTests(unittest.TestCase):
    def test_recording_http_client_roundtrips_json_snapshots(self) -> None:
        payload = {"ok": True, "items": [1, 2, 3]}
        with tempfile.TemporaryDirectory() as tmpdir:
            client = RecordingHttpClient(
                snapshot_dir=tmpdir,
                json_client=FakeJsonClient(payload),
            )

            response = client.get_json(
                "https://api.example.com/items",
                params={"limit": 3, "active": True},
            )
            self.assertEqual(response, payload)

            replay = ReplayHttpClient(tmpdir)
            replayed = replay.get_json(
                "https://api.example.com/items",
                params={"limit": 3, "active": True},
            )
            self.assertEqual(replayed, payload)

            snapshot_files = sorted(Path(tmpdir).glob("*.json"))
            self.assertEqual(len(snapshot_files), 1)
            envelope = json.loads(snapshot_files[0].read_text())
            self.assertEqual(envelope["kind"], "json")
            self.assertEqual(envelope["request"]["url"], "https://api.example.com/items")
            self.assertEqual(envelope["request"]["params"]["active"], True)

    def test_recording_http_client_roundtrips_text_snapshots(self) -> None:
        payload = "Date,Close\n2026-03-10,123.45\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            client = RecordingHttpClient(
                snapshot_dir=tmpdir,
                text_client=FakeTextClient(payload),
            )

            response = client.get_text(
                "https://api.example.com/history.csv",
                params={"symbol": "spy.us"},
            )
            self.assertEqual(response, payload)

            replay = ReplayHttpClient(tmpdir)
            replayed = replay.get_text(
                "https://api.example.com/history.csv",
                params={"symbol": "spy.us"},
            )
            self.assertEqual(replayed, payload)

    def test_replay_client_matches_requests_by_params(self) -> None:
        payload = {"quote": 42}
        with tempfile.TemporaryDirectory() as tmpdir:
            client = RecordingHttpClient(
                snapshot_dir=tmpdir,
                json_client=FakeJsonClient(payload),
            )
            client.get_json(
                "https://api.example.com/quote",
                params={"symbol": "BTC", "depth": 5},
            )

            replay = ReplayHttpClient(tmpdir)
            self.assertEqual(
                replay.get_json(
                    "https://api.example.com/quote",
                    params={"depth": 5, "symbol": "BTC"},
                ),
                payload,
            )

    def test_replay_client_raises_for_missing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            replay = ReplayHttpClient(tmpdir)
            with self.assertRaises(SnapshotMissError):
                replay.get_json("https://api.example.com/missing", params={"id": 1})


if __name__ == "__main__":
    unittest.main()
