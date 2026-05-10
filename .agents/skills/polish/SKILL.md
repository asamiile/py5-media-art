---
name: polish
description: "Autonomously polish and refine existing artwork based on user feedback. Includes feedback analytics to identify trends and a critique loop to ensure high-precision refinements."
allowed-tools: Bash, Read, Write, Edit
---

# Polish Artwork Skill

Autonomously polishes an existing py5 media art sketch by analyzing feedback trends, selecting an improvement target, and implementing an enhanced version with high precision.

## Workflow

1. **Perform Feedback Analytics**
   - Run the analytics script to identify trends: `python3 .agents/skills/polish/scripts/analyze_feedback.py`
   - **Identify Patterns**: Use the script's output to identify keywords in positive and negative feedback (e.g., "likes dark backgrounds," "prefers high particle density," "wants more abstraction").
   - **Trend Analysis**: Check if the user's taste is shifting (e.g., recent works with "OK" ratings might have common traits that were absent in older works).
   - Create a internal summary of "User Preference Constraints" to guide the next polish.

2. **Select Polish Target**
   - Parse all work entries and calculate priority (see **Selection Priority**).
   - Choose the highest-priority work.
   - Cross-reference with `sketch/WORKS.md` to ensure the core technique is understood.

3. **Generate Precise Refinement Plan**
   - Analyze the specific Comment for the selected target.
   - **Contextualize**: Combine the specific request with the **Feedback Analytics** results.
     - *Example*: If user says "other colors" and Analytics show they like "Obsidian/Gold," lean towards that direction.
   - **Define Directives**: Create 3-5 specific code-level changes (e.g., "Change background alpha from 20 to 5," "Add a third harmonic oscillator with frequency 0.5").
   - Save the plan as a temporary internal artifact.

4. **Implement Enhancement (New Version)**
   - Follow `.agents/skills/shared/artwork-conventions.md` strictly.
   - **Create New Directory**: Copy the existing `sketch/{work_name}` to `sketch/{work_name}_v{n+1}`.
   - **Refine Code**: Modify `main.py` in the NEW directory according to the directives.
   - **Maintain Identity**: Do not change the core algorithm or theme; only refine parameters, colors, or complexity.

5. **Preview & Self-Critique**
   - Run the new sketch to generate the preview.
   - **Self-Critique Loop**: Evaluate the result against the **Refinement Plan** and **Critic axes** (Visual Impact, Technical Execution).
   - If the result doesn't fully address the feedback or violates the "User Preference Profile," perform one iteration of code adjustment.

6. **Update Documentation & Registry**
   - Update `sketch/WORKS.md` with the new version entry.
   - Update `.agents/FEEDBACK.md` by adding the new version header (e.g., `## {work_name}_v2`) at the top.
   - **IMPORTANT**: Do not write to the `Rating` or `Comment` fields of the new entry.
   - Update the `README.md` in the new directory with "Changes from previous version" notes.

7. **Commit**
   - Commit message: `polish: {work_name}_v{n} — {specific_improvement}`.

## Selection Priority

1. **Critical**: Rating = NG with Comment (clear rejection needing fix).
2. **High**: Rating blank with Comment (not yet evaluated, has feedback).
3. **Medium**: Rating = OK with Comment + feature request (approved direction, expand it).
4. **Low**: Rating = OK with Comment + minor tweak (nice-to-have).

## Precision Rules

- **Palette Precision**: Use curated color palettes (e.g., from professional color systems or nature-inspired) rather than random RGB values.
- **Complexity Precision**: If "more abstract" is requested, increase noise octaves or transformation depth; if "more realistic," add constraints or physical constants.
- **Naming Precision**: Always use the `{work_name}_v{n}` naming for directories and entries to maintain a clear evolution path.
- **Convention Adherence**: Ensure all preview files follow the `{work_name}_pN.png` suffix rules.

## Notes

- Never overwrite an existing past work directory.
- Use `uv run python main.py` for execution.
- If the user mentions "animation" for a still image work, transition to `continuous=True` and generate a video if the `create-video-artwork` skill is available.
