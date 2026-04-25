---
name: create-artwork
description: "Autonomously creates a py5 media art sketch following the workflow in CLAUDE.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create artwork, new sketch, media art"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Skill

Autonomously creates a py5 media art sketch by following the workflow defined in `CLAUDE.md`.

## Workflow

1. Read `CLAUDE.md` to confirm the full workflow
2. Read `sketch/WORKS.md` and `sketch/FEEDBACK.md` to understand past works and user preferences
3. Create or reuse the branch `feature/works-YYYYMMDD`
4. Implement a new, non-duplicate sketch in `sketch/{work_name}/main.py`
5. Update `sketch/WORKS.md`
6. Commit and push

## Notes

- Always choose a concept, theme, and technique different from every past work
- Entry point filename is always `main.py`
- Work names use snake_case
