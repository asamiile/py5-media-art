Autonomously polish and refine an existing artwork based on feedback from FEEDBACK.md.

The workflow:
1. **Select Target**: Read FEEDBACK.md and choose the highest-priority work needing improvement (blank/NG with actionable Comment)
2. **Analyze Feedback**: Extract improvement direction (color, pattern, abstraction, animation, clarity, realism, etc.)
3. **Implement**: Modify the sketch's main.py to address the feedback while preserving core identity
4. **Preview**: Generate new preview.png (save existing as preview_v{n}.png for version tracking)
5. **Document**: Update README.md and FEEDBACK.md with enhancement notes
6. **Commit**: Stage and commit changes with descriptive message

See `.agents/skills/polish/SKILL.md` for detailed implementation rules.
