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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system for moss
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize 3000 moss spore particles
    for _ in range(3000):
        # Start from a central core
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)
        r = random.uniform(50, 150)
        x = r * py5.sin(phi) * py5.cos(theta)
        y = r * py5.sin(phi) * py5.sin(theta)
        z = r * py5.cos(phi)
        
        particles.append({
            'pos': [x, y, z],
            'age': 0,
            'max_age': random.randint(100, 600),
            'hue': random.uniform(0.4, 0.5) # Green to cyan range
        })

def draw():
    # We do not clear background to leave trails (moss growth)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(py5.frame_count * 0.001)

    py5.color_mode(py5.HSB, 1.0)
    py5.no_fill()

    for p in particles:
        if p['age'] < p['max_age']:
            # Calculate noise-based movement
            nx = py5.os_noise(p['pos'][0] * 0.005, p['pos'][1] * 0.005, p['pos'][2] * 0.005 + py5.frame_count * 0.002)
            ny = py5.os_noise(p['pos'][0] * 0.005 + 100, p['pos'][1] * 0.005 + 100, p['pos'][2] * 0.005 - py5.frame_count * 0.002)
            nz = py5.os_noise(p['pos'][0] * 0.005 + 200, p['pos'][1] * 0.005 + 200, p['pos'][2] * 0.005 + py5.frame_count * 0.001)
            
            # Map noise (0,1) to (-1,1) angles
            ang_x = (nx - 0.5) * py5.TWO_PI * 2.0
            ang_y = (ny - 0.5) * py5.TWO_PI * 2.0
            ang_z = (nz - 0.5) * py5.TWO_PI * 2.0
            
            # Spherical to cartesian velocity
            vx = py5.sin(ang_y) * py5.cos(ang_x) * 2.0
            vy = py5.sin(ang_y) * py5.sin(ang_x) * 2.0
            vz = py5.cos(ang_y) * 2.0
            
            # Attraction to center to form a structure
            d = py5.mag(p['pos'][0], p['pos'][1], p['pos'][2])
            if d > 400:
                vx -= p['pos'][0] * 0.005
                vy -= p['pos'][1] * 0.005
                vz -= p['pos'][2] * 0.005

            old_pos = list(p['pos'])
            p['pos'][0] += vx
            p['pos'][1] += vy
            p['pos'][2] += vz
            
            # Color
            h = p['hue'] + (nx - 0.5) * 0.1
            s = 0.8
            b = 0.15 # Low brightness, additive blending will accumulate
            
            py5.stroke(h, s, b, 0.4)
            py5.stroke_weight(2)
            
            py5.begin_shape(py5.LINES)
            py5.vertex(old_pos[0], old_pos[1], old_pos[2])
            py5.vertex(p['pos'][0], p['pos'][1], p['pos'][2])
            py5.end_shape()
            
            p['age'] += 1
            
            # Branching probability
            if p['age'] < p['max_age'] and random.random() < 0.002 and len(particles) < 15000:
                particles.append({
                    'pos': list(p['pos']),
                    'age': 0,
                    'max_age': random.randint(50, 300),
                    'hue': p['hue'] + random.uniform(-0.05, 0.05)
                })

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
