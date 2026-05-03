---
name: create-artworks
description: "Continuously creates py5 media art sketches in a loop. Each iteration follows the same workflow as create-artwork (plan → implement → review → commit). Runs until stopped. Triggers: create artworks, batch art, continuous sketches"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artworks Skill (Continuous)

Continuously creates py5 media art sketches by repeating the single-artwork workflow in a loop. Each iteration produces a distinct work with a unique concept, theme, and technique.

## Workflow

1. Read `CLAUDE.md` to confirm the full workflow and coding conventions
2. Create or switch to the branch `feature/works-YYYYMMDD` (use today's date)
3. **Loop** — Repeat the following for each new work:
   1. **Planner**: Read `sketch/WORKS.md` and `sketch/FEEDBACK.md`, then produce a Creative Brief (see `.agents/skills/planner/SKILL.md`)
   2. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` (see `.agents/skills/artist/SKILL.md`)
   3. Run the sketch to generate `preview.png` and wait for the process to fully terminate before proceeding (ensure no lingering python processes)
   4. **Critic**: Review code + `preview.png` and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
   5. If REVISE: artist applies feedback and re-runs (max 2 revisions)
   6. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md`
   7. Commit and push
   8. Start next iteration immediately — no user confirmation

## Notes

- Always choose a concept, theme, and technique different from every past work (re-read `WORKS.md` each iteration)
- Entry point filename is always `main.py`
- Work names use snake_case
- Each iteration is a self-contained artwork — do not carry state between works
- The loop continues indefinitely until externally stopped
