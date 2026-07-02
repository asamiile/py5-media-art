from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

blocks = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Generate brutalist blocks
    grid_size = 15
    spacing = 80
    offset = (grid_size * spacing) / 2
    
    for x in range(grid_size):
        for z in range(grid_size):
            # Skip some blocks to create gaps
            if py5.random() < 0.3:
                continue
            
            px = x * spacing - offset
            pz = z * spacing - offset
            
            # Base height
            base_h = py5.random(100, 600)
            
            # Sub-blocks to make it look architectural
            num_sub = py5.random_int(1, 4)
            for _ in range(num_sub):
                pw = py5.random(40, 150)
                pd = py5.random(40, 150)
                ph = py5.random(50, base_h)
                py = -ph / 2  # Grow upwards from 0
                
                # Shift slightly off grid
                sx = px + py5.random(-20, 20)
                sz = pz + py5.random(-20, 20)
                
                # Colors: Mostly concrete, rare safety orange
                if py5.random() > 0.95:
                    c = py5.color(20, 90, 90) # Orange
                elif py5.random() > 0.8:
                    c = py5.color(220, 10, py5.random(40, 60)) # Cool concrete
                else:
                    c = py5.color(30, 10, py5.random(50, 80)) # Warm concrete
                    
                blocks.append({
                    "x": sx, "y": py, "z": sz,
                    "w": pw, "h": ph, "d": pd,
                    "c": c,
                    "phase": py5.random(py5.TWO_PI),
                    "speed": py5.random(0.01, 0.03)
                })

def draw():
    py5.background(220, 5, 15) # Very dark cool grey sky
    
    # Lighting
    py5.ambient_light(0, 0, 30)
    py5.directional_light(0, 0, 100, 0.5, 1, -1) # Main sun
    py5.directional_light(200, 20, 50, -1, 0.5, -0.5) # Soft blue fill
    
    # Camera motion
    t = py5.frame_count / float(TOTAL_FRAMES)
    cam_angle = t * py5.TWO_PI * 0.5 # Half rotation over sequence
    cam_radius = 1800
    cx = py5.cos(cam_angle) * cam_radius
    cz = py5.sin(cam_angle) * cam_radius
    cy = -800 + py5.sin(t * py5.TWO_PI) * 200
    
    py5.camera(cx, cy, cz, 0, -200, 0, 0, 1, 0)
    
    # Draw blocks
    for b in blocks:
        py5.push_matrix()
        
        # Animate Y position slowly
        y_offset = py5.sin(b["phase"] + py5.frame_count * b["speed"]) * 100
        py5.translate(b["x"], b["y"] + y_offset, b["z"])
        
        py5.fill(b["c"])
        py5.no_stroke()
        py5.box(b["w"], b["h"], b["d"])
        
        # Edge lines
        py5.stroke(0, 0, 10, 50)
        py5.stroke_weight(2)
        py5.no_fill()
        py5.box(b["w"], b["h"], b["d"])
        
        py5.pop_matrix()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
