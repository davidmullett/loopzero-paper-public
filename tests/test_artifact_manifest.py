from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "results" / "manifests" / "artifact_manifest_public.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_manifest_exists():
    assert MANIFEST_PATH.exists(), f"Missing {MANIFEST_PATH}"

def test_manifest_matches_files():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        path = ROOT / entry["path"]
        assert path.exists(), f"Missing tracked artifact: {path}"
        assert sha256_file(path) == entry["sha256"], f"Checksum mismatch: {path}"
