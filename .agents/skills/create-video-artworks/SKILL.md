---
name: create-video-artworks
description: "Continuously creates py5 media art animations in a loop. Each iteration follows the same workflow as create-video-artwork (plan → implement → review → commit). Runs until stopped. Triggers: create video artworks, batch video art, continuous animations"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Skill (Continuous)

Continuously creates py5 media art animations by repeating the single-artwork workflow in a loop. Each iteration produces a distinct work with a unique concept, theme, and technique.

## Workflow

1. Read `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. Create or switch to the branch `feature/works-YYYYMMDD` (use today's date)
3. **Loop** — Repeat the following for each new work:
   1. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, then produce a Creative Brief with **Format: Animation (10-30s @ 60fps)** (see `.agents/skills/planner/SKILL.md`)
   2. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` (see `.agents/skills/artist/SKILL.md`)
   3. Run the sketch to generate `output.mp4` and preview images, ensuring the process fully terminates
   4. **Critic**: Review code, video, and generated preview images and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
   5. If REVISE: artist applies feedback and re-runs (max 2 revisions)
   6. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions)
   7. Commit and push
   8. Start next iteration immediately — no user confirmation

## Notes

- Always choose a concept, theme, and technique different from every past work
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Animation is the primary output; ensure `output.mp4` is generated and committed for each work.
- The loop continues indefinitely until externally stopped
