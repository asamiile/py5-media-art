from __future__ import annotations

from pathlib import Path
from typing import Any


def preview_filename(pattern: int = 1, revision: int | None = None) -> str:
    """Return the standard preview filename for a pattern and optional revision."""
    if pattern < 1:
        raise ValueError("pattern must be >= 1")
    if revision is not None and revision < 1:
        raise ValueError("revision must be >= 1")

    base = f"preview_p{pattern}"
    if revision is not None:
        base = f"{base}_v{revision}"
    return f"{base}.png"


def save_preview_py5(sketch_dir: Path, filename: str = "preview.png") -> None:
    """Save the current py5 frame into `sketch_dir/filename`."""
    import py5
    py5.save_frame(str(sketch_dir / filename))


def exit_after_preview_py5(
    sketch_dir: Path,
    filename: str = "preview.png",
) -> None:
    """Save a preview image then exit the sketch."""
    import py5
    save_preview_py5(sketch_dir, filename=filename)
    py5.exit_sketch()


def maybe_save_exit_on_frame(
    preview_frame: int,
    sketch_dir: Path,
    filename: str = "preview.png",
) -> None:
    """
    If `py5.frame_count == preview_frame`, save preview and exit.

    Intended for sketches that keep animating until a fixed frame.
    """
    import py5
    if py5.frame_count == preview_frame:
        exit_after_preview_py5(sketch_dir, filename=filename)


def save_preview_pil(
    img_array: Any,
    sketch_dir: Path,
    filename: str = "preview.png",
    *,
    mode: str = "RGB",
) -> None:
    """
    Save a numpy image array to `sketch_dir/filename` via PIL.

    `img_array` is expected to be a uint8-like HxWx3 array, but we avoid
    being strict to keep sketch freedom.
    """
    from PIL import Image

    Image.fromarray(img_array, mode).save(str(sketch_dir / filename))


def exit_sketch() -> None:
    """Small alias to keep call sites readable."""
    import py5
    py5.exit_sketch()
