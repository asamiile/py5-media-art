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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

sim_w = 480
sim_h = 270

A = np.ones((sim_h, sim_w), dtype=np.float32)
B = np.zeros((sim_h, sim_w), dtype=np.float32)

D_A = 1.0
D_B = 0.5
f = 0.055
k = 0.062
dt = 1.0

img = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A, B, img
    
    for _ in range(20):
        cx = np.random.randint(0, sim_w)
        cy = np.random.randint(0, sim_h)
        r = np.random.randint(5, 15)
        
        y, x = np.ogrid[-cy:sim_h-cy, -cx:sim_w-cx]
        mask = x*x + y*y <= r*r
        B[mask] = 1.0
        
    img = py5.create_image(sim_w, sim_h, py5.RGB)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global A, B, img
    
    for _ in range(8):
        lap_A = (
            np.roll(A, 1, axis=0) + np.roll(A, -1, axis=0) +
            np.roll(A, 1, axis=1) + np.roll(A, -1, axis=1) -
            4 * A
        )
        
        lap_B = (
            np.roll(B, 1, axis=0) + np.roll(B, -1, axis=0) +
            np.roll(B, 1, axis=1) + np.roll(B, -1, axis=1) -
            4 * B
        )
        
        reaction = A * B * B
        
        t = py5.frame_count * 0.005
        cur_f = f + np.sin(t) * 0.01
        cur_k = k + np.cos(t * 0.5) * 0.005
        
        A += (D_A * lap_A - reaction + cur_f * (1 - A)) * dt
        B += (D_B * lap_B + reaction - (cur_k + cur_f) * B) * dt

        A = np.clip(A, 0, 1)
        B = np.clip(B, 0, 1)

    t = py5.frame_count * 0.01
    
    B_mapped = B ** 0.5 
    
    img.load_np_pixels()
    
    val = np.clip(B_mapped * 255, 0, 255).astype(np.uint8)
    
    r_tint = (np.sin(t) * 0.5 + 0.5)
    g_tint = (np.sin(t + 2) * 0.5 + 0.5)
    b_tint = (np.sin(t + 4) * 0.5 + 0.5)
    
    img.np_pixels[:, :, 0] = val * r_tint 
    img.np_pixels[:, :, 1] = val * g_tint 
    img.np_pixels[:, :, 2] = val * b_tint 
    img.np_pixels[:, :, 3] = 255 
    
    img.update_np_pixels()
    
    py5.background(0)
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

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

py5.run_sketch()
