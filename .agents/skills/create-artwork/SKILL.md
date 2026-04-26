---
name: create-artwork
description: "Autonomously creates a py5 media art sketch following the workflow in CLAUDE.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create artwork, new sketch, media art"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Skill

Autonomously creates a py5 media art sketch by following the workflow defined in `CLAUDE.md`.

## Workflow

1. Read `CLAUDE.md` to confirm the full workflow
2. **Planner**: Read `sketch/WORKS.md` and `sketch/FEEDBACK.md`, then produce a Creative Brief (see `.agents/skills/planner/SKILL.md`)
3. Create or reuse the branch `feature/works-YYYYMMDD`
4. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` (see `.agents/skills/artist/SKILL.md`)
5. Run the sketch to generate `preview.png`
6. **Critic**: Review code + `preview.png` and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
7. If REVISE: artist applies feedback and re-runs (max 2 revisions)
8. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md`
9. Commit and push

## Notes

- Always choose a concept, theme, and technique different from every past work
- Entry point filename is always `main.py`
- Work names use snake_case
