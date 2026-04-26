# py5 Media Art — Autonomous Workflow

Use `/create-artwork` or `/create-artworks` to automate. See `.agents/skills/` for detailed guides.

## Workflow

1. **Branch** — `feature/works-$(date +%Y%m%d)`
2. **Plan** — Planner reads `WORKS.md` + `FEEDBACK.md` → Creative Brief (`.agents/skills/planner/SKILL.md`)
3. **Implement** — Artist executes brief in `sketch/{work_name}/main.py` (`.agents/skills/artist/SKILL.md`)
4. **Preview** — `uv run python sketch/{work_name}/main.py` → saves `preview.png`
5. **Review** — Critic loop, max 2 revisions (`.agents/skills/critic/SKILL.md`)
6. **Document** — Add README.md, update `WORKS.md` and `FEEDBACK.md`
7. **Commit & Push**

## Key Details

- **Names**: snake_case (e.g. `flowing_particles`)
- **Resolution**: Preview 1920×1080 | Output 3840×2160 (change `SIZE` constant)
- **Python**: Use `py5.run_sketch()`, don't fix random seed
- **Retina**: After `py5.load_np_pixels()`, check `py5.np_pixels.shape[:2]` for actual size

## Directory Structure

```
sketch/
  WORKS.md            # all works registry (always update)
  FEEDBACK.md         # user preferences (read before creating)
  {work_name}/
    main.py           # entry point (fixed filename)
    preview.png       # latest preview
    preview_v1.png    # before first revision
    preview_v2.png    # before second revision
    output.mp4        # animation only
    frames/           # sequential PNGs — not committed
    README.md
.agents/skills/
  planner/            # concept & palette brief
  artist/             # implementation
  critic/             # review
  create-artwork/     # single run
  create-artworks/    # continuous run
```
