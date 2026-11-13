---
name: create-artwork
description: "Autonomously creates a py5 media art still image following the workflow in AGENTS.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create artwork, new sketch, media art"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Skill

Autonomously creates a py5 media art still image by following the workflow defined in `AGENTS.md`.

## Workflow

1. Read `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. **Diversity Prescription**: Run `uv run python scripts/check_diversity.py plan` to obtain the 5-axis diversity prescription
3. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, then use the `logic-lab` MCP server to search for relevant algorithm references before producing a Creative Brief with **Format: Still image** (see `.agents/skills/planner/SKILL.md`)
4. Create or reuse the branch `feature/works-YYYYMMDD`
5. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` as 100% pure visual art; if the brief includes a Logic Lab Reference, fetch only those referenced files through the `logic-lab` MCP server (see `.agents/skills/artist/SKILL.md`)
6. **Programmatic Anti-Bias Check**: Run `uv run python scripts/check_diversity.py check {work_name}` and fix any violations
7. Run the sketch to generate pattern-specific preview images and ensure the process terminates (wait for completion and kill if it hangs)
8. **Critic**: Review code + generated preview images and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
9. If REVISE: artist applies feedback and re-runs (max 2 revisions)
10. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions)
11. Commit and push
12. Upload outputs to Google Drive: `uv run python scripts/upload_to_drive.py {work_name}` (see `.agents/skills/shared/drive-upload.md`)

## Notes

- Always choose a concept, theme, and technique different from every past work
- Never use `kinetic_` prefixes, `_2d`/`_3d` suffixes, `py5.text()`, or `FIG. 01..08` telemetry flank cards
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Prefer the `logic-lab` MCP server for external algorithm references. If the MCP server is unavailable, continue without `logic-lab` rather than relying on copied indexes from another repository.
- Never read all of `logic-lab`. Search first, then fetch only the specific algorithm files named in the Creative Brief.
