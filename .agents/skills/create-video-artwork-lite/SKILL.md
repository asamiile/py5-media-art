---
name: create-video-artwork-lite
description: "Creates exactly one py5 media art animation (video) with a lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Minimizes planning/review overhead while still generating output.mp4, updating records, committing, and pushing. Triggers: create video artwork lite, lightweight animation, NVIDIA proxy video"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artwork Lite Skill

Create exactly one new py5 media art animation using a reduced-overhead version of the normal `create-video-artwork` workflow. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

## Workflow

1. Read only the essential parts of `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
3. Create or reuse branch `feature/works-YYYYMMDD`.
4. Produce a short inline creative brief with **Format: Animation (10-30s @ 60fps)**:
   - work name
   - one-sentence theme
   - technique
   - 3-5 color palette
   - how it differs from recent works
5. Implement `sketch/{work_name}/main.py` and `README.md`. Ensure it uses FFmpeg for encoding.
6. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/output.mp4` and `preview_p1.png` exist.
7. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
8. If the verdict is `REVISE`, apply at most one revision; the second review should approve unless there is a hard failure.
9. Update both `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions).
10. Stage and commit `sketch/{work_name}/`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
11. Push.

## Lightweight Rules

- **MANDATORY**: Always produce an Animation (video).
- Do not invoke separate Planner, Artist, or Critic agents.
- Do not run an indefinite loop.
- Do not perform more than one revision.
- Animation is the primary output; ensure `output.mp4` is generated and committed.
- Follow `.agents/skills/shared/artwork-conventions.md` for naming and staging.
