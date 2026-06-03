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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle arrays
NUM_HUNTERS = 200
NUM_TARGETS = 5

hunters_pos = np.random.rand(NUM_HUNTERS, 3) * 1000 - 500
hunters_vel = np.random.rand(NUM_HUNTERS, 3) * 10 - 5
targets_pos = np.random.rand(NUM_TARGETS, 3) * 800 - 400
targets_vel = np.random.rand(NUM_TARGETS, 3) * 2 - 1
targets_health = np.ones(NUM_TARGETS) * 100

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.sphere_detail(12)

def draw_pyramid(size):
    py5.begin_shape(py5.TRIANGLES)
    # Base
    py5.vertex(-size, -size, 0)
    py5.vertex(size, -size, 0)
    py5.vertex(size, size, 0)
    
    py5.vertex(-size, -size, 0)
    py5.vertex(size, size, 0)
    py5.vertex(-size, size, 0)
    
    # Sides
    py5.vertex(-size, -size, 0)
    py5.vertex(size, -size, 0)
    py5.vertex(0, 0, size * 2)
    
    py5.vertex(size, -size, 0)
    py5.vertex(size, size, 0)
    py5.vertex(0, 0, size * 2)
    
    py5.vertex(size, size, 0)
    py5.vertex(-size, size, 0)
    py5.vertex(0, 0, size * 2)
    
    py5.vertex(-size, size, 0)
    py5.vertex(-size, -size, 0)
    py5.vertex(0, 0, size * 2)
    py5.end_shape()

def draw():
    global hunters_pos, hunters_vel, targets_pos, targets_vel, targets_health
    
    py5.background(10, 80, 5)  # Dark space
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * py5.TWO_PI * 0.2)
    py5.rotate_x(py5.sin(t * py5.PI) * 0.2)
    
    py5.ambient_light(20, 20, 20)
    py5.directional_light(180, 100, 100, 1, 1, -1)
    py5.directional_light(340, 100, 80, -1, -1, 1)
    
    # Update targets
    for i in range(NUM_TARGETS):
        if targets_health[i] <= 0:
            targets_pos[i] = np.random.rand(3) * 800 - 400
            targets_health[i] = 100
            
        # Wander
        targets_vel[i] += (np.random.rand(3) - 0.5) * 0.5
        # Soft boundary
        targets_vel[i] -= targets_pos[i] * 0.001
        
        # Limit speed
        speed = np.linalg.norm(targets_vel[i])
        if speed > 3:
            targets_vel[i] = (targets_vel[i] / speed) * 3
            
        targets_pos[i] += targets_vel[i]
        
        # Draw target
        py5.push_matrix()
        py5.translate(*targets_pos[i])
        py5.no_stroke()
        health_ratio = targets_health[i] / 100.0
        py5.fill(340, 80, 50 + health_ratio * 50, 80)
        
        # Breathing effect
        breath = py5.sin(t * py5.TWO_PI * 5 + i) * 10
        py5.sphere(40 + breath * health_ratio)
        py5.pop_matrix()

    # Update hunters
    for i in range(NUM_HUNTERS):
        # Find closest target
        dists = np.linalg.norm(targets_pos - hunters_pos[i], axis=1)
        closest_idx = np.argmin(dists)
        closest_dist = dists[closest_idx]
        
        # Steer towards target
        steer = targets_pos[closest_idx] - hunters_pos[i]
        steer_norm = np.linalg.norm(steer)
        
        if steer_norm > 0:
            steer = (steer / steer_norm) * 0.5
        
        hunters_vel[i] += steer
        
        # Swarm avoidance
        # Simplified: random noise
        hunters_vel[i] += (np.random.rand(3) - 0.5) * 1.5
        
        # Damage target if close
        if closest_dist < 60:
            targets_health[closest_idx] -= 0.5
            
        # Limit speed
        speed = np.linalg.norm(hunters_vel[i])
        if speed > 15:
            hunters_vel[i] = (hunters_vel[i] / speed) * 15
            
        hunters_pos[i] += hunters_vel[i]
        
        # Draw hunter
        py5.push_matrix()
        py5.translate(*hunters_pos[i])
        
        # Look at direction
        v = hunters_vel[i]
        yaw = py5.atan2(v[1], v[0])
        pitch = py5.atan2(-v[2], py5.sqrt(v[0]**2 + v[1]**2))
        
        py5.rotate_z(yaw)
        py5.rotate_y(pitch)
        
        py5.no_stroke()
        py5.fill(180, 90, 100, 90)
        
        # Scale based on speed
        draw_pyramid(5 + speed * 0.2)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
        import os
        os._exit(0)

py5.run_sketch()
