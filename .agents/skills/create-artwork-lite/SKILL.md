---
name: create-artwork-lite
description: "Creates exactly one py5 media art sketch with a lightweight workflow for slow Claude Code proxy routes such as NVIDIA API. Minimizes planning/review overhead while still generating preview images, updating records, committing, and pushing. Triggers: create artwork lite, lightweight artwork, NVIDIA proxy artwork"
allowed-tools: Bash, Read, Write, Edit
---

# Create Artwork Lite Skill

Create exactly one new py5 media art sketch using a reduced-overhead version of the normal `create-artwork` workflow. This is intended for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Use this skill when execution speed and fewer model/tool round trips matter more than a full Planner -> Artist -> Critic separation.

## Workflow

1. Read only the essential parts of `CLAUDE.md`, `.agents/skills/shared/artwork-conventions.md`, `.agents/skills/shared/py5-templates.md`, `sketch/WORKS.md`, and `.agents/FEEDBACK.md`.
2. Check `git status --short`. Stop if unrelated pending changes would make a clean commit unsafe.
3. Create or reuse branch `feature/works-YYYYMMDD`.
4. Produce a short inline creative brief:
   - work name
   - one-sentence theme
   - technique
   - 3-5 color palette
   - how it differs from recent works
5. Implement `sketch/{work_name}/main.py` and `README.md`.
6. Run `uv run python sketch/{work_name}/main.py` and ensure `sketch/{work_name}/preview_p1.png` exists.
7. Perform one concise self-critique in the same format as `.agents/skills/critic/SKILL.md`.
8. If the verdict is `REVISE`, apply at most one revision and regenerate pattern-specific previews; the second review should approve unless there is a hard failure.
9. Update both `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
10. Stage only intended files:
    - `sketch/{work_name}/`
    - `sketch/WORKS.md`
    - `.agents/FEEDBACK.md`
11. Commit and push.
12. Report work name, score/verdict, changed files, and commit hash.

## Lightweight Rules

- Do not invoke separate Planner, Artist, or Critic agents.
- Do not run an indefinite loop.
- Do not perform more than one revision.
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

## Minimum Quality Bar

- The work must be visually intentional, not a default demo.
- The concept, technique, and palette must differ from recent works.
- `preview_p1.png` must be generated before review and commit.
- `.agents/FEEDBACK.md` must receive at least one concise note for the new work.
- If critique tooling or visual inspection is unavailable, use a fallback self-critique in the critic format and explicitly output `APPROVE` or `REVISE`.

## Recommended Templates

Use `.agents/skills/shared/py5-templates.md`.
