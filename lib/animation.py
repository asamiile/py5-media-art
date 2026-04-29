from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def frames_dir(sketch_dir: Path, dirname: str = "frames") -> Path:
    """Return the frame output directory for an animation sketch."""
    return sketch_dir / dirname


def save_animation_frame(frames_path: Path, pattern: str = "frame-####.png") -> None:
    """Save the current py5 frame into an animation frame sequence."""
    import py5

    py5.save_frame(str(frames_path / pattern))


def render_video_and_preview(
    sketch_dir: Path,
    frames_path: Path,
    *,
    fps: int,
    total_frames: int,
    preview_frame: int | None = None,
    output_filename: str = "output.mp4",
    preview_filename: str = "preview.png",
    input_pattern: str = "frame-%04d.png",
) -> None:
    """
    Build output.mp4 from saved frames and copy one frame to preview.png.

    This only handles the output plumbing; sketches still own all drawing logic.
    """
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-r",
            str(fps),
            "-i",
            str(frames_path / input_pattern),
            "-vcodec",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(sketch_dir / output_filename),
        ],
        check=True,
    )
    frame_no = preview_frame if preview_frame is not None else total_frames // 2
    shutil.copyfile(
        frames_path / f"frame-{frame_no:04d}.png",
        sketch_dir / preview_filename,
    )
