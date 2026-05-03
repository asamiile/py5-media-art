# Artwork Conventions

Shared naming, file, and staging rules for py5 media art skills.

## Work Names

- Use plain snake_case for new concepts, e.g. `flowing_particles`.
- Do not add `_v1` to first versions.
- If intentionally remaking or replacing the idea of a past work, create a new directory with the next suffix: `{base_work_name}_v2`, `{base_work_name}_v3`, etc.
- Never overwrite an existing past work directory.

## Preview Images

- Use `preview_p1.png` for the first generated pattern.
- If the work deliberately includes multiple distinct patterns or variants, save them as `preview_p2.png`, `preview_p3.png`, etc.
- Keep the pattern suffix before the revision suffix for snapshots: `preview_p1_v1.png`, `preview_p2_v1.png`, etc.
- Do not create or commit an unsuffixed `preview.png` for new works.
- `preview_p1.png` must exist before review and commit.

## Work Directory

```text
sketch/
  {work_name}/
    main.py
    README.md
    preview_p1.png
    preview_p2.png       # optional additional pattern
    preview_p1_v1.png    # optional revision snapshot
    output.mp4           # animation only
    frames/              # sequential PNGs, not committed
```

## Staging

Stage only intended files:

- `sketch/{work_name}/`
- `sketch/WORKS.md`
- `.agents/FEEDBACK.md`

Do not stage unrelated pending changes.
