---
description: "Autonomously creates a py5 media art sketch. Covers branch setup, past-work research, implementation, critic review, and commit/push."
---

# Create Artwork

Autonomously creates a py5 media art sketch by following the workflow defined in `CLAUDE.md`.

## Workflow

// turbo-all

1. Read `CLAUDE.md` to confirm the full workflow and coding conventions.

2. **Planner phase** — Read `sketch/WORKS.md` and `sketch/FEEDBACK.md`, then produce a Creative Brief following the process in `.agents/skills/planner/SKILL.md`:
   - Map coverage of past themes × techniques
   - Weight by user feedback (OK / NG ratings)
   - Propose one novel concept with: work name, theme, technique, color palette (3–5 colors), visual impression, format (still/animation), and rationale

3. Create or switch to the branch `feature/works-YYYYMMDD` (use today's date).

4. **Artist phase** — Implement the concept from the Creative Brief following `.agents/skills/artist/SKILL.md`:
   - Create `sketch/{work_name}/main.py` using the appropriate template (still image or animation)
   - Theme-first approach: emotion → palette → algorithm
   - Preview resolution: 1920×1080, Output resolution: 3840×2160 (use `SIZE` constant)
   - Use `py5.run_sketch()`, do not fix random seed
   - On Retina: after `py5.load_np_pixels()`, check `py5.np_pixels.shape[:2]` for actual size

5. **Preview** — Run the sketch to generate `preview.png`:
   ```bash
   uv run python sketch/{work_name}/main.py
   ```

6. **Critic phase** — Review code + `preview.png` following `.agents/skills/critic/SKILL.md`:
   - Score on 4 axes (Originality, Visual Impact, Technical Execution, Conceptual Depth) out of 10 each
   - APPROVE if total ≥ 30, otherwise REVISE with concrete code-level suggestions

7. **Revision loop** — If REVISE: artist applies feedback, re-runs sketch, critic reviews again (max 2 revisions; 3rd review must APPROVE).

8. **Document** — Create `sketch/{work_name}/README.md`, update `sketch/WORKS.md` and `sketch/FEEDBACK.md`.

9. **Commit & Push** — Stage all changes and push to the feature branch.

## Rules

- Always choose a concept, theme, and technique different from every past work
- Entry point filename is always `main.py`
- Work names use snake_case
- Limit palette to 3–5 colors; never use full-spectrum rainbow as default
- Include `output.mp4` in commit for animation works
- `frames/` directory is not committed
