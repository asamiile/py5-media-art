---
name: create-video-artwork
description: "Autonomously creates a py5 media art animation (video) following the workflow in AGENTS.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create video artwork, new animation, video sketch"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artwork Skill

Autonomously creates a py5 media art animation by following the workflow defined in `AGENTS.md`.

## Workflow

1. Read `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. **Diversity Prescription**: Run `uv run python scripts/check_diversity.py plan` to obtain the 5-axis diversity prescription and banned subject tokens
3. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, then use the `logic-lab` MCP server to search for relevant algorithm references before producing a Creative Brief with **Format: Animation (15-30s @ 60fps)** (see `.agents/skills/planner/SKILL.md`)
4. Create or reuse the branch `feature/works-YYYYMMDD`
5. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` as 100% full-bleed visual art (zero `py5.text()`, zero flank cards or medallions); ensure it uses FFmpeg for encoding (see `.agents/skills/artist/SKILL.md`)
6. **Programmatic Anti-Bias Check**: Run `uv run python scripts/check_diversity.py check {work_name}` and fix any violations before rendering
7. Run the sketch to generate both the video file (`output.mp4` / `{work_name}.mp4`) and pattern-specific preview images (`{work_name}_p1.png`); ensure the process terminates correctly
8. **Critic**: Run `uv run python scripts/check_diversity.py check {work_name}`, review code, generated video, and preview images, and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
9. If REVISE: artist applies feedback and re-runs (max 2 revisions; `check_diversity.py check` must PASS)
10. Create `sketch/{work_name}/README.md` and update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions)
11. Commit and push
12. Upload outputs to Google Drive: `uv run python scripts/upload_to_drive.py {work_name}` (see `.agents/skills/shared/drive-upload.md`)

## Notes

- Always choose a concept, genre, composition archetype, motion archetype, and tonal palette different from recent works
- Never use `kinetic_` prefixes, `_2d`/`_3d` suffixes, `py5.text()`, or `FIG. 01..08` telemetry flank cards
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Prefer the `logic-lab` MCP server for external algorithm references.
- Animation is the primary output; ensure `output.mp4` is generated. Never commit MP4 files; they live on Google Drive after the upload step.
