---
name: create-video-artworks-lite
description: "Continuously creates py5 media art animations with the lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Repeats create-video-artwork-lite-style iterations until interrupted, committing and pushing each work. Triggers: create video artworks lite, batch animation lite, continuous lightweight video, NVIDIA proxy videos"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Lite Skill (Continuous)

Continuously creates py5 media art animations using the lightweight mode of the canonical pipeline in `.agents/skills/shared/workflow.md` (optimized for slow proxy routes such as NVIDIA API).

## Mode Parameters

- **Format**: Animation (`15–30s @ 60fps`, `900`–`1800` frames; outputs `{work_name}.mp4` and `{work_name}.png`)
- **Loop Mode**: Continuous loop with a 60–90 second rate-limit pause between iterations
- **Depth**: Lite (inline Creative Brief + 1 concise self-critique, max 1 revision; no separate subagent invocations)

## Execution

1. Read `.agents/skills/shared/workflow.md`, `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md`.
2. Run **Pre-Flight Setup** once, then repeat the **Per-Work Iteration Pipeline** in **Lite Depth** (`plan` → inline brief → `main.py` & `README.md` → `check` → `render` → concise self-critique → `WORKS.md` / `FEEDBACK.md` → `commit & push` → `upload_to_drive.py` → wait 60–90s).
3. Never commit `.mp4` files or `frames/`; videos are moved to Google Drive by `scripts/upload_to_drive.py`.
