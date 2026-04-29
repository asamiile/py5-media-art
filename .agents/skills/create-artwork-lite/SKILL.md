---
name: create-artwork-lite
description: "Creates exactly one py5 media art sketch with a lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Minimizes planning/review overhead while still generating preview.png, updating records, committing, and pushing. Triggers: create artwork lite, lightweight artwork, NVIDIA proxy artwork"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Lite Skill

Create exactly one new py5 media art sketch using a reduced-overhead version of the normal `create-artwork` workflow. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Use this skill when execution speed and fewer model/tool round trips matter more than a full Planner -> Artist -> Critic separation.

## Workflow

1. Read only the essential parts of `CLAUDE.md`, `sketch/WORKS.md`, and `sketch/FEEDBACK.md`.
2. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
3. Create or reuse branch `feature/works-YYYYMMDD`.
4. Produce a short inline creative brief:
   - work name
   - one-sentence theme
   - technique
   - 3-5 color palette
   - how it differs from recent works
5. Implement `sketch/{work_name}/main.py` and `README.md`.
6. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/preview.png` exists.
7. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
8. If the verdict is `REVISE`, apply at most one revision and regenerate `preview.png`; the second review should approve unless there is a hard failure.
9. Update both `sketch/WORKS.md` and `sketch/FEEDBACK.md`.
10. Stage only intended files:
    - `sketch/{work_name}/`
    - `sketch/WORKS.md`
    - `sketch/FEEDBACK.md`
11. Commit and push.
12. Report work name, score/verdict, changed files, and commit hash.

## Lightweight Rules

- Do not invoke separate Planner, Artist, or Critic agents.
- Do not run an indefinite loop.
- Do not perform more than one revision.
- Do not read every historical work in detail; scan enough of `WORKS.md` and `FEEDBACK.md` to avoid obvious repetition.
- Prefer a still image over MP4 unless the concept clearly requires motion.
- Prefer existing helpers in `lib/`:
  - `lib.paths.sketch_dir`
  - `lib.sizes.get_sizes`
  - `lib.preview.exit_after_preview_py5`
  - `lib.preview.maybe_save_exit_on_frame`
  - `lib.preview.save_preview_pil`
  - `lib.animation` only for animation output
- Never delete unrelated files or stage unrelated pending changes.

## Minimum Quality Bar

- The work must be visually intentional, not a default demo.
- The concept, technique, and palette must differ from recent works.
- `preview.png` must be generated before review and commit.
- `FEEDBACK.md` must receive at least one concise note for the new work.
- If critique tooling or visual inspection is unavailable, use a fallback self-critique in the critic format and explicitly output `APPROVE` or `REVISE`.

## Recommended Still Image Skeleton

```python
from pathlib import Path
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    py5.background(0)


def draw():
    # drawing logic
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR)


py5.run_sketch()
```
