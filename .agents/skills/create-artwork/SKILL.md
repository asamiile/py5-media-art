---
name: create-artwork
description: "Autonomously creates a py5 media art still image following the workflow in CLAUDE.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create artwork, new sketch, media art"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Skill

Autonomously creates a py5 media art still image by following the workflow defined in `CLAUDE.md`.

## Workflow

1. Read `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, then use the `logic-lab` MCP server to search for relevant algorithm references before producing a Creative Brief with **Format: Still image** (see `.agents/skills/planner/SKILL.md`)
3. Create or reuse the branch `feature/works-YYYYMMDD`
4. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py`; if the brief includes a Logic Lab Reference, fetch only those referenced files through the `logic-lab` MCP server (see `.agents/skills/artist/SKILL.md`)
5. Run the sketch to generate pattern-specific preview images and ensure the process terminates (wait for completion and kill if it hangs)
6. **Critic**: Review code + generated preview images and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
7. If REVISE: artist applies feedback and re-runs (max 2 revisions)
8. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions)
9. Commit and push

## Notes

- Always choose a concept, theme, and technique different from every past work
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Prefer the `logic-lab` MCP server for external algorithm references. If the MCP server is unavailable, continue without `logic-lab` rather than relying on copied indexes from another repository.
- Never read all of `logic-lab`. Search first, then fetch only the specific algorithm files named in the Creative Brief.
