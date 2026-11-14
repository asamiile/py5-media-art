---
name: create-video-artworks
description: "Continuously creates py5 media art animations in a loop. Each iteration follows the same workflow as create-video-artwork (plan → implement → review → commit). Runs until stopped. Triggers: create video artworks, batch video art, continuous animations"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Skill (Continuous)

Continuously creates py5 media art animations in an autonomous loop by following the canonical pipeline in `.agents/skills/shared/workflow.md`.

## Mode Parameters

- **Format**: Animation (`15–30s @ 60fps`, `900`–`1800` frames; outputs `{work_name}.mp4` and `{work_name}.png`)
- **Loop Mode**: Continuous loop (repeats until externally stopped; no user confirmation between iterations)
- **Depth**: Standard (`Planner` → `Artist` → `Critic`, max 2 revisions)

## Execution

1. Read `.agents/skills/shared/workflow.md`, `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md`.
2. Run **Pre-Flight Setup** once, then repeat the **Per-Work Iteration Pipeline** in `.agents/skills/shared/workflow.md` indefinitely (`plan` → `Creative Brief` → `main.py` → `check` → `render` → `Critic` → `README.md` / `WORKS.md` / `FEEDBACK.md` → `commit & push` → `upload_to_drive.py`).
3. Never commit `.mp4` files or `frames/`; videos are moved to Google Drive by `scripts/upload_to_drive.py`.
