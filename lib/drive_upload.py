"""
Send finished work outputs to Google Drive with rclone.

Each work gets its own folder on Drive: ``{remote}/{work_name}/``.

- Stills (``*.png``, ``*.jpg``) are copied; the repository keeps them.
- Videos (``*.mp4``, ``*.mov``, ``*.webm``) are moved; rclone verifies each
  upload by checksum and deletes the local copy only after it succeeds.
  Videos ffprobe cannot read stay local.

Remote:  PY5_UPLOAD_REMOTE (rclone "remote:path"; uploads are off when unset)
Disable: PY5_UPLOAD=0 (outputs then stay in the sketch folder)
Both are read from the environment or the repository's ``.env``.
Setup:   see README.md ("Google Drive upload").
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STILL_EXTENSIONS = {".png", ".jpg", ".jpeg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}


def _load_env() -> dict[str, str]:
    """Settings from .env, overridden by the process environment."""
    values: dict[str, str] = {}
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    for key in ("PY5_UPLOAD_REMOTE", "PY5_UPLOAD"):
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def remote() -> str:
    return _load_env().get("PY5_UPLOAD_REMOTE", "")


def _rclone(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(["rclone", *args], text=True, **kwargs)


def is_enabled() -> bool:
    """Upload is on when a destination is set, not disabled, and known to rclone."""
    env = _load_env()
    target = env.get("PY5_UPLOAD_REMOTE", "")
    if not target or env.get("PY5_UPLOAD") == "0":
        return False
    try:
        result = _rclone(["listremotes"], capture_output=True)
    except FileNotFoundError:
        return False
    if result.returncode != 0:
        return False
    return target.split(":")[0] + ":" in result.stdout.split()


def _is_readable_video(file: Path) -> bool:
    """Header check only; catches truncated or half-written files."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name:format=duration",
                "-of", "csv=p=0", str(file),
            ],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _transfer(command: str, work_dir: Path, names: list[str]) -> None:
    if not names:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as listing:
        listing.write("\n".join(names) + "\n")
    try:
        _rclone([
            command, str(work_dir), f"{remote()}/{work_dir.name}",
            "--files-from-raw", listing.name,
            "--retries", "3", "--stats-one-line", "--stats", "30s", "-v",
        ])
    finally:
        os.unlink(listing.name)


def upload_work(work_dir: Path) -> dict[str, list[str]]:
    """
    Copy stills and move videos of one work to ``{remote}/{work_name}/``.

    Returns {"copied": [...], "moved": [...], "kept": [...]} (file names).
    Does nothing (and returns empty lists) when uploads are disabled.
    """
    work_dir = Path(work_dir)
    report: dict[str, list[str]] = {"copied": [], "moved": [], "kept": []}
    if not is_enabled():
        return report

    files = sorted(p for p in work_dir.iterdir() if p.is_file())
    stills = [p.name for p in files if p.suffix.lower() in STILL_EXTENSIONS]
    videos = []
    for p in files:
        if p.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if _is_readable_video(p):
            videos.append(p.name)
        else:
            report["kept"].append(p.name)
            print(f"[Drive Upload] Kept {p.name}: ffprobe could not read it")

    print(f"[Drive Upload] {work_dir.name} -> {remote()}/{work_dir.name}")
    _transfer("copy", work_dir, stills)
    report["copied"] = stills
    _transfer("move", work_dir, videos)
    for name in videos:
        (report["kept"] if (work_dir / name).exists() else report["moved"]).append(name)
    if report["kept"]:
        print(f"[Drive Upload] Left in {work_dir}: {', '.join(report['kept'])}")
    return report


def fetch_videos(work_dir: Path) -> list[str]:
    """Download a work's videos from Drive back into its sketch folder."""
    work_dir = Path(work_dir)
    if not is_enabled():
        return []
    source = f"{remote()}/{work_dir.name}"
    include = [arg for ext in sorted(VIDEO_EXTENSIONS) for arg in ("--include", f"/*{ext}")]
    _rclone(["copy", source, str(work_dir), *include, "-v"])
    return sorted(p.name for p in work_dir.iterdir() if p.suffix.lower() in VIDEO_EXTENSIONS)
