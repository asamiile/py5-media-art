Execute `.agents/skills/create-artwork/SKILL.md` following the canonical pipeline in `.agents/skills/shared/workflow.md`:

- **Format**: Still image (`sketch/{work_name}/{work_name}_p1.png`)
- **Mode**: Single work, Standard depth (`Planner` → `Artist` → `Critic`)
- Run `uv run python scripts/check_diversity.py plan` before planning and `uv run python scripts/check_diversity.py check {work_name}` before rendering and during review
- Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment blank), commit & push on `feature/works-YYYYMMDD`, and run `uv run python scripts/upload_to_drive.py {work_name}`
