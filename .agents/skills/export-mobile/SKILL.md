---
name: export-mobile
description: "Re-encodes an existing py5 artwork's MP4 to mobile-optimized format: H.264/720p/10–20s seamless loop. Takes a work name as argument. Triggers: export mobile, mobile export, mobile video, re-encode for mobile"
allowed-tools: Bash, Read, Write, Edit
---

# Export Mobile Skill

Re-encode an existing artwork's video as a mobile-optimized MP4.  
No new sketch is created — only the existing rendered video is transcoded.

## Output Spec

| Item       | Value                                    |
|------------|------------------------------------------|
| Container  | MP4                                      |
| Codec      | H.264 (`libx264`, baseline, level 3.1)  |
| Resolution | 1280×720 (720p), aspect preserved        |
| Duration   | 10–20 seconds (see duration rules below) |
| Loop       | Seamless — uses `-stream_loop -1` + `-t` |
| Fast-start | `-movflags +faststart`                   |
| Quality    | `-crf 23`                                |

## Inputs

- **Work name**: passed as the argument to the command (e.g. `lbm_karman_vortex_street`)
- **Source file**: `sketch/{work_name}/{work_name}.mp4`

## Workflow

1. Receive the work name from the command argument.
2. Verify `sketch/{work_name}/` exists. If not, stop and report the error.
3. Find the source MP4. Try in this order:
   a. `sketch/{work_name}/{work_name}.mp4`
   b. Any single `*.mp4` file in `sketch/{work_name}/` that does not end with `_mobile.mp4`
   If no source found, stop and report.
4. Get the source duration:
   ```bash
   ffprobe -v quiet -show_entries format=duration -of csv=p=0 sketch/{work_name}/{work_name}.mp4
   ```
5. Determine `TARGET_SEC` using these rules:
   - Source is 10–20 s → use source duration as-is (no loop, no trim)
   - Source < 10 s → `TARGET_SEC = 15` (loop to fill)
   - Source > 20 s → `TARGET_SEC = 15` (trim to a centered segment)
6. Run FFmpeg:
   ```bash
   ffmpeg -y -stream_loop -1 \
     -i sketch/{work_name}/{work_name}.mp4 \
     -t {TARGET_SEC} \
     -vcodec libx264 \
     -profile:v baseline -level 3.1 \
     -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
     -pix_fmt yuv420p \
     -movflags +faststart \
     -crf 23 \
     sketch/{work_name}/{work_name}_mobile.mp4
   ```
   `-stream_loop -1` with `-t` handles both looping (short source) and trimming (long source).
7. Verify `sketch/{work_name}/{work_name}_mobile.mp4` was created successfully.
8. Report: work name, source duration, target duration, output path, file size.

## Notes

- Output filename is always `{work_name}_mobile.mp4` — never overwrite the original.
- Do **not** modify `main.py`, `WORKS.md`, or `FEEDBACK.md`.
- Do **not** commit unless explicitly requested.
- If the source video does not exist at all (artwork never rendered), report clearly:
  `"Source MP4 not found. Run the sketch first to generate {work_name}.mp4."`
