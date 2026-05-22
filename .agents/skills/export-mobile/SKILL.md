---
name: export-mobile
description: "Re-encodes an existing py5 artwork's MP4 to mobile-optimized format: H.264/10–20s seamless loop, two orientations (landscape 1280×720 and portrait 720×1280). Takes a work name as argument. Triggers: export mobile, mobile export, mobile video, re-encode for mobile"
allowed-tools: Bash, Read, Write, Edit
---

# Export Mobile Skill

Re-encode an existing artwork's video as mobile-optimized MP4s — one landscape and one portrait.  
No new sketch is created — only the existing rendered video is transcoded.

## Output Spec

| Item        | Landscape                               | Portrait                                |
|-------------|------------------------------------------|------------------------------------------|
| Container   | MP4                                      | MP4                                      |
| Codec       | H.264 (`libx264`, baseline, level 3.1)  | H.264 (`libx264`, baseline, level 3.1)  |
| Resolution  | 1280×720                                 | 720×1280                                 |
| Duration    | 10–20 seconds (see duration rules below) | 10–20 seconds (same TARGET_SEC)          |
| Loop        | Seamless — uses `-stream_loop -1` + `-t` | Seamless — uses `-stream_loop -1` + `-t` |
| Fast-start  | `-movflags +faststart`                   | `-movflags +faststart`                   |
| Quality     | `-crf 23`                                | `-crf 23`                                |
| Scaling     | Fill + center-crop (no black bars)       | Fill + center-crop (no black bars)       |
| Output file | `{work_name}_landscape.mp4`              | `{work_name}_portrait.mp4`               |

## Inputs

- **Work name**: passed as the argument to the command (e.g. `lbm_karman_vortex_street`)
- **Source file**: `sketch/{work_name}/{work_name}.mp4`

## Workflow

1. Receive the work name from the command argument.
2. Verify `sketch/{work_name}/` exists. If not, stop and report the error.
3. Find the source MP4. Try in this order:
   a. `sketch/{work_name}/{work_name}.mp4`
   b. Any single `*.mp4` file in `sketch/{work_name}/` that does not end with `_landscape.mp4` or `_portrait.mp4`
   If no source found, stop and report.
4. Get the source duration:
   ```bash
   ffprobe -v quiet -show_entries format=duration -of csv=p=0 sketch/{work_name}/{work_name}.mp4
   ```
5. Determine `TARGET_SEC` using these rules (applies to both outputs):
   - Source is 10–20 s → use source duration as-is (no loop, no trim)
   - Source < 10 s → `TARGET_SEC = 15` (loop to fill)
   - Source > 20 s → `TARGET_SEC = 15` (trim to a centered segment)
6. Run FFmpeg for **landscape** (1280×720):
   ```bash
   ffmpeg -y -stream_loop -1 \
     -i sketch/{work_name}/{work_name}.mp4 \
     -t {TARGET_SEC} \
     -vcodec libx264 \
     -profile:v baseline -level 3.1 \
     -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720" \
     -pix_fmt yuv420p \
     -movflags +faststart \
     -crf 23 \
     sketch/{work_name}/{work_name}_landscape.mp4
   ```
7. Run FFmpeg for **portrait** (720×1280):
   ```bash
   ffmpeg -y -stream_loop -1 \
     -i sketch/{work_name}/{work_name}.mp4 \
     -t {TARGET_SEC} \
     -vcodec libx264 \
     -profile:v baseline -level 3.1 \
     -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" \
     -pix_fmt yuv420p \
     -movflags +faststart \
     -crf 23 \
     sketch/{work_name}/{work_name}_portrait.mp4
   ```
   `-stream_loop -1` with `-t` handles both looping (short source) and trimming (long source).  
   `force_original_aspect_ratio=increase` + `crop` fills the entire target frame from the center,
   avoiding the small-video-with-black-bars problem that occurs with `decrease` + `pad`.
8. Verify both output files were created successfully.
9. Report: work name, source duration, target duration, and for each output — path and file size.

## Notes

- Output filenames follow the pattern `{work_name}_{orientation}.mp4` (`landscape` or `portrait`).
- Never overwrite the original source file.
- Do **not** modify `main.py`, `WORKS.md`, or `FEEDBACK.md`.
- Do **not** commit unless explicitly requested.
- If the source video does not exist at all (artwork never rendered), report clearly:
  `"Source MP4 not found. Run the sketch first to generate {work_name}.mp4."`
