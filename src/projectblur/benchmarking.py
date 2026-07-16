"""Create reproducible, immutable JSON records for ProjectBlur benchmarks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any


def create_benchmark_metadata(
    project_root: Path,
    *,
    packages: Sequence[str] = (),
) -> dict[str, object]:
    """Return timestamp, runtime, and repository metadata for one benchmark run."""
    started_at = datetime.now(timezone.utc)
    package_versions: dict[str, str | None] = {}
    for package in packages:
        try:
            package_versions[package] = version(package)
        except PackageNotFoundError:
            package_versions[package] = None

    processor = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER")
    return {
        "run_id": started_at.strftime("%Y%m%dT%H%M%S.%fZ"),
        "recorded_at_utc": started_at.isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        ),
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor_identifier": processor,
            "logical_processors": os.cpu_count(),
            "python": platform.python_version(),
            "process_bits": 64 if os.sys.maxsize > 2**32 else 32,
            "packages": package_versions,
        },
        "repository": _repository_state(project_root),
    }


def file_evidence(path: Path, *, project_root: Path) -> dict[str, object]:
    """Return a portable path, size, and SHA-256 for a benchmark model file."""
    resolved = path.resolve()
    try:
        displayed_path = resolved.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        # Do not persist a machine-specific absolute path for an external override.
        displayed_path = resolved.name
    digest = hashlib.sha256()
    with resolved.open("rb") as model_file:
        for block in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "path": displayed_path,
        "bytes": resolved.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def save_benchmark_record(
    record: Mapping[str, Any],
    *,
    project_root: Path,
    filename_prefix: str,
    output: Path | None = None,
) -> Path:
    """Save one JSON record without overwriting evidence from an earlier run."""
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("benchmark record must contain a non-empty run_id")
    safe_prefix = re.sub(r"[^a-zA-Z0-9_.-]+", "_", filename_prefix).strip("._")
    if not safe_prefix:
        raise ValueError("filename_prefix must contain a filename-safe character")

    target = (
        output
        if output is not None
        else project_root / "artifacts" / "benchmarks" / f"{safe_prefix}_{run_id}.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as output_file:
            json.dump(record, output_file, indent=2, sort_keys=True)
            output_file.write("\n")
    except FileExistsError as error:
        raise FileExistsError(
            f"benchmark output already exists and will not be overwritten: {target}"
        ) from error
    return target


def _repository_state(project_root: Path) -> dict[str, object]:
    """Return Git provenance, or an explicit unavailable state outside Git."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "worktree_dirty": None}
    return {"commit": commit, "worktree_dirty": bool(status.strip())}
