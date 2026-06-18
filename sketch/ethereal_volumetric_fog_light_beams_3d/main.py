from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    time_t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_y(time_t * 0.2)
    py5.rotate_x(time_t * 0.1)
    
    num_particles = 2000
    
    orb1_x = np.sin(time_t * 0.8) * 400
    orb1_y = np.cos(time_t * 1.2) * 300
    orb1_z = np.sin(time_t * 0.5) * 500
    
    orb2_x = np.sin(time_t * 0.5 + py5.PI) * 500
    orb2_y = np.cos(time_t * 0.9 + py5.PI) * 400
    orb2_z = np.cos(time_t * 0.7) * 400
    
    # Draw central orbs
    py5.no_stroke()
    
    # Fake glow for orb 1
    for i in range(10, 0, -1):
        py5.push_matrix()
        py5.translate(orb1_x, orb1_y, orb1_z)
        py5.fill(200, 80, 100, 10)
        py5.circle(0, 0, i * 20)
        py5.pop_matrix()
        
    py5.push_matrix()
    py5.translate(orb1_x, orb1_y, orb1_z)
    py5.fill(200, 10, 100, 255)
    py5.circle(0, 0, 40)
    py5.pop_matrix()
    
    # Fake glow for orb 2
    for i in range(10, 0, -1):
        py5.push_matrix()
        py5.translate(orb2_x, orb2_y, orb2_z)
        py5.fill(320, 80, 100, 10)
        py5.circle(0, 0, i * 20)
        py5.pop_matrix()
        
    py5.push_matrix()
    py5.translate(orb2_x, orb2_y, orb2_z)
    py5.fill(320, 10, 100, 255)
    py5.circle(0, 0, 40)
    py5.pop_matrix()
    
    # Draw dust particles that catch the light
    random.seed(42) # Consistent positions for particles
    py5.stroke_weight(4)
    
    py5.begin_shape(py5.POINTS)
    for _ in range(num_particles):
        px = random.uniform(-800, 800)
        py5.noise_seed(int(px * 100)) # Just to vary
        py = random.uniform(-800, 800)
        pz = random.uniform(-800, 800)
        
        # Add some wiggle
        px += py5.noise(px * 0.01, time_t) * 100 - 50
        py += py5.noise(py * 0.01, time_t) * 100 - 50
        pz += py5.noise(pz * 0.01, time_t) * 100 - 50
        
        dist1 = np.sqrt((orb1_x - px)**2 + (orb1_y - py)**2 + (orb1_z - pz)**2)
        dist2 = np.sqrt((orb2_x - px)**2 + (orb2_y - py)**2 + (orb2_z - pz)**2)
        
        inf1 = max(0, 400 - dist1) / 400
        inf2 = max(0, 400 - dist2) / 400
        
        r, g, b = 0, 0, 0
        if inf1 > 0:
            py5.stroke(200, 80, 100, inf1 * 255)
            py5.vertex(px, py, pz)
        if inf2 > 0:
            py5.stroke(320, 80, 100, inf2 * 255)
            py5.vertex(px, py, pz)
            
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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
