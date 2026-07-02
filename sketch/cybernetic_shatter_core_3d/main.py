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

NUM_DEBRIS = 400
debris = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global debris
    
    for _ in range(NUM_DEBRIS):
        # Random point on a sphere
        theta = np.random.rand() * py5.TWO_PI
        phi = np.arccos(2 * np.random.rand() - 1)
        
        x = np.sin(phi) * np.cos(theta)
        y = np.sin(phi) * np.sin(theta)
        z = np.cos(phi)
        
        normal = np.array([x, y, z])
        
        debris.append({
            "normal": normal,
            "pos": normal * 100, # Start at surface of core
            "vel": np.zeros(3),
            "size": np.random.rand() * 15 + 5,
            "rot_speed": np.random.randn(3) * 0.1,
            "rot": np.zeros(3)
        })

def draw():
    py5.background(0) # Pitch black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.05
    
    py5.light_specular(255, 255, 255)
    py5.directional_light(30, 100, 100, 0, 0, -1) # Orange light from front
    py5.directional_light(200, 100, 100, -1, 1, -1) # Blue light from side
    py5.ambient_light(20, 20, 20)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_y(t * 0.3)
    py5.rotate_x(t * 0.1)
    
    # Heartbeat pulse (happens every ~60 frames)
    # math: pulse is sharp, then decays
    pulse_t = (py5.frame_count % 60) / 60.0
    pulse = np.exp(-pulse_t * 10) # Sharp spike that decays quickly
    
    py5.blend_mode(py5.ADD)
    
    # Draw core
    py5.push_matrix()
    core_size = 150 + pulse * 50
    py5.fill(30, 100, 80 + pulse*20) # Neon orange, brightens on pulse
    py5.no_stroke()
    py5.sphere(core_size)
    py5.pop_matrix()
    
    # Update and draw debris
    py5.specular(255, 255, 255)
    py5.shininess(100)
    
    for d in debris:
        # Physics
        target_pos = d["normal"] * 100
        
        # Explosion force
        if py5.frame_count % 60 == 1:
            d["vel"] += d["normal"] * (np.random.rand() * 30 + 10)
            
        # Spring force back to core
        force = (target_pos - d["pos"]) * 0.05
        d["vel"] += force
        d["vel"] *= 0.85 # Friction/Damping
        d["pos"] += d["vel"]
        
        d["rot"] += d["rot_speed"] * np.linalg.norm(d["vel"]) * 0.1
        
        py5.push_matrix()
        py5.translate(*d["pos"])
        py5.rotate_x(d["rot"][0])
        py5.rotate_y(d["rot"][1])
        py5.rotate_z(d["rot"][2])
        
        # Speed-based color shift
        speed = np.linalg.norm(d["vel"])
        if speed > 15:
            py5.fill(0, 0, 100, 90) # Flash white when exploding fast
        else:
            py5.fill(210, 100, 100, 80) # Electric blue normally
            
        py5.box(d["size"])
        py5.pop_matrix()

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
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        os._exit(0)

py5.run_sketch()
