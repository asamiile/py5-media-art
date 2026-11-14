Execute `.agents/skills/create-video-artwork-lite/SKILL.md` following the canonical pipeline in `.agents/skills/shared/workflow.md`:

- **Format**: Animation (`15–30s @ 60fps`, `900`–`1800` frames; outputs `output.mp4`, `{work_name}.mp4`, and `{work_name}_p1.png`)
- **Mode**: Single work, Lite depth (inline Creative Brief + 1 concise self-critique; no subagent invocations)
- Run `uv run python scripts/check_diversity.py plan` before planning and `uv run python scripts/check_diversity.py check {work_name}` before rendering
- Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment blank), commit & push on `feature/works-YYYYMMDD` (never stage `.mp4` or `frames/`), and run `uv run python scripts/upload_to_drive.py {work_name}`
