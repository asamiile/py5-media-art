Execute `.agents/skills/create-artworks-lite/SKILL.md` following the canonical pipeline in `.agents/skills/shared/workflow.md`:

- **Format**: Still image (`sketch/{work_name}/{work_name}_p1.png`)
- **Mode**: Continuous loop with 60–90s rate-limit pause between works, Lite depth (inline Creative Brief + 1 concise self-critique; no subagent invocations)
- For each iteration, run `uv run python scripts/check_diversity.py plan` before planning and `uv run python scripts/check_diversity.py check {work_name}` before rendering
- Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment blank), commit & push on `feature/works-YYYYMMDD`, and run `uv run python scripts/upload_to_drive.py {work_name}`
