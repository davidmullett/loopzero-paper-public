from __future__ import annotations

import csv
import gzip
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
PROVENANCE_FILENAME = f"{BENCHMARK_ID}__raw_input_provenance.json"

# Official GroupLens locations for MovieLens-25M
DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-25m.zip"
DATASET_MD5_URL = "https://files.grouplens.org/datasets/movielens/ml-25m.zip.md5"
README_URL = "https://files.grouplens.org/datasets/movielens/ml-25m-README.html"

ARCHIVE_FILENAME = "ml-25m.zip"
ARCHIVE_MD5_FILENAME = "ml-25m.zip.md5"
README_FILENAME = "ml-25m-README.html"

EXPECTED_EXTRACTED_FILES = [
    "README.txt",
    "genome-scores.csv",
    "genome-tags.csv",
    "links.csv",
    "movies.csv",
    "ratings.csv",
    "tags.csv",
]

SORTED_RATINGS_FILENAME = "ratings__sorted_by_user_time.csv.gz"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    data_external: Path
    data_raw: Path
    data_processed: Path
    results_frozen: Path
    results_manifests: Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, *, overwrite: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"[skip] exists: {dest}")
        return dest

    tmp = dest.with_suffix(dest.suffix + ".part")
    if tmp.exists():
        tmp.unlink()

    print(f"[download] {url} -> {dest}")
    with urllib.request.urlopen(url) as resp, tmp.open("wb") as out:
        shutil.copyfileobj(resp, out)

    tmp.replace(dest)
    return dest


def parse_md5_file(md5_path: Path) -> str:
    """
    Handles both formats:
      <md5>
      <md5>  filename
    """
    text = md5_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty MD5 file: {md5_path}")

    first_token = text.split()[0].strip()
    if len(first_token) != 32:
        raise ValueError(f"Could not parse MD5 from {md5_path}: {text!r}")
    return first_token.lower()


def ensure_contract(paths: RepoPaths) -> Dict:
    contract_path = paths.results_frozen / CONTRACT_FILENAME
    if not contract_path.exists():
        raise FileNotFoundError(
            f"Contract freeze not found at {contract_path}. "
            f"Run freeze_contract.py first."
        )

    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}"
        )

    dataset_name = contract.get("dataset", {}).get("name")
    if dataset_name != "MovieLens-25M":
        raise ValueError(
            f"Unexpected dataset in contract: {dataset_name!r}. "
            f"Expected 'MovieLens-25M'."
        )

    return contract


def extract_zip(archive_path: Path, dest_dir: Path, *, overwrite: bool = False) -> Path:
    """
    Extracts ml-25m.zip into dest_dir / 'ml-25m'.
    """
    extracted_root = dest_dir / "ml-25m"

    if extracted_root.exists() and not overwrite:
        print(f"[skip] extracted dir exists: {extracted_root}")
        return extracted_root

    if extracted_root.exists() and overwrite:
        shutil.rmtree(extracted_root)

    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"[extract] {archive_path} -> {dest_dir}")
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(dest_dir)

    if not extracted_root.exists():
        raise FileNotFoundError(
            f"Expected extracted directory not found: {extracted_root}"
        )

    return extracted_root


def validate_extracted_files(extracted_root: Path) -> List[Path]:
    found: List[Path] = []
    missing: List[str] = []

    for name in EXPECTED_EXTRACTED_FILES:
        path = extracted_root / name
        if path.exists():
            found.append(path)
        else:
            missing.append(name)

    if missing:
        raise FileNotFoundError(
            f"Missing expected extracted files under {extracted_root}: {missing}"
        )

    return found


def file_info(path: Path) -> Dict[str, object]:
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "md5": md5_file(path),
    }


def build_sorted_ratings(
    ratings_csv: Path,
    out_csv_gz: Path,
    *,
    overwrite: bool = False,
    chunksize: int = 2_000_000,
) -> Dict[str, object]:
    """
    Build ratings sorted chronologically within user.

    Official README says the raw file is ordered first by userId, then within user
    by movieId, so this step is required for chronological replay.
    """
    out_csv_gz.parent.mkdir(parents=True, exist_ok=True)

    if out_csv_gz.exists() and not overwrite:
        print(f"[skip] sorted ratings exists: {out_csv_gz}")
        return {
            "path": str(out_csv_gz),
            "size_bytes": out_csv_gz.stat().st_size,
            "sha256": sha256_file(out_csv_gz),
            "md5": md5_file(out_csv_gz),
            "sort_columns": ["userId", "timestamp", "movieId"],
            "stable_tie_break": "movieId ascending within identical timestamp",
            "overwritten": False,
        }

    print(f"[sort] loading ratings from {ratings_csv}")
    df = pd.read_csv(
        ratings_csv,
        usecols=["userId", "movieId", "rating", "timestamp"],
        dtype={
            "userId": "int32",
            "movieId": "int32",
            "rating": "float32",
            "timestamp": "int64",
        },
    )

    print("[sort] sorting by userId, timestamp, movieId")
    df = df.sort_values(
        by=["userId", "timestamp", "movieId"],
        ascending=[True, True, True],
        kind="mergesort",  # stable
        ignore_index=True,
    )

    print(f"[write] {out_csv_gz}")
    with gzip.open(out_csv_gz, "wt", encoding="utf-8", newline="") as gz:
        df.to_csv(gz, index=False)

    return {
        "path": str(out_csv_gz),
        "size_bytes": out_csv_gz.stat().st_size,
        "sha256": sha256_file(out_csv_gz),
        "md5": md5_file(out_csv_gz),
        "sort_columns": ["userId", "timestamp", "movieId"],
        "stable_tie_break": "movieId ascending within identical timestamp",
        "overwritten": True,
    }


