---
name: create-artwork-lite
description: "Creates exactly one py5 media art still image with a lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Minimizes planning/review overhead while still generating preview images, updating records, committing, and pushing. Triggers: create artwork lite, lightweight artwork, NVIDIA proxy artwork"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Lite Skill

Creates one py5 media art still image using the lightweight mode of the canonical pipeline in `.agents/skills/shared/workflow.md` (optimized for slow proxy routes such as NVIDIA API).

## Mode Parameters

- **Format**: Still image (`{work_name}_p1.png`)
- **Loop Mode**: Single work (1 iteration)
- **Depth**: Lite (inline Creative Brief + 1 concise self-critique, max 1 revision; no separate subagent invocations)

## Execution

1. Read `.agents/skills/shared/workflow.md`, `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md`.
2. Execute the **Pre-Flight Setup** and one **Per-Work Iteration Pipeline** in **Lite Depth** (`plan` → inline brief → `main.py` & `README.md` → `check` → `render` → concise self-critique → `WORKS.md` / `FEEDBACK.md` → `commit & push` → `upload_to_drive.py`).
