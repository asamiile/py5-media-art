# Artwork Conventions

Shared naming, file, and staging rules for py5 media art skills.

## Work Names

- Use concise, evocative 2–4 word `snake_case` names for new concepts (e.g., `vermilion_basalt_faults`, `sashiko_indigo_drift`, `mist_catenary_veil`).
- **Forbidden affixes**: Never prefix names with `kinetic_` and never suffix names with `_2d` or `_3d`. Avoid long 6–8 word academic/scientific jargon chains.
- Do not add `_v1` to first versions.
- If intentionally remaking or replacing the idea of a past work, create a new directory with the next suffix: `{base_work_name}_v2`, `{base_work_name}_v3`, etc.
- Never overwrite an existing past work directory.

## Pure Visual Canvas (Zero Text / Zero Infographic Panels)

- Every sketch must be **100% pure visual media art** across the entire 3840×2160 frame.
- **Strictly forbidden on canvas**: `py5.text()`, title headers, footer captions, `FIG. 01..08` flank cards, telemetry dashboards, color swatch legends, historical timeline tables, oscillogram boxes, museum borders, and central circular compass/goniometer bezels.

## Preview Images

- Use `{work_name}.png` for the default preview image (do not append `_p1` or `_v1`).
- Only if a work deliberately includes multiple distinct patterns or variants, save the additional ones as `{work_name}_p2.png`, `{work_name}_p3.png`, etc.
- Do not create or commit an unsuffixed `preview.png` for new works.
- `{work_name}.png` must exist before review and commit.

## Work Directory

```text
sketch/
  {work_name}/
    main.py
    *.glsl                   # optional shaders (see shaders.md)
    README.md
    {work_name}.png
    {work_name}_p2.png       # optional additional pattern
    {work_name}.mp4          # animation only; moved to Google Drive after commit
    frames/                  # sequential PNGs, not committed
```

## Staging

Stage only intended files:

- `sketch/{work_name}/`
- `sketch/WORKS.md`
- `.agents/FEEDBACK.md`

Do not stage unrelated pending changes.

## Google Drive Upload

After commit and push, send the work's outputs to Google Drive (stills copied, videos moved) — see `.agents/skills/shared/drive-upload.md`.

## FEEDBACK.md Protocol

- **Agents MUST NOT** write anything in the `Rating` or `Comment` fields of `.agents/FEEDBACK.md`.
- These fields are reserved EXCLUSIVELY for the USER to provide feedback and critique.
- When registering a new work, the Agent should only create the header and empty fields:
  ```markdown
  ## {work_name}

  - **Rating**: 
  - **Comment**: 
  ```
