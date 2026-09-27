# Google Drive Upload

Videos are large (the repository once held ~40 GB of MP4s), so finished outputs live on Google Drive, not on the local disk.

## Flow

```text
render stills + video → review → commit stills (git) → upload
                                                         ├─ stills (*.png, *.jpg): copied  (stay in the repository)
                                                         └─ videos (*.mp4, *.mov, *.webm): moved (local copy deleted)
```

Destination: `<PY5_UPLOAD_REMOTE>/<work_name>/` — one Drive folder per work, mirroring `sketch/<work_name>/`.

## Commands

```bash
uv run python scripts/upload_to_drive.py {work_name}          # after commit & push
uv run python scripts/upload_to_drive.py --fetch {work_name}  # download a work's videos back (e.g. export-mobile)
uv run python scripts/upload_to_drive.py --all                # move every video still left in sketch/
uv run python scripts/upload_to_drive.py --enabled            # exit 0 when uploads are configured
```

## Rules

- Upload **after** commit & push, never before review: the Critic and verification steps need the local `output.mp4`/`{work_name}.mp4`.
- Implementation: `lib/drive_upload.py` (rclone). rclone verifies each upload by checksum and deletes the local video only after success. Videos that `ffprobe` cannot read stay local.
- Settings come from `.env` (gitignored; template in `.env.example`): `PY5_UPLOAD_REMOTE` (e.g. `gdrive:Media/py5-media-art`), `PY5_UPLOAD=0` to disable. Do not hardcode the Drive path in code.
- When uploads are not configured (no `.env`, rclone missing, remote unknown), the command prints a notice and exits 1. Report it and continue — this is not a workflow failure; videos simply stay local.
- Re-running an upload is safe: unchanged files are skipped, changed files are overwritten.
- Never delete files on Drive.
