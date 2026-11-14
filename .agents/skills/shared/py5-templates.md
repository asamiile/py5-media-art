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
WORK_NAME = SKETCH_DIR.name
PREVIEW_FRAME = 60
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)  # Capping density at 1x prevents extreme Retina-doubled rendering loads
    # Initialize canvas with the brief's background polarity


def draw():
    # Pure visual drawing logic across the full 3840x2160 canvas (zero py5.text)
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


py5.run_sketch()
```

## Animation

```python
from pathlib import Path
import random
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, step_animation_frame
from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = random.randint(15, 30)  # 15-30s (never lock to 12s / 720 frames)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)  # Capping density at 1x prevents extreme Retina-doubled rendering loads
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    # Pure visual drawing logic across the full 3840x2160 canvas (zero py5.text)
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
```

## Shader (optional)

GLSL shaders are an optional tool: a finishing pass (`PostFX`: bloom, tone map, grain...) and GPU fragment-shader fields. They need `py5.P2D`/`py5.P3D`. Usage, when to use / avoid, and gotchas: `.agents/skills/shared/shaders.md`.

```python
from lib.shaders import PostFX

fx = PostFX(bloom=0.8, tonemap=1.0, grain=0.03)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    fx.setup()

def draw():
    # drawing logic
    fx.apply()  # last step before maybe_save_exit_on_frame / step_animation_frame
```

## Notes

- Prefer helpers in `lib/`: `lib.paths.sketch_dir`, `lib.sizes.get_sizes`, `lib.preview`, and `lib.animation`.
- Save previews with `{work_name}.png` (`preview_filename(work_name=WORK_NAME)`).
- Explicitly call `maybe_save_exit_on_frame()` or `step_animation_frame()` so continuous runs do not leave sketch processes running.
- Animation works save sequential PNGs to `frames/` and compile `{work_name}.mp4` with ffmpeg, then remove `frames/`.
- MP4 files are generated outputs; do not commit them. After commit, they are moved to Google Drive (`.agents/skills/shared/drive-upload.md`).
- Do not fix random seed; results should vary each run.
- On Retina, after `py5.load_np_pixels()`, get actual size from `py5.np_pixels.shape[:2]`.
