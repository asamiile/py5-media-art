from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

# Mycelium state
NUM_PARTICLES = 3000
points = None
velocities = None
lifetimes = None
colors = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 10)  # Very dark navy
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global points, velocities, lifetimes, colors
    points = np.zeros((NUM_PARTICLES, 3))
    # Random initial velocities outward from center
    theta = np.random.rand(NUM_PARTICLES) * 2 * np.pi
    phi = np.random.rand(NUM_PARTICLES) * np.pi
    r = np.random.rand(NUM_PARTICLES) * 5
    velocities = np.zeros((NUM_PARTICLES, 3))
    velocities[:, 0] = r * np.sin(phi) * np.cos(theta)
    velocities[:, 1] = r * np.sin(phi) * np.sin(theta)
    velocities[:, 2] = r * np.cos(phi)
    
    lifetimes = np.random.randint(100, 400, size=NUM_PARTICLES)
    colors = np.random.choice([190, 270, 320], size=NUM_PARTICLES) # cyan, violet, magenta

def draw():
    global points, velocities, lifetimes, colors
    
    # Semi-transparent background for trails
    py5.push_style()
    py5.no_stroke()
    py5.fill(5, 5, 10, 5)
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    # Update logic
    active_mask = lifetimes > 0
    t = py5.frame_count * 0.02
    
    # Curl noise approximation for velocity perturbation
    noise_field_x = np.array([py5.os_noise(p[0]*0.01, p[1]*0.01, t) for p in points])
    noise_field_y = np.array([py5.os_noise(p[1]*0.01, p[2]*0.01, t) for p in points])
    noise_field_z = np.array([py5.os_noise(p[2]*0.01, p[0]*0.01, t) for p in points])
    
    velocities[:, 0] += (noise_field_x - 0.5) * 0.5
    velocities[:, 1] += (noise_field_y - 0.5) * 0.5
    velocities[:, 2] += (noise_field_z - 0.5) * 0.5
    
    # Glitch effect
    is_glitch = py5.frame_count % 120 > 115
    if is_glitch:
        glitch_shift = np.random.randn(NUM_PARTICLES, 3) * 50
        points[active_mask] += glitch_shift[active_mask]
    else:
        points[active_mask] += velocities[active_mask]
        
    lifetimes -= 1
    
    # Draw points
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    for i in range(NUM_PARTICLES):
        if active_mask[i]:
            h = colors[i]
            s = 80
            b = 90
            alpha = min(50, lifetimes[i])
            if is_glitch and h == 320: # magenta flashes brighter on glitch
                b = 100
                alpha = 100
                py5.stroke_weight(4)
            else:
                py5.stroke_weight(2)
            
            py5.stroke(h, s, b, alpha)
            py5.point(points[i, 0], points[i, 1], points[i, 2])
            
    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        os._exit(0)

py5.run_sketch()
