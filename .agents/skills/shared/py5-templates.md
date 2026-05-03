# py5 Templates

Shared implementation templates for py5 media art sketches.

## Still Image

```python
from pathlib import Path
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    py5.background(0)


def draw():
    # drawing logic
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


py5.run_sketch()
```

## Animation

```python
from pathlib import Path
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    # drawing logic; choose intentionally whether to call background() each frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()
```

## Notes

- Prefer helpers in `lib/`: `lib.paths.sketch_dir`, `lib.sizes.get_sizes`, and `lib.preview`.
- Save previews with `preview_filename(pattern=1)` unless creating additional patterns.
- Explicitly call `py5.exit_sketch()` or use `maybe_save_exit_on_frame()` so continuous runs do not leave sketch processes running.
- Animation works save sequential PNGs to `frames/` and combine into MP4 with ffmpeg.
- Include `output.mp4` in the commit only for animation works.
- Do not fix random seed; results should vary each run.
- On Retina, after `py5.load_np_pixels()`, get actual size from `py5.np_pixels.shape[:2]`.
