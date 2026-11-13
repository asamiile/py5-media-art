from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any


def preview_filename(
    pattern: int = 1,
    revision: int | None = None,
    work_name: str | None = None,
) -> str:
    """
    Return the preview filename for a pattern and optional revision.

    When ``work_name`` is provided, returns ``{work_name}_p{pattern}.png``
    (or ``{work_name}_p{pattern}_v{revision}.png``) per current conventions.
    When ``work_name`` is omitted, returns ``preview_p{pattern}.png`` for
    backward compatibility with legacy sketches.
    """
    if pattern < 1:
        raise ValueError("pattern must be >= 1")
    if revision is not None and revision < 1:
        raise ValueError("revision must be >= 1")

    prefix = f"{work_name}_p{pattern}" if work_name else f"preview_p{pattern}"
    if revision is not None:
        prefix = f"{prefix}_v{revision}"
    return f"{prefix}.png"


def abort_if_blank(min_std: float = 1.0) -> None:
    """Abort the process if the current py5 canvas is blank (pixel std < min_std)."""
    import py5

    py5.load_np_pixels()
    if float(py5.np_pixels.std()) < min_std:
        print(
            f"[Error] Blank screen detected on frame {py5.frame_count} "
            f"(std < {min_std}). Aborting."
        )
        os._exit(1)


def save_preview_py5(sketch_dir: Path, filename: str | None = None) -> None:
    """Save the current py5 frame into ``sketch_dir/filename``."""
    import py5

    target = filename or preview_filename(work_name=sketch_dir.name)
    py5.save_frame(str(sketch_dir / target))


def exit_after_preview_py5(
    sketch_dir: Path,
    filename: str | None = None,
) -> None:
    """Save a preview image then forcefully exit the sketch."""
    import py5

    save_preview_py5(sketch_dir, filename=filename)
    py5.exit_sketch()
    # Force process exit to prevent macOS JVM/AWT threads from hanging
    time.sleep(0.5)
    os._exit(0)


def maybe_save_exit_on_frame(
    preview_frame: int,
    sketch_dir: Path,
    filename: str | None = None,
    *,
    check_blank: bool = True,
) -> None:
    """
    Check for blank frames on frame 2 / ``preview_frame``, and when
    ``py5.frame_count == preview_frame``, save the preview image and exit.
    """
    import py5

    if check_blank and (py5.frame_count == 2 or py5.frame_count == preview_frame):
        abort_if_blank()
    if py5.frame_count == preview_frame:
        exit_after_preview_py5(sketch_dir, filename=filename)


def save_preview_pil(
    img_array: Any,
    sketch_dir: Path,
    filename: str = "preview.png",
    *,
    mode: str = "RGB",
) -> None:
    """Save a numpy image array to ``sketch_dir/filename`` via PIL."""
    from PIL import Image

    Image.fromarray(img_array, mode).save(str(sketch_dir / filename))


def exit_sketch() -> None:
    """Small alias to keep call sites readable."""
    import py5

    py5.exit_sketch()
