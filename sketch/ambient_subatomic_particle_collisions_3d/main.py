from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

particles = []

class Particle:
    def __init__(self, pos, vel, size, color, life, parent_gen=0):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.size = size
        self.color = color
        self.life = life
        self.max_life = life
        self.parent_gen = parent_gen
        self.history = [np.copy(self.pos)]

    def update(self):
        # Magnetic field spiraling effect
        # Cross product of velocity and a magnetic field pointing mostly in Z
        B = np.array([0.0, 0.0, 1.0])
        force = np.cross(self.vel, B) * 0.1
        self.vel += force
        
        # Add a bit of noise
        noise_vec = np.array([
            py5.os_noise(self.pos[0] * 0.005, self.pos[1] * 0.005, py5.frame_count * 0.01),
            py5.os_noise(self.pos[1] * 0.005, self.pos[2] * 0.005, py5.frame_count * 0.01),
            py5.os_noise(self.pos[2] * 0.005, self.pos[0] * 0.005, py5.frame_count * 0.01)
        ]) * 0.5 - 0.25
        self.vel += noise_vec
        
        self.pos += self.vel
        self.history.append(np.copy(self.pos))
        if len(self.history) > 20:
            self.history.pop(0)
        self.life -= 1

def spawn_collision():
    num_particles = random.randint(50, 150)
    for _ in range(num_particles):
        vel = np.random.randn(3) * random.uniform(2.0, 15.0)
        col_idx = random.randint(0, 3)
        colors = [
            (255, 100, 100, 150),
            (100, 255, 100, 150),
            (100, 100, 255, 150),
            (255, 255, 100, 150)
        ]
        particles.append(Particle([0, 0, 0], vel, random.uniform(2, 6), colors[col_idx], random.randint(30, 120), 0))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10)
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(10)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Rotate camera
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    # Occasional new collisions
    if py5.frame_count % 60 == 1 or random.random() < 0.01:
        spawn_collision()
        
    global particles
    new_particles = []
    
    py5.no_fill()
    for p in particles:
        p.update()
        
        if p.life > 0:
            new_particles.append(p)
            
            # Draw trail
            py5.stroke(p.color[0], p.color[1], p.color[2], p.color[3] * (p.life / p.max_life))
            py5.stroke_weight(p.size * (p.life / p.max_life))
            py5.begin_shape()
            for hist_pos in p.history:
                py5.vertex(hist_pos[0], hist_pos[1], hist_pos[2])
            py5.end_shape()
            
            # Sub-collisions/decays
            if p.parent_gen < 2 and random.random() < 0.02:
                for _ in range(random.randint(2, 5)):
                    sub_vel = p.vel * 0.5 + np.random.randn(3) * random.uniform(1.0, 5.0)
                    new_particles.append(Particle(p.pos, sub_vel, p.size * 0.7, p.color, random.randint(20, 60), p.parent_gen + 1))
                p.life = 0 # Parent dies

    particles = new_particles

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
