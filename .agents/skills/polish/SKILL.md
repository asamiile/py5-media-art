---
name: polish
description: "Autonomously polish and refine existing artwork based on user feedback. Selects improvement target from .agents/FEEDBACK.md, generates enhancement plan, and implements updated version."
allowed-tools: Bash, Read, Write, Edit
---

# Polish Artwork Skill

Autonomously polishes an existing py5 media art sketch by analyzing feedback, selecting an improvement target, and implementing an enhanced version.

## Workflow

1. **Read Shared Conventions**
   - Read `.agents/skills/shared/artwork-conventions.md` before editing preview files

2. **Parse `.agents/FEEDBACK.md`**
   - Read all work entries with ratings and comments
   - Calculate improvement priority (blank/NG with comment → OK with comment)
   
3. **Select Polish Target**
   - Choose the highest-priority work needing improvement
   - Criteria: Rating blank or NG with actionable Comment, OR OK with feature requests
   
4. **Analyze Comment & Generate Plan**
   - Extract improvement direction from Comment text
   - Categories:
     - Color/Pattern: "see other colors", "monotonous color", "see other patterns"
     - Abstraction: "more abstract", "less abstract"
     - Animation: "want to watch animation"
     - Clarity: "too blurry", "patterns overlap"
     - Realism: "reproduce natural phenomena"
   - Generate specific implementation directives
   
5. **Implement Enhancement**
   - Read existing `sketch/{work_name}/main.py`
   - Modify code to address Comment directives
   - Keep the core algorithm, adjust parameters/colors/density
   - Save the existing preview as a versioned snapshot before editing, following `.agents/skills/shared/artwork-conventions.md`; legacy `preview.png` may use `preview_v{n}.png`
   
6. **Preview & Verify**
   - Run: `uv run python sketch/{work_name}/main.py`
   - Generate the updated pattern-specific preview
   - Verify visual improvement matches intent
   
7. **Update Documentation**
   - Edit `sketch/{work_name}/README.md` with enhancement notes
   - Update `.agents/FEEDBACK.md` with the new versioned preview reference and revised Comment
   
8. **Commit**
   - Stage changes: main.py, preview image files, versioned preview snapshots, README.md, `.agents/FEEDBACK.md`
   - Commit: "polish: {work_name} — {improvement_summary}"

## Selection Priority

For next improvement target, prioritize in this order:
1. **Critical**: Rating = NG with Comment (clear rejection needing fix)
2. **High**: Rating blank with Comment (not yet evaluated, has feedback)
3. **Medium**: Rating = OK with Comment + feature request (approved direction, expand it)
4. **Low**: Rating = OK with Comment + minor tweak (nice-to-have)

## Implementation Rules

- Keep original algorithm/theme; modify only parameters/colors/patterns
- If Comment requests "other colors", vary palette; use artistic combinations (not single-gradient)
- If Comment requests "other patterns", add algorithmic variants (multiple Truchet orientations, Rule variants, etc.)
- If Comment requests "more abstract", reduce density/increase transformation depth; if "more realistic", add details/constraints
- If Comment mentions animation, change to `py5.run_sketch(continuous=True)` or add frame-based evolution
- Never change work name or core identity
- Document what changed in README for transparency

## Notes

- Follow `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Preview resolution: 1920×1080 (change `SIZE` in script for output 3840×2160)
- Preserve git history by creating separate commit (not amending)
