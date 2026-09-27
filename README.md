## Media Art Works

### Generate Art Works

- Install ffmpeg (once)

```bash
brew install ffmpeg
```

- Run Sketch

```bash
uv run python sketch/test/main.py
```

- Autonomous artwork creation via Claude Code

Open this repository in Claude Code and run:

```
/create-artwork
```

If you continue with multiple iterations:

```
/create-artworks
```

### Shaders (optional)

Sketches can use GLSL shaders via `lib/shaders.py` (finishing pass: bloom, tone map, grain; GPU fragment-shader fields). Requires the `P2D`/`P3D` renderer and py5 >= 0.10.11a0. Check that shaders work on this machine:

```bash
uv run python scripts/check_shaders.py
```

### Google Drive upload

Finished outputs go to Google Drive, one folder per work: stills are copied (they stay in the repository), videos are moved (the local copy is deleted after a checksum-verified upload). The artwork skills run this automatically after commit & push.

```bash
brew install rclone
rclone config create gdrive drive scope=drive   # Log in to Google Drive in the browser
cp .env.example .env                            # then set PY5_UPLOAD_REMOTE
```

| Variable | Description |
| --- | --- |
| `PY5_UPLOAD_REMOTE` | Upload destination (e.g. `gdrive:Media/py5-media-art`). No upload if unset |
| `PY5_UPLOAD` | Set to `0` to skip uploading |

```bash
uv run python scripts/upload_to_drive.py {work_name}          # upload one work
uv run python scripts/upload_to_drive.py --all                # move every video left in sketch/
uv run python scripts/upload_to_drive.py --fetch {work_name}  # download a work's videos back
```

rclone's shared client ID is being retired in 2026. Create [your own client ID](https://rclone.org/drive/#making-your-own-client-id) and set it with `rclone config update gdrive client_id=... client_secret=...`.

### Generate Article

- Generate a Medium draft article for a sketch

```
/write-medium-article {work_name}
```

The generated Markdown file is saved to `medium/`. Paste the contents into Medium's editor to publish.

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Support

If you find this helpful, consider supporting the work:

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/asamiile)


## Author

[Asami.K](https://asami.tokyo/)


