---
name: create-video-artworks-lite
description: "Continuously creates py5 media art animations with the lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Repeats create-video-artwork-lite-style iterations until interrupted, committing and pushing each work. Triggers: create video artworks lite, batch animation lite, continuous lightweight video, NVIDIA proxy videos"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Lite Skill (Continuous)

Continuously create py5 media art animations using the lightweight workflow from `create-video-artwork-lite`. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Each iteration must produce one complete, independent animation and commit/push it before starting the next.

## Workflow

1. Read only the essential parts of `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Create or reuse branch `feature/works-YYYYMMDD`.
3. Loop until externally interrupted:
   1. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
   2. Produce a short inline creative brief with **Format: Animation (10-30s @ 60fps)**:
      - work name
      - one-sentence theme
      - technique
      - 3-5 color palette
      - how it differs from recent works
   3. Implement `sketch/{work_name}/main.py` and `README.md`.
   4. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/output.mp4` and `preview_p1.png` exist.
   5. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
   6. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions).
   7. Commit and push.
   8. Wait 60-90 seconds (Rate Limit) then start the next iteration.

## Lightweight Rules

- **MANDATORY**: Always produce Animations.
- Do not invoke separate Planner, Artist, or Critic agents.
- Animation is the primary output; ensure `output.mp4` is generated for each work. Commit MP4 files only when explicitly requested.
- Do not perform more than one revision per work.
- Follow `.agents/skills/shared/artwork-conventions.md` for naming and staging.
- The loop continues indefinitely until externally stopped.
