from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Mandala config
SYMMETRY = 12
ANGLE_STEP = (py5.PI * 2) / SYMMETRY


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    # Motion blur / fading
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Rotate the entire mandala slowly
    py5.rotate(t * 0.2)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(SYMMETRY):
        py5.push_matrix()
        py5.rotate(i * ANGLE_STEP)
        
        # Draw the main wedge
        draw_wedge(t, i)
        
        # Mirror for the next half of the symmetry segment
        py5.scale(1, -1)
        draw_wedge(t, i)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

def draw_wedge(t, segment_index):
    # Generates a sequence of overlapping shapes within the wedge
    for r_idx in range(5):
        r_base = 100 + r_idx * 150
        num_points = 6
        
        py5.begin_shape()
        for p in range(num_points):
            angle = (p / (num_points - 1)) * (ANGLE_STEP / 2)
            
            # Use 3D perlin noise mapped to a polar coordinate
            n_x = math.cos(angle) * r_base * 0.005
            n_y = math.sin(angle) * r_base * 0.005
            noise_val = py5.os_noise(n_x, n_y, t + r_idx * 1.5)
            
            r = r_base + (noise_val - 0.5) * 200
            
            x = math.cos(angle) * r
            y = math.sin(angle) * r
            
            # Dynamic colors
            hue_offset = noise_val * 3.0
            r_col = 50 + math.sin(hue_offset) * 100
            g_col = 100 + math.sin(hue_offset + 2) * 155
            b_col = 150 + math.sin(hue_offset + 4) * 105
            
            py5.stroke(r_col, g_col, b_col, 150)
            py5.vertex(x, y)
        py5.end_shape()

py5.run_sketch()
