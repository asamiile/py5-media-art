---
name: export-mobile
description: "Creates a py5 media art animation encoded for mobile playback: mp4/h.264/720p-or-lower/10–20s seamless loop. Triggers: export mobile, mobile video, mobile export, mobile render"
allowed-tools: Bash, Read, Write, Edit
---

# Export Mobile Skill

Create a py5 media art animation and encode it as a mobile-optimized video.

## Output Spec

| Item       | Value                          |
|------------|-------------------------------|
| Container  | MP4                           |
| Codec      | H.264 (`libx264`)            |
| Resolution | ≤ 1280×720 (720p)            |
| FPS        | 60                            |
| Duration   | 10–20 seconds                 |
| Loop       | Seamless (last frame → first) |
| Profile    | `baseline` level 3.1          |
| Fast-start | `-movflags +faststart`        |

## Workflow

1. Read `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
3. Create or reuse branch `feature/works-YYYYMMDD`.
4. Produce a short inline creative brief:
   - work name
   - one-sentence theme
   - technique
   - 3–5 color palette
   - how it differs from recent works
   - **Format: Mobile Animation (10–20s @ 60fps, seamless loop, 720p)**
5. Implement `sketch/{work_name}/main.py` with these constraints:
   - Set `SIZE = (1280, 720)` directly (do not use `get_sizes()`).
   - `DURATION_SEC` must be between 10 and 20.
   - Design the motion to loop seamlessly: the last frame must visually connect back to the first (e.g., use `t = frame_count / TOTAL_FRAMES` cycling through `[0, 1)`).
6. Run `uv run python sketch/{work_name}/main.py` and verify output.
7. The FFmpeg encoding step inside `main.py` **must** use:
   ```bash
   ffmpeg -y -r {FPS} \
     -i frames/frame-%04d.png \
     -vcodec libx264 \
     -profile:v baseline -level 3.1 \
     -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
     -pix_fmt yuv420p \
     -movflags +faststart \
     -crf 23 \
     {SKETCH_DIR}/{work_name}_mobile.mp4
   ```
   Output filename must end with `_mobile.mp4`.
8. Verify `{work_name}_mobile.mp4` and `{work_name}_p1.png` both exist.
9. Perform one concise self-critique (same format as `.agents/skills/critic/SKILL.md`). Apply at most one revision if REVISE.
10. Write `sketch/{work_name}/README.md`. Include a **Mobile Export** section noting the spec.
11. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty).
12. Stage and commit intended files in `sketch/{work_name}/`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
13. Push.

## py5 Template for Mobile

```python
from pathlib import Path
import math
import shutil
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

SIZE = (1280, 720)          # 720p for mobile
DURATION_SEC = 15           # 10–20 seconds; adjust per content
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    t = py5.frame_count / TOTAL_FRAMES  # 0.0 → <1.0; use for seamless loop

    # --- drawing logic ---

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render] {py5.frame_count}/{TOTAL_FRAMES} ({t*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print("[FFmpeg] Encoding mobile MP4...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264",
            "-profile:v", "baseline", "-level", "3.1",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-crf", "23",
            str(SKETCH_DIR / f"{WORK_NAME}_mobile.mp4"),
        ], check=True)

        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)


py5.run_sketch()
```

## Seamless Loop Design Patterns

- **Trigonometric cycling**: use `t * 2 * math.pi` as the phase angle → returns to start automatically.
- **Modular offset**: advance all elements by a fixed step each frame so that at `t=1.0` the state equals `t=0.0`.
- **Noise loop**: use `py5.noise(cos(t*TAU)*r, sin(t*TAU)*r)` with a fixed radius `r` to close the loop in noise space.

## Key Rules

- Do **not** use `get_sizes()`; set `SIZE = (1280, 720)` directly.
- `DURATION_SEC` must be **10–20**.
- Output file must be `{work_name}_mobile.mp4`, not `output.mp4`.
- Seamless loop is **mandatory**: test visually that frame 1 ≈ frame TOTAL_FRAMES.
- Do not commit MP4 files unless explicitly requested.
- Follow `.agents/skills/shared/artwork-conventions.md` for all other naming and staging rules.
