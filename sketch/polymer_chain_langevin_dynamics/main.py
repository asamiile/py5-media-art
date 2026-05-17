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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_CHAINS = 150
CHAIN_LENGTH = 1000

class PolymerSimulation:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        
        # Positions: shape (chains, length, 2)
        # Initialize randomly but close to center
        self.pos = np.random.rand(NUM_CHAINS, CHAIN_LENGTH, 2) * 0.1 + 0.45
        
        # Sort along chains so they are somewhat ordered initially
        self.pos = np.sort(self.pos, axis=1)
        
        # Velocities
        self.vel = np.zeros_like(self.pos)
        
        # Colors: Assign a hue per chain
        self.hues = np.linspace(160, 320, NUM_CHAINS) # Cyan to Magenta
        # Shuffle hues so neighbors aren't identical color
        np.random.shuffle(self.hues)
        
        self.k_spring = 0.8
        self.damping = 0.85
        self.noise_strength = 0.003
        self.swirl_strength = 0.004
        
    def step(self, t):
        # 1. Spring force
        d = self.pos[:, 1:, :] - self.pos[:, :-1, :]
        f_spring = self.k_spring * d
        
        force = np.zeros_like(self.pos)
        force[:, :-1, :] += f_spring
        force[:, 1:, :] -= f_spring
        
        # 2. Fluid Swirl Field (Time varying)
        # Scale positions to a frequency
        freq = 4.0
        # curl of a scalar potential: 
        # psi = sin(x)*cos(y), vx = d(psi)/dy = -sin(x)sin(y), vy = -d(psi)/dx = -cos(x)cos(y)
        # Let's use simpler shifting sines
        px = self.pos[:, :, 0] * freq
        py = self.pos[:, :, 1] * freq
        
        fx = np.sin(py + t * np.pi * 2) * np.cos(px - t * np.pi)
        fy = -np.cos(px + t * np.pi * 2) * np.sin(py + t * np.pi)
        
        force[:, :, 0] += fx * self.swirl_strength
        force[:, :, 1] += fy * self.swirl_strength
        
        # 3. Thermal Noise (Langevin)
        force += np.random.randn(*self.pos.shape) * self.noise_strength
        
        # 4. Global confinement (soft boundary push)
        center_dist_x = self.pos[:, :, 0] - 0.5
        center_dist_y = self.pos[:, :, 1] - 0.5
        dist_sq = center_dist_x**2 + center_dist_y**2
        
        # Push back if too far from center
        push = dist_sq * 0.05
        force[:, :, 0] -= center_dist_x * push
        force[:, :, 1] -= center_dist_y * push
        
        # Integrate
        self.vel = self.vel * self.damping + force
        self.pos += self.vel

sim = None

def setup():
    global sim
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 10, 15)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    sim = PolymerSimulation(py5.width, py5.height)

def draw():
    global sim
    
    # Slight motion blur with dark background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10, 15, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # 5 substeps for stability of the spring physics
    for _ in range(5):
        sim.step(t)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    # Draw chains
    for i in range(NUM_CHAINS):
        pts = sim.pos[i]
        px = pts[:, 0] * py5.width
        py = pts[:, 1] * py5.height
        coords = np.column_stack((px, py))
        
        # Use chain hue
        py5.stroke(sim.hues[i], 200, 255, 60)
        py5.points(coords)
    
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

py5.run_sketch()
