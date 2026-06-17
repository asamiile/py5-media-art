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

NUM_PARTICLES = 4000
particles = []

class Photon:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        # Most photons travel roughly towards +z (the camera) but with some inward spiraling
        self.vel = np.array([-y * 0.02 - x * 0.005, x * 0.02 - y * 0.005, random.uniform(2.0, 5.0)], dtype=float)
        self.history = [self.pos.copy()]
        self.dead = False
        # Assign a warm color
        hue = random.uniform(10, 45) # Deep orange to yellow
        self.color = (hue, random.uniform(80, 100), random.uniform(50, 100))
        
def spawn_photon():
    # Spawn in an accretion disk (xy plane) far away
    r = random.uniform(150, 600)
    theta = random.uniform(0, 2*np.pi)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = random.uniform(-1000, -800)
    return Photon(x, y, z)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    for _ in range(NUM_PARTICLES):
        particles.append(spawn_photon())

def draw():
    # Fade background to leave trails
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    
    # Static camera looking at origin
    py5.camera(0, -200, 800, 0, 0, 0, 0, 1, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Black hole mass
    GM = 150000.0
    
    global particles
    for p in particles:
        if p.dead:
            continue
            
        # Distance to center
        r_vec = -p.pos
        r_sq = np.dot(r_vec, r_vec)
        r = np.sqrt(r_sq)
        
        # Event horizon check
        if r < 60:
            p.dead = True
            continue
            
        # Out of bounds check
        if p.pos[2] > 1000 or r > 1500:
            p.dead = True
            continue
            
        # Gravitational pull (approximating bending of light)
        # F = G*M / r^2
        if r > 10:
            force_mag = GM / r_sq
            force = (r_vec / r) * force_mag
            p.vel += force
            
        # Speed limit
        speed = np.linalg.norm(p.vel)
        if speed > 15.0:
            p.vel = (p.vel / speed) * 15.0
            
        p.pos += p.vel
        p.history.append(p.pos.copy())
        
        if len(p.history) > 20:
            p.history.pop(0)
            
        py5.stroke(p.color[0], p.color[1], p.color[2], 150)
        py5.begin_shape()
        for hist_p in p.history:
            py5.vertex(hist_p[0], hist_p[1], hist_p[2])
        py5.end_shape()
        
    # Replace dead particles
    particles = [p for p in particles if not p.dead]
    while len(particles) < NUM_PARTICLES:
        particles.append(spawn_photon())
        
    # Draw event horizon (pure black sphere to occlude)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0)
    py5.sphere_detail(30)
    py5.push_matrix()
    py5.rotate_x(py5.frame_count * 0.01)
    py5.sphere(60)
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

py5.run_sketch()
