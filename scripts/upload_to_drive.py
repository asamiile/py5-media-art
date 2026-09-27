"""
Send work outputs to Google Drive (see lib/drive_upload.py).

  uv run python scripts/upload_to_drive.py <work_name> [...]   # upload the given works
  uv run python scripts/upload_to_drive.py --all               # every work that still has a local video
  uv run python scripts/upload_to_drive.py --fetch <work_name> # download a work's videos back
  uv run python scripts/upload_to_drive.py --enabled           # exit 0 when uploads are configured
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from lib.drive_upload import VIDEO_EXTENSIONS, fetch_videos, is_enabled, remote, upload_work

SKETCH_ROOT = PROJECT_ROOT / "sketch"


def work_dir(name: str) -> Path:
    path = SKETCH_ROOT / Path(name).name
    if not path.is_dir():
        sys.exit(f"Work not found: {path}")
    return path


def works_with_videos() -> list[Path]:
    return sorted(
        d for d in SKETCH_ROOT.iterdir()
        if d.is_dir() and any(p.suffix.lower() in VIDEO_EXTENSIONS for p in d.iterdir())
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("works", nargs="*", help="work names (sketch/<work_name>)")
    parser.add_argument("--all", action="store_true", help="upload every work that still has a local video")
    parser.add_argument("--fetch", action="store_true", help="download videos of the given works from Drive")
    parser.add_argument("--enabled", action="store_true", help="only report whether uploads are configured")
    args = parser.parse_args()

    if args.enabled:
        return 0 if is_enabled() else 1
    if not is_enabled():
        print("Drive upload is off: set PY5_UPLOAD_REMOTE in .env and configure rclone (see README.md).")
        return 1

    if args.fetch:
        for name in args.works:
            print(f"{name}: {', '.join(fetch_videos(work_dir(name))) or 'no videos on Drive'}")
        return 0

    targets = works_with_videos() if args.all else [work_dir(n) for n in args.works]
    if not targets:
        parser.print_usage()
        return 1

    kept = []
    for i, target in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {target.name}")
        kept += [f"{target.name}/{n}" for n in upload_work(target)["kept"]]
    print(f"Done: {len(targets)} works -> {remote()}")
    if kept:
        print("Left locally:\n  " + "\n  ".join(kept))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
