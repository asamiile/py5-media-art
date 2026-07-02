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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Agent:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        # Random initial velocity
        theta = random.uniform(0, np.pi*2)
        phi = random.uniform(0, np.pi)
        self.vel = np.array([np.sin(phi)*np.cos(theta), np.sin(phi)*np.sin(theta), np.cos(phi)], dtype=float)
        self.history = [self.pos.copy()]
        self.age = 0
        self.max_age = random.randint(100, 400)
        self.dead = False

agents = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    # Spawn initial agents in center
    for _ in range(50):
        agents.append(Agent(0, 0, 0))

def draw():
    global agents
    # Draw dark background with some transparency to create trails
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    
    # Use push/pop matrix to draw full screen rect without camera translation
    py5.push_matrix()
    py5.camera() # reset camera to default
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    
    # Set up camera to slowly orbit
    cam_radius = 800
    cam_angle = py5.frame_count * 0.005
    cam_x = np.cos(cam_angle) * cam_radius
    cam_z = np.sin(cam_angle) * cam_radius
    py5.camera(cam_x, 300 * np.sin(cam_angle * 0.5), cam_z, 0, 0, 0, 0, 1, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    time_offset = py5.frame_count * 0.01
    
    new_agents = []
    
    for a in agents:
        if a.dead:
            continue
            
        a.age += 1
        if a.age > a.max_age:
            a.dead = True
            # Branching chance when dying
            if random.random() < 0.8 and len(agents) + len(new_agents) < 2000:
                for _ in range(random.randint(1, 3)):
                    new_agents.append(Agent(a.pos[0], a.pos[1], a.pos[2]))
            continue
            
        # Curl noise movement
        nx = py5.os_noise(a.pos[0] * 0.002, a.pos[1] * 0.002, time_offset) * 2 - 1
        ny = py5.os_noise(a.pos[1] * 0.002, a.pos[2] * 0.002, time_offset + 10) * 2 - 1
        nz = py5.os_noise(a.pos[2] * 0.002, a.pos[0] * 0.002, time_offset + 20) * 2 - 1
        
        force = np.array([nx, ny, nz])
        a.vel += force * 0.2
        
        # Limit speed
        speed = np.linalg.norm(a.vel)
        if speed > 2.0:
            a.vel = (a.vel / speed) * 2.0
            
        a.pos += a.vel
        a.history.append(a.pos.copy())
        
        # Keep history short for performance
        if len(a.history) > 30:
            a.history.pop(0)
            
        # Draw path
        py5.color_mode(py5.HSB, 360, 100, 100, 255)
        # Deep cyan to jade/emerald colors (120 to 180 hue)
        my_hue = 150 + nx * 30
        py5.stroke(my_hue, 80, 100, 100)
        
        py5.begin_shape()
        for p in a.history:
            py5.vertex(p[0], p[1], p[2])
        py5.end_shape()
        
        # Draw glowing tip
        py5.push_matrix()
        py5.translate(a.pos[0], a.pos[1], a.pos[2])
        py5.no_stroke()
        py5.fill(my_hue, 50, 100, 200)
        # py5.sphere is too slow for 2000 agents. Use rect facing camera.
        py5.rect_mode(py5.CENTER)
        py5.rect(0, 0, 4, 4)
        py5.pop_matrix()
        
    agents.extend(new_agents)
    
    # Remove dead agents that have no history left to clear them out
    if py5.frame_count % 120 == 0:
        agents = [a for a in agents if not a.dead]
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save gigabytes of local storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
