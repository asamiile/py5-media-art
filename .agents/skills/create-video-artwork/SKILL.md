---
name: create-video-artwork
description: "Autonomously creates a py5 media art animation (video) following the workflow in AGENTS.md. Covers branch setup, past-work research, implementation, commit, and push. Triggers: create video artwork, new animation, video sketch"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artwork Skill

Autonomously creates a single py5 media art animation (video) by following the canonical pipeline in `.agents/skills/shared/workflow.md`.

## Mode Parameters

- **Format**: Animation (`15–30s @ 60fps`, `900`–`1800` frames; outputs `{work_name}.mp4` and `{work_name}.png`)
- **Loop Mode**: Single work (1 iteration)
- **Depth**: Standard (`Planner` → `Artist` → `Critic`, max 2 revisions)

## Execution

1. Read `.agents/skills/shared/workflow.md`, `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md`.
2. Execute the **Pre-Flight Setup** and one full **Per-Work Iteration Pipeline** (`plan` → `Creative Brief` → `main.py` → `check` → `render` → `Critic` → `README.md` / `WORKS.md` / `FEEDBACK.md` → `commit & push` → `upload_to_drive.py`).
3. Never commit `.mp4` files or `frames/`; videos are moved to Google Drive by `scripts/upload_to_drive.py`.
