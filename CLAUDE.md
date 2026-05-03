# py5 Media Art — Autonomous Workflow

Use `/create-artwork` or `/create-artworks` to automate. See `.agents/skills/` for detailed guides.
Shared conventions live in `.agents/skills/shared/artwork-conventions.md` and `.agents/skills/shared/py5-templates.md`.

## Workflow

1. **Branch** — `feature/works-$(date +%Y%m%d)`
2. **Plan** — Planner reads `sketch/WORKS.md` + `.agents/FEEDBACK.md` → Creative Brief (`.agents/skills/planner/SKILL.md`)
3. **Implement** — Artist executes brief in `sketch/{work_name}/main.py` (`.agents/skills/artist/SKILL.md`)
4. **Preview** — `uv run python sketch/{work_name}/main.py` → saves pattern-specific previews (ensure process terminates)
5. **Review** — Critic loop, max 2 revisions (`.agents/skills/critic/SKILL.md`)
6. **Document** — Add README.md, update `sketch/WORKS.md` and `.agents/FEEDBACK.md`
7. **Commit & Push**

## Key Details

- **Work names**: Use snake_case for new concepts (e.g. `flowing_particles`). Do not add `_v1` to every first version. When intentionally remaking or replacing the idea of a past work, create a new directory with an incremented work-name suffix such as `flowing_particles_v2`, `flowing_particles_v3`, etc.; never overwrite the original directory.
- **Preview files**: Use `preview_p1.png` for the first generated pattern. If the work includes multiple distinct patterns or variants, save them as `preview_p2.png`, `preview_p3.png`, etc. Revision snapshots keep the pattern suffix before the revision suffix, e.g. `preview_p1_v1.png`.
- **Resolution**: Preview 1920×1080 | Output 3840×2160 (change `SIZE` constant)
- **Animation duration**: When creating video/animation works, make them **10 seconds or longer**.
- **Python**: Use `py5.run_sketch()`, don't fix random seed
- **Retina**: After `py5.load_np_pixels()`, check `py5.np_pixels.shape[:2]` for actual size

## Directory Structure

```
sketch/
  WORKS.md            # all works registry (always update)
  {work_name}/
    main.py           # entry point (fixed filename)
    preview_p1.png       # first/latest pattern preview
    preview_p2.png       # second pattern preview, if created
    preview_p1_v1.png    # p1 before first revision
    preview_p1_v2.png    # p1 before second revision
    output.mp4        # animation only
    frames/           # sequential PNGs — not committed
    README.md
  {work_name}_v2/     # remake/rework of a past work, if intentionally created
.agents/skills/
  planner/            # concept & palette brief
  artist/             # implementation
  critic/             # review
  create-artwork/     # single run
  create-artworks/    # continuous run
```

`.agents/FEEDBACK.md` stores agent-only user preference and critique memory.
