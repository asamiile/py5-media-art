from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p2.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
NUM_DROPLETS = 64 # 4x4x4
PARTICLES_PER_DROPLET = 1500
TOTAL_PARTICLES = NUM_DROPLETS * PARTICLES_PER_DROPLET
LATTICE_STEP = 300.0  # Scaled up step for 4K canvas

class SupersolidSimulation:
    def __init__(self, n_droplets, p_per_d):
        self.nd = n_droplets
        self.ppd = p_per_d
        self.total = n_droplets * p_per_d
        
        # Grid positions
        side = int(np.cbrt(n_droplets))
        self.grid = np.stack(np.meshgrid(
            np.linspace(-(side-1)*LATTICE_STEP/2, (side-1)*LATTICE_STEP/2, side),
            np.linspace(-(side-1)*LATTICE_STEP/2, (side-1)*LATTICE_STEP/2, side),
            np.linspace(-(side-1)*LATTICE_STEP/2, (side-1)*LATTICE_STEP/2, side)
        ), axis=-1).reshape(-1, 3).astype(np.float32)
        
        # Particle relative positions (droplet cloud - scaled for 4K)
        self.rel_pos = np.random.normal(0, 60, (self.total, 3)).astype(np.float32)
        self.droplet_idx = np.repeat(np.arange(n_droplets), p_per_d)
        
        self.phase = np.random.rand(n_droplets).astype(np.float32) * np.pi * 2
        self.freq = np.random.uniform(0.5, 1.5, n_droplets).astype(np.float32)

    def get_points(self, t):
        # Wave propagation through lattice
        # k-vector for the phonon mode
        k = np.array([0.01, 0.01, 0.01], dtype=np.float32)
        omega = 0.05
        
        # Displacement of droplets (scaled amplitude and distance frequency for 4K)
        dist_to_origin = np.linalg.norm(self.grid, axis=1)
        amp = 40.0 * np.sin(dist_to_origin * 0.005 - t * omega)
        disp = amp[:, np.newaxis] * k / np.linalg.norm(k)
        
        # Current centers
        centers = self.grid + disp
        
        # Particle positions
        p_pos = centers[self.droplet_idx] + self.rel_pos
        
        # Breathing droplets (scaled distance frequency for 4K)
        breath = 1.0 + 0.2 * np.sin(dist_to_origin[self.droplet_idx] * 0.01 - t * 0.1)
        p_pos = centers[self.droplet_idx] + (self.rel_pos * breath[:, np.newaxis])
        
        return p_pos

sim = SupersolidSimulation(NUM_DROPLETS, PARTICLES_PER_DROPLET)

import shutil

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)  # Capping at 1x density prevents Retina-doubling lag on 4K renders
    py5.smooth(8)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 10, 20)

def draw():
    t = py5.frame_count
    
    # Progress logs to prevent command timeouts
    if t % 60 == 0:
        print(f"[Render Progress] Frame {t}/{TOTAL_FRAMES} ({t/TOTAL_FRAMES*100:.1f}%)")
        
    py5.background(5, 10, 20)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.005)
    py5.rotate_x(t * 0.002)
    
    points = sim.get_points(t)
    
    # Color mapping: Distance from origin and breathing state
    dist = np.linalg.norm(points, axis=1)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.stroke_weight(2.5)  # Balanced for 4K
    
    # Use additive blending for glowing effect
    # We'll split particles by droplet for slightly different hues
    for i in range(NUM_DROPLETS):
        mask = sim.droplet_idx == i
        p = points[mask]
        
        # Hue shifts from Blue (200) to Green (120) based on t and position
        d_center = np.linalg.norm(sim.grid[i])
        hue = 180 + 40 * np.sin(d_center * 0.005 - t * 0.05)  # Scaled distance frequency for 4K
        alpha = 30 + 10 * np.sin(d_center * 0.01 + t * 0.1)  # Scaled distance frequency for 4K
        
        py5.stroke(hue, 70, 100, alpha)
        py5.points(p)
        
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.pop_matrix()

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into 4K video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "22",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Mirror output
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