def count_ratings_rows(ratings_csv: Path) -> int:
    """
    Fast-ish row count excluding header.
    """
    with ratings_csv.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in f) - 1


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        data_external=repo_root / "data" / "external" / "movielens25m",
        data_raw=repo_root / "data" / "raw" / "movielens25m",
        data_processed=repo_root / "data" / "processed" / "movielens25m",
        results_frozen=repo_root / "results" / "frozen",
        results_manifests=repo_root / "results" / "manifests",
    )


def build_provenance_manifest(
    *,
    contract: Dict,
    archive_info: Dict[str, object],
    official_md5: str,
    md5_verified: bool,
    readme_info: Dict[str, object],
    extracted_file_infos: List[Dict[str, object]],
    sorted_ratings_info: Dict[str, object],
    ratings_row_count: int,
) -> Dict[str, object]:
    return {
        "benchmark_id": BENCHMARK_ID,
        "stage": "raw_input_provenance",
        "contract_sha256": contract.get("contract_sha256"),
        "dataset": {
            "name": contract["dataset"]["name"],
            "source": contract["dataset"]["source"],
            "archive_url": DATASET_URL,
            "archive_md5_url": DATASET_MD5_URL,
            "readme_url": README_URL,
        },
        "archive": {
            **archive_info,
            "official_md5": official_md5,
            "md5_verified": md5_verified,
        },
        "readme": readme_info,
        "extracted_files": extracted_file_infos,
        "sorted_ratings": sorted_ratings_info,
        "ratings_row_count_raw_csv_excluding_header": ratings_row_count,
        "chronological_sort_rule": {
            "required_by_contract": True,
            "raw_order": ["userId", "movieId"],
            "sorted_order": ["userId", "timestamp", "movieId"],
        },
        "notes": [
            "The raw MovieLens ratings file is not chronologically ordered within user.",
            "Canonical replay should consume the sorted ratings artifact, not raw ratings.csv.",
            "This manifest is upstream provenance only and does not yet define episodes.",
        ],
    }


def run(
    *,
    repo_root: Path,
    overwrite_downloads: bool = False,
    overwrite_extract: bool = False,
    overwrite_sorted: bool = False,
) -> Path:
    paths = build_repo_paths(repo_root)
    paths.results_manifests.mkdir(parents=True, exist_ok=True)

    contract = ensure_contract(paths)

    archive_path = paths.data_external / ARCHIVE_FILENAME
    md5_path = paths.data_external / ARCHIVE_MD5_FILENAME
    readme_path = paths.data_external / README_FILENAME

    download_file(DATASET_URL, archive_path, overwrite=overwrite_downloads)
    download_file(DATASET_MD5_URL, md5_path, overwrite=overwrite_downloads)
    download_file(README_URL, readme_path, overwrite=overwrite_downloads)

    archive_md5_observed = md5_file(archive_path)
    archive_md5_official = parse_md5_file(md5_path)
    md5_verified = archive_md5_observed == archive_md5_official
    if not md5_verified:
        raise ValueError(
            f"Archive MD5 mismatch for {archive_path}:\n"
            f"  observed={archive_md5_observed}\n"
            f"  official={archive_md5_official}"
        )

    extracted_root = extract_zip(
        archive_path,
        paths.data_raw,
        overwrite=overwrite_extract,
    )

    extracted_paths = validate_extracted_files(extracted_root)

    ratings_csv = extracted_root / "ratings.csv"
    sorted_ratings_path = paths.data_processed / SORTED_RATINGS_FILENAME

    sorted_ratings_info = build_sorted_ratings(
        ratings_csv,
        sorted_ratings_path,
        overwrite=overwrite_sorted,
    )

    extracted_file_infos = [file_info(p) for p in extracted_paths]
    archive_info = file_info(archive_path)
    readme_info = file_info(readme_path)
    ratings_row_count = count_ratings_rows(ratings_csv)

    provenance = build_provenance_manifest(
        contract=contract,
        archive_info=archive_info,
        official_md5=archive_md5_official,
        md5_verified=md5_verified,
        readme_info=readme_info,
        extracted_file_infos=extracted_file_infos,
        sorted_ratings_info=sorted_ratings_info,
        ratings_row_count=ratings_row_count,
    )

    out_path = paths.results_manifests / PROVENANCE_FILENAME
    out_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[ok] wrote provenance manifest: {out_path}")
    print(f"[ok] archive md5 verified: {archive_md5_official}")
    print(f"[ok] sorted ratings: {sorted_ratings_path}")
    return out_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(
        repo_root=repo_root,
        overwrite_downloads=False,
        overwrite_extract=False,
        overwrite_sorted=False,
    )


if __name__ == "__main__":
    main()