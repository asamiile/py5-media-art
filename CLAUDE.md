# py5 Media Art — Claude Code Instructions

## Project Overview

A repository for autonomously creating media art with py5.

## Autonomous Artwork Creation Workflow

Follow these steps strictly when creating artwork autonomously.

### Step 1: Create or reuse the branch

If today's branch already exists, reuse it. Only create a new one if it does not exist.

```bash
BRANCH="feature/works-$(date +%Y%m%d)"
git fetch origin
git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" main
git pull origin "$BRANCH" 2>/dev/null || true
```

### Step 2: Survey past works and feedback

- Read `sketch/WORKS.md` to understand past works — theme, technique, and visual style
- Read `sketch/FEEDBACK.md` to understand user preferences (ignore entries with blank Rating)
- Check existing code under `sketch/` to avoid repeating ideas
- **Never create a work with the same concept, visual, or algorithm as a past work**

### Step 3: Implement a new sketch

- Implement the sketch in `sketch/{work_name}/main.py`
  - Use snake_case for the work name (e.g. `flowing_particles`, `recursive_tree`)
- Both still-image and animation works are supported (see templates below)

#### Size settings

| Mode | Resolution | Use |
|---|---|---|
| Preview | 1920×1080 | Sketch review and screenshot |
| Output | 3840×2160 | Export for UE / TouchDesigner |

- Screenshots are taken in **Preview mode**
- Switching to Output mode requires only changing `SIZE = OUTPUT_SIZE`

#### Template A — Still image

```python
from pathlib import Path
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120  # save preview ~2 seconds in and exit

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

def setup():
    py5.size(*SIZE)
    py5.background(0)

def draw():
    # drawing logic

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()

py5.run_sketch()
```

#### Template B — Animation (MP4 output)

```python
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # drawing logic (choose intentionally whether to call background() each frame)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / "preview.png")], check=True)

py5.run_sketch()
```

- Animation works save sequential PNGs to `frames/` and combine them into MP4 with ffmpeg
- ffmpeg required: `brew install ffmpeg`
- Include `output.mp4` in the commit

#### Other conventions

- Run with `py5.run_sketch()`
- Choose intentionally whether to call `background()` each frame (omit to leave trails)
- Do not fix the random seed — results should vary each run
- On Retina displays, `np_pixels` is 2× the SIZE. After `py5.load_np_pixels()`, get the actual size from `py5.np_pixels.shape[:2]`

### Step 4: Launch preview and save screenshot

```bash
uv run python sketch/{work_name}/main.py
```

- The sketch automatically saves `sketch/{work_name}/preview.png` and exits
- Copy the first screenshot as `preview_v1.png`:

```bash
cp sketch/{work_name}/preview.png sketch/{work_name}/preview_v1.png
```

### Step 4.5: Critic review (Artist → Critic → Artist loop)

As the **Critic** (`.agents/skills/critic/SKILL.md`), evaluate:

1. Check differentiation from past works in `sketch/WORKS.md`
2. Read `sketch/{work_name}/main.py`
3. View `sketch/{work_name}/preview.png`
4. Score on 4 axes: Originality, Visual Impact, Technical Execution, Conceptual Depth

**If Verdict is `REVISE`:**
- As the **Artist** (`.agents/skills/artist/SKILL.md`), apply the feedback concretely
- Re-run `uv run python sketch/{work_name}/main.py` to update `preview.png`
- Copy the improved screenshot as `preview_v{n}.png` (v2, v3…):

```bash
cp sketch/{work_name}/preview.png sketch/{work_name}/preview_v2.png
```

- Critic re-evaluates
- This loop runs **at most 2 times** — the 3rd review must always be `APPROVE`

**If Verdict is `APPROVE`:**
- `preview.png` is the final version; `preview_v{n}.png` files remain as process records
- Proceed to the next step

### Step 5: Create the work's README.md

Create `sketch/{work_name}/README.md`:

```markdown
# {Work Title in English}

![preview](preview.png)

{Description in English. Around 200 characters. Include theme, technique, and highlights.}
```

### Step 6: Update WORKS.md

Append to `sketch/WORKS.md`:

```markdown
## {work_name}

- **Date**: YYYY-MM-DD
- **Theme**: (e.g. fluid, geometry, nature)
- **Technique**: (e.g. particle system, recursion, noise)
- **Description**: One-line summary in English
```

### Step 7: Commit

```bash
git add sketch/{work_name}/
git add sketch/WORKS.md
git commit -m "feat: add {work_name} sketch"
```

### Step 8: Push

```bash
git push -u origin feature/works-$(date +%Y%m%d)
```

### Step 9: Update .agents/ if needed

Update `.agents/skills/` when new skills or configuration are required.

## Directory Structure

```
sketch/
  WORKS.md                  # registry of all works (always update)
  FEEDBACK.md               # user ratings and preferences (read before creating)
  {work_name}/
    main.py                 # entry point (fixed filename)
    preview.png             # final preview (always the latest)
    preview_v1.png          # first screenshot
    preview_v2.png          # improved screenshot (after REVISE)
    output.mp4              # animation works only
    frames/                 # sequential PNGs for animation (not committed)
    README.md               # work description
.agents/
  skills/
    create-artwork/         # single artwork creation skill
    create-artworks/        # continuous multi-artwork skill
    artist/                 # artist agent
    critic/                 # critic agent
.claude/
  settings.json             # permissions for autonomous execution
  commands/
    create-artwork.md       # /create-artwork command
    create-artworks.md      # /create-artworks command (continuous)
```

## Running a Sketch

```bash
uv run python sketch/{work_name}/main.py
```

## Prerequisites for Animation

```bash
brew install ffmpeg
```
