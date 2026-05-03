---
name: create-artworks-lite
description: "Continuously creates py5 media art sketches with the lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Repeats create-artwork-lite-style iterations until interrupted, committing and pushing each work. Triggers: create artworks lite, batch artwork lite, continuous lightweight artwork, NVIDIA proxy artworks"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artworks Lite Skill

Continuously create py5 media art sketches using the lightweight workflow from `create-artwork-lite`. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Each iteration must produce one complete, independent artwork and commit/push it before starting the next.

## Workflow

1. Read only the essential parts of `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Create or reuse branch `feature/works-YYYYMMDD`.
3. Loop until externally interrupted:
   1. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
   2. Re-read or rescan `sketch/WORKS.md` and `.agents/FEEDBACK.md` enough to avoid repetition.
   3. Produce a short inline creative brief:
      - work name
      - one-sentence theme
      - technique
      - 3-5 color palette
      - how it differs from recent works
   4. Implement `sketch/{work_name}/main.py` and `README.md`.
   5. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/preview_p1.png` exists.
   6. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
   7. If the verdict is `REVISE`, apply at most one revision and regenerate pattern-specific previews; the second review should approve unless there is a hard failure.
   8. Update both `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
   9. Stage only intended files:
      - `sketch/{work_name}/`
      - `sketch/WORKS.md`
      - `.agents/FEEDBACK.md`
   10. Commit and push.
   11. Report the completed work name, score/verdict, changed files, and commit hash.
   12. Immediately start the next iteration.

## Stop Conditions

Stop instead of continuing if any of these happen:

- unrelated pending changes are present
- a unique work name cannot be chosen confidently
- `preview_p1.png` cannot be generated
- the sketch fails after one repair attempt
- commit or push fails after one repair attempt
- the user interrupts the run

## Lightweight Rules

- Do not invoke separate Planner, Artist, or Critic agents.
- Do not use the full `create-artworks` workflow.
- Do not carry creative state between works except by reading updated `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
- Do not perform more than one revision per work.
- Do not read every historical work in detail; scan enough of `sketch/WORKS.md` and `.agents/FEEDBACK.md` to avoid obvious repetition.
- Prefer a still image over MP4 unless the concept clearly requires motion.
- Follow `.agents/skills/shared/artwork-conventions.md` for work names, preview names, and staging.
- Prefer existing helpers in `lib/`:
  - `lib.paths.sketch_dir`
  - `lib.sizes.get_sizes`
  - `lib.preview.exit_after_preview_py5`
  - `lib.preview.maybe_save_exit_on_frame`
  - `lib.preview.save_preview_pil`
  - `lib.animation` only for animation output
- Never delete unrelated files or stage unrelated pending changes.

## Minimum Quality Bar Per Work

- The work must be visually intentional, not a default demo.
- The concept, technique, and palette must differ from recent works.
- `preview_p1.png` must be generated before review and commit.
- `.agents/FEEDBACK.md` must receive at least one concise note for the new work.
- If critique tooling or visual inspection is unavailable, use a fallback self-critique in the critic format and explicitly output `APPROVE` or `REVISE`.
- The final report for each iteration must include an explicit `APPROVE` or `REVISE` verdict.

## Recommended Templates

Use `.agents/skills/shared/py5-templates.md`.

## Rate Limit Rules

- After each committed/pushed artwork, wait 60-90 seconds before starting the next iteration.
- If `Provider API request failed` or an upstream API error occurs, wait 90-180 seconds and retry once.
- If the retry fails, stop and report the last completed commit and current git status.
- Keep progress reports concise to reduce extra provider calls.
