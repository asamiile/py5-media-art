# Canonical Artwork Creation Pipeline

All `create-artwork*` and `create-video-artwork*` skills follow this unified pipeline. Each skill specifies its **Mode Parameters** (Format, Execution Mode, and Agent Depth) and delegates the core execution steps to this document.

## Mode Matrix

| Skill | Format | Loop Mode | Depth |
| --- | --- | --- | --- |
| `create-artwork` | Still image (`{work_name}.png`) | Single | Standard (Planner → Artist → Critic, max 2 revisions) |
| `create-artworks` | Still image (`{work_name}.png`) | Continuous loop | Standard (Planner → Artist → Critic, max 2 revisions) |
| `create-video-artwork` | Animation (`15–30s @ 60fps`, `{work_name}.mp4` + `{work_name}.png`) | Single | Standard (Planner → Artist → Critic, max 2 revisions) |
| `create-video-artworks` | Animation (`15–30s @ 60fps`, `{work_name}.mp4` + `{work_name}.png`) | Continuous loop | Standard (Planner → Artist → Critic, max 2 revisions) |
| `create-artwork-lite` | Still image (`{work_name}.png`) | Single | Lite (Inline brief + 1 concise self-critique, max 1 revision) |
| `create-artworks-lite` | Still image (`{work_name}.png`) | Continuous loop (+ 60–90s rate-limit pause) | Lite (Inline brief + 1 concise self-critique, max 1 revision) |
| `create-video-artwork-lite` | Animation (`15–30s @ 60fps`, `{work_name}.mp4` + `{work_name}.png`) | Single | Lite (Inline brief + 1 concise self-critique, max 1 revision) |
| `create-video-artworks-lite` | Animation (`15–30s @ 60fps`, `{work_name}.mp4` + `{work_name}.png`) | Continuous loop (+ 60–90s rate-limit pause) | Lite (Inline brief + 1 concise self-critique, max 1 revision) |

---

## Pre-Flight Setup (Once per invocation)

1. **Read Shared Conventions**:
   - `AGENTS.md`
   - `.agents/skills/shared/artwork-conventions.md`
   - `.agents/skills/shared/py5-templates.md`
   - `.agents/skills/shared/safety-and-aesthetics.md`
2. **Branch Setup**:
   - Check `git status --short`. If unrelated dirty changes make committing unsafe, stop and report.
   - Create or switch to branch `feature/works-YYYYMMDD` (using today's date). Never commit or push directly to `main`.

---

## Per-Work Iteration Pipeline

Repeat the following steps once (for `Single` skills) or indefinitely until externally interrupted (for `Continuous loop` skills):

### 1. Programmatic Diversity Prescription
Run the diversity analyzer before planning:
```bash
uv run python scripts/check_diversity.py plan
```
Use the output to select:
- **Genre** (rotating across the 8 genre buckets; never repeating the last 3 works)
- **Composition Archetype** (rotating across the 8 spatial layouts)
- **Motion Archetype** (rotating across the 7 temporal curves; for animations, vary duration between `900` and `1800` frames at 60fps — never lock to `720` frames)
- **Tonal / Palette Family** (rotating across the 6 full-canvas tonal families)
- **Banned Subject Tokens** (zero token overlap with the last 10 works)

### 2. Concept Planning
- **Standard Depth**: Follow `.agents/skills/planner/SKILL.md`. Read `sketch/WORKS.md` and `.agents/FEEDBACK.md`, optionally query the `logic-lab` MCP server for specific algorithms, and output a full Creative Brief matching the target **Format**.
- **Lite Depth**: Read `sketch/WORKS.md` and `.agents/FEEDBACK.md` and write a concise inline Creative Brief (work name in 2–4 `snake_case` words, genre/composition/motion archetype, one-sentence visual theme, technique, 3–5 color palette, and differentiation from recent works).

### 3. Implementation
- Implement `sketch/{work_name}/main.py` following `.agents/skills/artist/SKILL.md` and `.agents/skills/shared/py5-templates.md`.
- **100% Pure Visual Canvas**: Zero `py5.text()`, zero `FIG. 01..08` telemetry flank cards, zero central medallions or museum borders, and zero signatures/hanko (落款・印章).
- Use `lib.preview` (`preview_filename`, `maybe_save_exit_on_frame`) for still works or `lib.animation` (`step_animation_frame`) for animations.

### 4. Programmatic Anti-Bias Check (Pre-Render)
Verify that the code and work name pass all anti-clustering rules before spending render time:
```bash
uv run python scripts/check_diversity.py check {work_name}
```
Fix any `[FAIL]` items immediately.

### 5. Render & Preview Generation
Run the sketch and ensure the process terminates cleanly:
```bash
uv run python sketch/{work_name}/main.py
```
- **Still works**: Verify `sketch/{work_name}/{work_name}.png` (and any `_p2.png`, etc.) exists and is non-blank.
- **Animation works**: Verify `sketch/{work_name}/{work_name}.mp4` and `sketch/{work_name}/{work_name}.png` exist and `frames/` is cleaned up.

### 6. Critique & Revision
- **Standard Depth**: Follow `.agents/skills/critic/SKILL.md`. Run `uv run python scripts/check_diversity.py check {work_name}`, inspect the generated preview image (`{work_name}.png`) and code, score all 5 axes, and return `APPROVE` or `REVISE` (up to 2 revisions).
- **Lite Depth**: Perform one concise self-critique using the 5 axes in `.agents/skills/critic/SKILL.md` (up to 1 revision if needed).

### 7. Documentation & Registry Update
- Create `sketch/{work_name}/README.md` using `.agents/skills/shared/readme-template.md`.
- Prepend the work's metadata entry to `sketch/WORKS.md`.
- Prepend a blank feedback section to `.agents/FEEDBACK.md` (leave `Rating` and `Comment` empty).

### 8. Commit, Push & Upload
- Stage only the allowed files (`git add sketch/{work_name}/main.py sketch/{work_name}/README.md sketch/{work_name}/{work_name}*.png sketch/WORKS.md .agents/FEEDBACK.md`). Never stage `.mp4` files or `frames/`.
- Commit (`feat: add {work_name} sketch`) and push to the `feature/works-YYYYMMDD` branch.
- Upload outputs to Google Drive (stills copied, videos moved):
  ```bash
  uv run python scripts/upload_to_drive.py {work_name}
  ```

### 9. Loop Continuation (Continuous Mode Only)
- **Standard Continuous (`create-artworks`, `create-video-artworks`)**: Immediately start Step 1 for the next work without waiting for user confirmation.
- **Lite Continuous (`create-artworks-lite`, `create-video-artworks-lite`)**: Wait 60–90 seconds for proxy rate limits, then start Step 1 for the next work.
