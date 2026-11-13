---
name: create-video-artwork-lite
description: "Creates exactly one py5 media art animation (video) with a lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Minimizes planning/review overhead while still generating output.mp4, updating records, committing, and pushing. Triggers: create video artwork lite, lightweight animation, NVIDIA proxy video"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artwork Lite Skill

Create exactly one new py5 media art animation using a reduced-overhead version of the normal `create-video-artwork` workflow. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

## Workflow

1. Read only the essential parts of `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
3. Create or reuse branch `feature/works-YYYYMMDD`.
4. Run `uv run python scripts/check_diversity.py plan` to get the 5-axis diversity prescription.
5. Produce a short inline creative brief with **Format: Animation (15-30s @ 60fps)**:
   - work name (2–4 words, no `kinetic_` prefix, no `_2d`/`_3d` suffix)
   - genre, composition archetype, and motion archetype
   - one-sentence theme
   - technique
   - 3–5 color palette
   - how it differs from recent works
6. Implement `sketch/{work_name}/main.py` (100% pure visual art across 3840×2160; zero `py5.text()`, zero flank cards or medallions) and `README.md`. Ensure it uses FFmpeg for encoding.
7. Run `uv run python scripts/check_diversity.py check {work_name}` and fix any reported bias issues.
8. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/output.mp4` and `{work_name}_p1.png` exist.
9. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
10. If the verdict is `REVISE`, apply at most one revision; the second review should approve unless there is a hard failure.
11. Update both `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions).
12. Stage and commit the intended non-ignored files in `sketch/{work_name}/`, plus `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
13. Push.
14. Upload outputs to Google Drive: `uv run python scripts/upload_to_drive.py {work_name}` (see `.agents/skills/shared/drive-upload.md`).

## Lightweight Rules

- **MANDATORY**: Always produce an Animation (15–30s @ 60fps; never 12s / 720 frames).
- **Pure Visual Canvas**: Never use `py5.text()`, `FIG. 01..08` telemetry flank cards, museum borders, or central compass bezels.
- Do not invoke separate Planner, Artist, or Critic agents.
- Do not run an indefinite loop.
- Do not perform more than one revision.
- Animation is the primary output; ensure `output.mp4` is generated. Never commit MP4 files; they live on Google Drive after the upload step.
- Follow `.agents/skills/shared/artwork-conventions.md` for naming and staging.
