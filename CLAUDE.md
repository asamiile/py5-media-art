# py5 Media Art — Autonomous Workflow

## Workflow Overview

**Use `/create-artwork` or `/create-artworks` to automate. See `.agents/skills/` for detailed guides.**

1. **Branch**: `feature/works-$(date +%Y%m%d)`
2. **Research**: Verify unique concept via `WORKS.md` and `FEEDBACK.md`
3. **Implement**: Create `sketch/{work_name}/main.py` — see `.agents/skills/artist/SKILL.md` for templates
4. **Preview**: `uv run python sketch/{work_name}/main.py` → saves preview.png
5. **Critic Review**: Artist ↔ Critic loop (max 2 revisions)
6. **Document**: Add README.md, update WORKS.md and FEEDBACK.md
7. **Commit & Push**: Standard git workflow

## Key Details

- **Names**: Use snake_case (e.g. `flowing_particles`)
- **Resolution**: Preview 1920×1080 | Output 3840×2160 (change `SIZE` constant)
- **Python**: Use `py5.run_sketch()`, don't fix random seed
- **Retina**: After `py5.load_np_pixels()`, check `py5.np_pixels.shape[:2]` for actual size

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
