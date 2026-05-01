from __future__ import annotations

from pathlib import Path
from typing import Any


def save_preview_py5(sketch_dir: Path, filename: str = "preview.png") -> None:
    """Save the current py5 frame into `sketch_dir/preview.png`."""
    import py5
    py5.save_frame(str(sketch_dir / filename))


def exit_after_preview_py5(
    sketch_dir: Path,
    filename: str = "preview.png",
) -> None:
    """Save `preview.png` then exit the sketch."""
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
    Save a numpy image array to `sketch_dir/preview.png` via PIL.

    `img_array` is expected to be a uint8-like HxWx3 array, but we avoid
    being strict to keep sketch freedom.
    """
    from PIL import Image

    Image.fromarray(img_array, mode).save(str(sketch_dir / filename))


def exit_sketch() -> None:
    """Small alias to keep call sites readable."""
    import py5
    py5.exit_sketch()
