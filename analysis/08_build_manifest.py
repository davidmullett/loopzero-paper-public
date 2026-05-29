from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "results" / "frozen"
MANIFEST_DIR = ROOT / "results" / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

FILES_TO_TRACK = [
    FROZEN / "table1_domains.csv",
    FROZEN / "table2_equal_fp.csv",
    FROZEN / "table_s1_thresholds_public.csv",
    FROZEN / "fig3_leadtime_source.csv",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    entries = []
    for path in FILES_TO_TRACK:
        if path.exists():
            entries.append({
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256_file(path),
            })

    manifest = {
        "artifact_set": "loopzero-paper-public",
        "version": "0.1.0",
        "entries": entries,
    }

    manifest_path = MANIFEST_DIR / "artifact_manifest_public.json"
    checksums_path = MANIFEST_DIR / "checksums.txt"

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with checksums_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(f"{entry['sha256']}  {entry['path']}\n")

    print(f"Wrote {manifest_path}")
    print(f"Wrote {checksums_path}")

if __name__ == "__main__":
    main()
