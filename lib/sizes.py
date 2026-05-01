from __future__ import annotations

from typing import Optional, Tuple

# Default sizes used across most sketches.
PREVIEW_SIZE: Tuple[int, int] = (1920, 1080)
OUTPUT_SIZE: Tuple[int, int] = (3840, 2160)


def get_sizes(
    preview_size: Optional[Tuple[int, int]] = None,
    output_size: Optional[Tuple[int, int]] = None,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """
    Return (preview_size, output_size, size_for_py5).

    For this project, sketches commonly render at preview resolution and save
    only `preview.png` (output/mp4 generation is handled separately).
    """
    ps = preview_size or PREVIEW_SIZE
    os = output_size or OUTPUT_SIZE
    size_for_py5 = ps
    return ps, os, size_for_py5

