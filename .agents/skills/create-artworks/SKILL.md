---
name: create-artworks
description: "Continuously creates py5 media art still images in a loop. Each iteration follows the same workflow as create-artwork (plan → implement → review → commit). Runs until stopped. Triggers: create artworks, batch art, continuous sketches"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artworks Skill (Continuous)

Continuously creates py5 media art still images in an autonomous loop by following the canonical pipeline in `.agents/skills/shared/workflow.md`.

## Mode Parameters

- **Format**: Still image (`{work_name}_p1.png`)
- **Loop Mode**: Continuous loop (repeats until externally stopped; no user confirmation between iterations)
- **Depth**: Standard (`Planner` → `Artist` → `Critic`, max 2 revisions)

## Execution

1. Read `.agents/skills/shared/workflow.md`, `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md`.
2. Run **Pre-Flight Setup** once, then repeat the **Per-Work Iteration Pipeline** in `.agents/skills/shared/workflow.md` indefinitely (`plan` → `Creative Brief` → `main.py` → `check` → `render` → `Critic` → `README.md` / `WORKS.md` / `FEEDBACK.md` → `commit & push` → `upload_to_drive.py`).
