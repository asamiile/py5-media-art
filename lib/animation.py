from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from lib.preview import abort_if_blank, preview_filename


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
    cleanup_frames: bool = False,
) -> None:
    """
    Build ``output.mp4`` from saved frames and copy one frame to ``preview_filename``.
    """
    output_path = sketch_dir / output_filename
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
            str(output_path),
        ],
        check=True,
    )

    frame_no = preview_frame if preview_frame is not None else max(1, total_frames // 2)
    frame_file = frames_path / f"frame-{frame_no:04d}.png"
    if not frame_file.exists():
        # Fallback if 0-indexed or different frame numbering
        candidates = sorted(frames_path.glob("frame*.png"))
        if candidates:
            frame_file = candidates[len(candidates) // 2]
    if frame_file.exists():
        shutil.copyfile(frame_file, sketch_dir / preview_filename)

    if cleanup_frames and frames_path.exists():
        shutil.rmtree(frames_path)


def step_animation_frame(
    sketch_dir: Path,
    frames_path: Path,
    *,
    fps: int = 60,
    total_frames: int,
    preview_name: str | None = None,
) -> None:
    """
    Per-frame helper for animation ``draw()`` loops:
    1. Saves the current frame to ``frames/frame-####.png``.
    2. Checks for blank screens on frame 2 and every 60 frames.
    3. Prints render progress every 60 frames.
    4. On ``total_frames``, compiles ``output.mp4`` + ``{work_name}.mp4``,
       copies the midpoint frame to ``{work_name}_p1.png``, deletes ``frames/``,
       and terminates the process cleanly.
    """
    import py5

    save_animation_frame(frames_path)

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        abort_if_blank()

    if py5.frame_count % 60 == 0:
        pct = py5.frame_count / total_frames * 100
        print(f"[Render Progress] Frame {py5.frame_count}/{total_frames} ({pct:.1f}%)")

    if py5.frame_count >= total_frames:
        py5.exit_sketch()
        target_preview = preview_name or preview_filename(work_name=sketch_dir.name)
        print(f"[Render FFmpeg] Compiling {total_frames} frames into video...")
        render_video_and_preview(
            sketch_dir,
            frames_path,
            fps=fps,
            total_frames=total_frames,
            output_filename="output.mp4",
            preview_filename=target_preview,
            cleanup_frames=True,
        )
        print("[Render Cleanup] Temporary frames directory successfully removed.")
        os._exit(0)
