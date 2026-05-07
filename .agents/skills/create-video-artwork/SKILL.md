---
name: create-video-artwork
description: "Autonomously creates a py5 media art animation (video) following the workflow in CLAUDE.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create video artwork, new animation, video sketch"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artwork Skill

Autonomously creates a py5 media art animation by following the workflow defined in `CLAUDE.md`.

## Workflow

1. Read `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, then use the `logic-lab` MCP server to search for relevant algorithm references before producing a Creative Brief with **Format: Animation (10-30s @ 60fps)** (see `.agents/skills/planner/SKILL.md`)
3. Create or reuse the branch `feature/works-YYYYMMDD`
4. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py`; ensure it uses FFmpeg for encoding (see `.agents/skills/artist/SKILL.md`)
5. Run the sketch to generate both the video file (`output.mp4`) and pattern-specific preview images; ensure the process terminates correctly
6. **Critic**: Review code, generated video, and preview images and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
7. If REVISE: artist applies feedback and re-runs (max 2 revisions)
8. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md`
9. Commit and push

## Notes

- Always choose a concept, theme, and technique different from every past work
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Prefer the `logic-lab` MCP server for external algorithm references.
- Animation is the primary output; ensure `output.mp4` is generated and committed.
