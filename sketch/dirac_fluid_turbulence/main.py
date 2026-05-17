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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
NUM_PARTICLES = 100000  # Scaled up for ultra-lush 4K density
V_BG = 8.0  # Scaled background speed for 4K flow rate

class DiracFluidSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        self.pos = np.random.rand(n_particles, 2).astype(np.float32)
        self.pos[:, 0] *= SIZE[0]
        self.pos[:, 1] *= SIZE[1]
        self.phase = np.random.rand(n_particles).astype(np.float32) * np.pi * 2
        
        # Obstacle (scaled size for 4K)
        self.obs_pos = np.array([SIZE[0]*0.25, SIZE[1]*0.5], dtype=np.float32)
        self.obs_r = 160.0

    def update(self, t):
        # Background flow
        self.pos[:, 0] += V_BG
        
        # Vortex Street (von Karman)
        # We'll place a few periodic vortices
        # One every 60 frames
        n_vortices = 12
        v_period = 60
        for i in range(n_vortices):
            v_t = (t - i * v_period) % (n_vortices * v_period)
            if v_t < 0: continue
            
            # Vortex position drifts with flow
            # Sign alternates (scaled parameters for 4K)
            sign = 1 if i % 2 == 0 else -1
            vx = self.obs_pos[0] + v_t * V_BG * 0.8
            vy = self.obs_pos[1] + sign * 120 * np.sin(v_t * 0.05)
            
            # Influence
            dx = self.pos[:, 0] - vx
            dy = self.pos[:, 1] - vy
            d2 = dx*dx + dy*dy + 2000 # Softening (scaled for 4K)
            
            # Induced velocity (rotational)
            strength = 32000.0 * np.exp(-v_t * 0.005) # Fades over time (scaled for 4K)
            self.pos[:, 0] -= strength * dy / d2
            self.pos[:, 1] += strength * dx / d2
            
        # Wrap around
        self.pos[:, 0] %= SIZE[0]
        # Keep within y bounds
        self.pos[:, 1] = np.clip(self.pos[:, 1], 0, SIZE[1])
        
        # Avoid obstacle
        dx = self.pos[:, 0] - self.obs_pos[0]
        dy = self.pos[:, 1] - self.obs_pos[1]
        d = np.sqrt(dx*dx + dy*dy)
        mask = d < self.obs_r
        if np.any(mask):
            self.pos[mask, 0] = self.obs_pos[0] + dx[mask] / d[mask] * self.obs_r
            self.pos[mask, 1] = self.obs_pos[1] + dy[mask] / d[mask] * self.obs_r

    def get_points(self):
        return self.pos

sim = DiracFluidSimulation(NUM_PARTICLES)

import shutil

def setup():
    py5.size(*SIZE, py5.P2D)  # Use GPU accelerated P2D
    py5.pixel_density(1)  # Capping at 1x density prevents Retina-doubling lag on 4K renders
    py5.smooth(8)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 5, 20)

def draw():
    t = py5.frame_count
    
    # Progress logs to prevent command timeouts
    if t % 60 == 0:
        print(f"[Render Progress] Frame {t}/{TOTAL_FRAMES} ({t/TOTAL_FRAMES*100:.1f}%)")
    
    # Motion Blur effect
    py5.fill(10, 5, 20, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    sim.update(t)
    points = sim.get_points()
    
    # Color based on y position and velocity
    # Plasma Blue to Electric Gold
    py5.stroke_weight(2.0)  # Balanced for 4K
    
    # We'll use HSB for the gradient
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Split by y bands for performance
    n_bands = 12
    for i in range(n_bands):
        y_low = i * (SIZE[1] / n_bands)
        y_high = (i + 1) * (SIZE[1] / n_bands)
        mask = (points[:, 1] >= y_low) & (points[:, 1] < y_high)
        if np.any(mask):
            # Blue (200) to Purple (280) or Gold (50)
            # Let's use a dynamic hue
            hue = 200 + 40 * np.sin(t * 0.02 + i * 0.5)
            # Add some Gold highlights near the obstacle or vortices
            py5.stroke(hue, 80, 100, 40)
            py5.points(points[mask])
            
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    
    # Draw Obstacle
    py5.no_fill()
    py5.stroke(255, 255, 255, 40)
    py5.stroke_weight(4.0)  # Balanced for 4K
    py5.circle(sim.obs_pos[0], sim.obs_pos[1], sim.obs_r * 2)

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
