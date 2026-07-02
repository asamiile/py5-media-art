import os
from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid Setup
TILE_SIZE = 120
COLS = int(SIZE[0] / (TILE_SIZE * 0.866) + 3)
ROWS = int(SIZE[1] / (TILE_SIZE * 1.5) + 3)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)

def draw_iso_cube(cx, cy, radius, phase):
    # Calculate isometric points
    angles = np.linspace(np.pi/6, 2*np.pi + np.pi/6, 7)
    px = cx + np.cos(angles) * radius
    py = cy + np.sin(angles) * radius

    # Oscillating shading based on phase to create the illusion of flipping
    shade1 = 15 + 240 * ((np.sin(phase) + 1) / 2)
    shade2 = 15 + 240 * ((np.sin(phase + 2*np.pi/3) + 1) / 2)
    shade3 = 15 + 240 * ((np.sin(phase + 4*np.pi/3) + 1) / 2)
    
    # Optional colors mixed into the shades
    base_color1 = np.array([200, 90, 50])  # Terracotta
    base_color2 = np.array([30, 60, 80])   # Slate Blue
    base_color3 = np.array([245, 245, 240])# Off-white

    c1 = base_color1 * ((np.sin(phase) + 1) / 2) + np.array([15,15,15]) * ((1 - np.sin(phase)) / 2)
    c2 = base_color2 * ((np.sin(phase + 2*np.pi/3) + 1) / 2) + np.array([15,15,15]) * ((1 - np.sin(phase + 2*np.pi/3)) / 2)
    c3 = base_color3 * ((np.sin(phase + 4*np.pi/3) + 1) / 2) + np.array([15,15,15]) * ((1 - np.sin(phase + 4*np.pi/3)) / 2)

    # Top face
    py5.fill(c3[0], c3[1], c3[2])
    py5.quad(cx, cy, px[4], py[4], px[5], py[5], px[0], py[0])
    
    # Left face
    py5.fill(c1[0], c1[1], c1[2])
    py5.quad(cx, cy, px[2], py[2], px[3], py[3], px[4], py[4])
    
    # Right face
    py5.fill(c2[0], c2[1], c2[2])
    py5.quad(cx, cy, px[0], py[0], px[1], py[1], px[2], py[2])

def draw():
    py5.background(245, 245, 240)
    py5.stroke(15, 15, 15)
    py5.stroke_weight(4)
    py5.stroke_join(py5.ROUND)

    t = (py5.frame_count / TOTAL_FRAMES) * 2 * np.pi
    
    # Draw isometric grid
    for row in range(-1, ROWS):
        for col in range(-1, COLS):
            cx = col * TILE_SIZE * 1.732
            cy = row * TILE_SIZE * 1.5
            
            if row % 2 != 0:
                cx += TILE_SIZE * 0.866
            
            # Distance from center for radial wave
            dist = np.sqrt((cx - py5.width/2)**2 + (cy - py5.height/2)**2)
            phase_offset = dist * 0.005 - t * 4
            
            draw_iso_cube(cx, cy, TILE_SIZE, phase_offset)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
