---
name: create-video-artworks-lite
description: "Continuously creates py5 media art animations with the lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Repeats create-video-artwork-lite-style iterations until interrupted, committing and pushing each work. Triggers: create video artworks lite, batch animation lite, continuous lightweight video, NVIDIA proxy videos"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Lite Skill (Continuous)

Continuously create py5 media art animations using the lightweight workflow from `create-video-artwork-lite`. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Each iteration must produce one complete, independent full-bleed animation and commit/push it before starting the next.

## Workflow

1. Read only the essential parts of `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Create or reuse branch `feature/works-YYYYMMDD`.
3. Loop until externally interrupted:
   1. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
   2. Run `uv run python scripts/check_diversity.py plan` to get the 5-axis diversity prescription (target genre, composition archetype, motion archetype, tonal family, and banned subject tokens).
   3. Produce a short inline creative brief with **Format: Animation (15-30s @ 60fps)**:
      - work name (2–4 words, no `kinetic_` prefix, no `_2d`/`_3d` suffix)
      - genre, composition archetype, and motion archetype
      - one-sentence theme (sensory/visual, not a historical treatise)
      - technique
      - 3–5 color palette (full-canvas tonal polarity)
      - how it differs from recent works
   4. Implement `sketch/{work_name}/main.py` (100% pure visual art across 3840×2160; zero `py5.text()`, zero flank cards or medallions) and `README.md`.
   5. Run `uv run python scripts/check_diversity.py check {work_name}` and fix any reported bias issues.
   6. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/output.mp4` and `{work_name}_p1.png` exist.
   7. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
   8. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions).
   9. Commit and push.
   10. Upload outputs to Google Drive: `uv run python scripts/upload_to_drive.py {work_name}` (see `.agents/skills/shared/drive-upload.md`).
   11. Wait 60-90 seconds (Rate Limit) then start the next iteration.

## Lightweight Rules

- **MANDATORY**: Always produce Animations (15–30s @ 60fps; never 12s / 720 frames).
- **Pure Visual Canvas**: Never use `py5.text()`, `FIG. 01..08` telemetry flank cards, museum borders, or central compass bezels.
- Do not invoke separate Planner, Artist, or Critic agents.
- Animation is the primary output; ensure `output.mp4` is generated for each work. Never commit MP4 files; they live on Google Drive after the upload step.
- Do not perform more than one revision per work (except fixing `check_diversity.py` errors).
- Follow `.agents/skills/shared/artwork-conventions.md` for naming and staging.
- The loop continues indefinitely until externally stopped.
