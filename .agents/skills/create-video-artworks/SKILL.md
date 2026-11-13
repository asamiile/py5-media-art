---
name: create-video-artworks
description: "Continuously creates py5 media art animations in a loop. Each iteration follows the same workflow as create-video-artwork (plan → implement → review → commit). Runs until stopped. Triggers: create video artworks, batch video art, continuous animations"
allowed-tools: Bash, Read, Write, Edit
---

# Create Video Artworks Skill (Continuous)

Continuously creates py5 media art animations by repeating the single-artwork workflow in a loop. Each iteration produces a distinct full-bleed work with a unique concept, genre, composition archetype, motion archetype, tonal family, and technique.

## Workflow

1. Read `AGENTS.md`, `.agents/skills/shared/artwork-conventions.md`, and `.agents/skills/shared/py5-templates.md` to confirm the full workflow and shared conventions
2. Create or switch to the branch `feature/works-YYYYMMDD` (use today's date)
3. **Loop** — Repeat the following for each new work:
   1. **Diversity Prescription**: Run `uv run python scripts/check_diversity.py plan` to get the mandatory 5-axis diversity prescription (excluded recent genres, target genre, composition archetype, motion archetype, tonal family, and banned subject tokens)
   2. **Planner**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, apply the prescription from step 1, and produce a Creative Brief with **Format: Animation (15-30s @ 60fps)** (see `.agents/skills/planner/SKILL.md`)
   3. **Artist**: Implement the concept from the Creative Brief in `sketch/{work_name}/main.py` as 100% full-bleed visual art (zero `py5.text()`, zero `FIG. 01..08` flank cards or central medallions; see `.agents/skills/artist/SKILL.md`)
   4. **Programmatic Anti-Bias Check**: Run `uv run python scripts/check_diversity.py check {work_name}`. Fix any reported naming, template, text, duration, or palette bias before rendering
   5. Run the sketch to generate `output.mp4` (and `{work_name}.mp4`) and `{work_name}_p1.png`, ensuring the process fully terminates
   6. **Critic**: Run `uv run python scripts/check_diversity.py check {work_name}`, review code, video, and generated preview images, and return APPROVE or REVISE (see `.agents/skills/critic/SKILL.md`)
   7. If REVISE: artist applies feedback and re-runs (max 2 revisions; `check_diversity.py check` must PASS)
   8. Create `sketch/{work_name}/README.md` and update `sketch/WORKS.md` and `.agents/FEEDBACK.md` (leave Rating and Comment empty per conventions)
   9. Commit and push
   10. Upload outputs to Google Drive: `uv run python scripts/upload_to_drive.py {work_name}` (see `.agents/skills/shared/drive-upload.md`)
   11. Start next iteration immediately — no user confirmation

## Anti-Bias Rules for Continuous Runs

- **Never mimic legacy `kinetic_*_2d` entries in `WORKS.md`**: Do not copy the "Central Medallion + 4 Flank Cards (`FIG. 01`..`FIG. 08`)" infographic layout, museum borders, or compass bezels from older works.
- **100% Pure Visual Canvas**: Never draw `py5.text()`, HUDs, charts, swatch legends, or historical timelines on the canvas.
- **Concise Work Names**: Use 2–4 evocative `snake_case` words without `kinetic_` prefix or `_2d`/`_3d` suffix.
- **Varied Duration**: Use 15–30s (`900`–`1800` frames at 60fps); never lock to `720` frames (`12`s).
- Follow shared naming, preview, and staging rules in `.agents/skills/shared/artwork-conventions.md`
- Entry point filename is always `main.py`
- Animation is the primary output; ensure `output.mp4` is generated for each work. Never commit MP4 files; they live on Google Drive after the upload step.
- The loop continues indefinitely until externally stopped
