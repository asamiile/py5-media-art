"""
Common helper utilities for py5 media art sketches.

Modules:
- ``lib.paths``: repository and sketch directory resolution
- ``lib.sizes``: 4K output and preview resolution constants
- ``lib.preview``: preview image saving, blank-frame fail-safe, and clean JVM exit
- ``lib.animation``: frame sequence capture, FFmpeg MP4 compilation, and cleanup
- ``lib.shaders``: optional GLSL shader loader, fullscreen pass, and PostFX pipeline
- ``lib.diversity``: 5-axis portfolio diversity prescription and anti-bias static checker
- ``lib.drive_upload``: rclone Google Drive upload and fetch helpers
- ``lib.safety``: temporal anti-flicker blending filter
"""
