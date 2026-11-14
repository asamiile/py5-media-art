Execute `.agents/skills/polish/SKILL.md` to autonomously refine an existing artwork based on `.agents/FEEDBACK.md`:

1. Run `uv run python .agents/skills/polish/scripts/analyze_feedback.py` and select the highest-priority work in `.agents/FEEDBACK.md`
2. Create `sketch/{work_name}_v{n}` and implement targeted improvements in `main.py` while keeping 100% pure visual composition
3. Run `uv run python scripts/check_diversity.py check {work_name}_v{n}` and render `sketch/{work_name}_v{n}/{work_name}_v{n}_p1.png` (and `output.mp4` if animated)
4. Update `sketch/{work_name}_v{n}/README.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md` (leave Rating and Comment blank for the new entry)
5. Commit (`polish: {work_name}_v{n} — {specific_improvement}`) and run `uv run python scripts/upload_to_drive.py {work_name}_v{n}`
