# py5 Media Art — Autonomous Workflow

Use `/create-artwork` or `/create-artworks` to automate. Each step reads shared conventions.

## Workflow

1. **Branch** — `feature/works-$(date +%Y%m%d)`
2. **Plan** — Planner reads `sketch/WORKS.md` + `.agents/FEEDBACK.md` → Creative Brief (`.agents/skills/planner/SKILL.md`)
3. **Implement** — Artist executes brief in `sketch/{work_name}/main.py` (`.agents/skills/artist/SKILL.md`)
4. **Preview** — `uv run python sketch/{work_name}/main.py` → saves pattern-specific previews (ensure process terminates)
5. **Review** — Critic loop, max 2 revisions (`.agents/skills/critic/SKILL.md`)
6. **Document** — Add README.md, update `sketch/WORKS.md` and `.agents/FEEDBACK.md`
7. **Commit & Push**

## Shared Conventions

All agents must follow:

- **Work naming & preview files** — See `.agents/skills/shared/artwork-conventions.md`
- **py5 code templates & patterns** — See `.agents/skills/shared/py5-templates.md`
- **Directory structure** — See `.agents/skills/shared/artwork-conventions.md`
- **Safety & Aesthetics guidelines** — See `.agents/skills/shared/safety-and-aesthetics.md`

## Key Constraints

- **Resolution**: Preview 1920×1080 | Output 3840×2160 (change `SIZE` constant)
- **Retina**: After `py5.load_np_pixels()`, check `py5.np_pixels.shape[:2]` for actual size
- **No fixed seeds**: Results should vary each run
- `.agents/FEEDBACK.md` is reserved for user feedback only (agents do not write to Rating/Comment fields)
