---
name: polish
description: "Autonomously polish and refine existing artwork based on user feedback. Includes feedback analytics to identify trends and a critique loop to ensure high-precision refinements."
allowed-tools: Bash, Read, Write, Edit
---

# Polish Artwork Skill

Autonomously polishes an existing py5 media art sketch by analyzing feedback trends, selecting an improvement target, and implementing an enhanced version with high precision.

## Workflow

1. **Perform Feedback Analytics**
   - Run the analytics script to identify trends: `uv run python .agents/skills/polish/scripts/analyze_feedback.py`
   - **Identify Patterns**: Use the script's output to identify keywords in positive and negative feedback (e.g., spatial density, motion pacing, contrast, abstraction level, tonal balance).
   - **Trend Analysis**: Check how the user's preferences apply to the selected work without forcing a uniform dark/gold palette across unrelated genres.
   - Create an internal summary of "User Preference Constraints" to guide the next polish.

2. **Select Polish Target**
   - Parse all work entries and calculate priority (see **Selection Priority**).
   - Choose the highest-priority work.
   - Cross-reference with `sketch/WORKS.md` to ensure the core technique is understood.

3. **Generate Precise Refinement Plan**
   - Analyze the specific Comment for the selected target.
   - **Contextualize**: Combine the specific request with the **Feedback Analytics** results while preserving the work's genre, composition archetype, and tonal identity unless the comment asks to change them.
   - **Define Directives**: Create 3–5 specific code-level changes (e.g., "Adjust trail decay alpha," "Introduce multi-scale harmonic modulation," "Convert legacy infographic/text overlays into pure full-bleed visual geometry").

4. **Implement Enhancement (New Version)**
   - Follow `.agents/skills/shared/artwork-conventions.md` and `.agents/skills/shared/py5-templates.md` strictly.
   - **Create New Directory**: Copy the existing `sketch/{work_name}` to `sketch/{work_name}_v{n+1}`.
   - **Refine Code**: Modify `main.py` in the NEW directory according to the directives. Ensure 100% pure visual composition (zero `py5.text()`, zero flank cards).
   - **Maintain Identity**: Preserve the core algorithmic theme while elevating visual impact, composition, or motion.

5. **Programmatic Check, Preview & Self-Critique**
   - Run `uv run python scripts/check_diversity.py check {work_name}_v{n}` and resolve any violations.
   - Run `uv run python sketch/{work_name}_v{n}/main.py` to generate `{work_name}_v{n}_p1.png` (and `output.mp4` if animated).
   - **Self-Critique Loop**: Evaluate the result against the **Refinement Plan** and **Critic axes** (`.agents/skills/critic/SKILL.md`).
   - If the result doesn't fully address the feedback, perform one iteration of code adjustment.

6. **Update Documentation & Registry**
   - Update `sketch/WORKS.md` with the new version entry.
   - Update `.agents/FEEDBACK.md` by adding the new version header (e.g., `## {work_name}_v2`) at the top.
   - **IMPORTANT**: Do not write to the `Rating` or `Comment` fields of the new entry.
   - Update `sketch/{work_name}_v{n}/README.md` with "Changes from previous version" notes.

7. **Commit**
   - Commit message: `polish: {work_name}_v{n} — {specific_improvement}`.

8. **Upload**
   - `uv run python scripts/upload_to_drive.py {work_name}_v{n}` (see `.agents/skills/shared/drive-upload.md`).

## Selection Priority

1. **Critical**: Rating = NG with Comment (clear rejection needing fix).
2. **High**: Rating blank with Comment (not yet evaluated, has feedback).
3. **Medium**: Rating = OK with Comment + feature request (approved direction, expand it).
4. **Low**: Rating = OK with Comment + minor tweak (nice-to-have).

## Precision Rules

- **Palette Precision**: Use curated color palettes suited to the work's tonal family (high-key paper, mid-tone mineral, pastel atmospheric, vibrant chromatic, monochrome, or deep luminous) rather than defaulting to a single dark palette.
- **Complexity Precision**: If "more abstract" is requested, increase noise octaves or transformation depth; if "more realistic," add physical constraints or optical shading.
- **Naming Precision**: Always use `{work_name}_v{n}` for directories and entries to maintain a clear evolution path.
- **Convention Adherence**: Ensure all preview files follow the `{work_name}_v{n}_p1.png` naming convention.

## Notes

- Never overwrite an existing past work directory.
- Use `uv run python sketch/{work_name}_v{n}/main.py` for execution.
- If the user mentions "animation" for a still image work, transition to the animation template in `.agents/skills/shared/py5-templates.md` (`step_animation_frame`).
