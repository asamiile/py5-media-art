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

class KuramotoSim:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        
        # Grid dimensions for simulation (downscaled for performance, then scaled up when drawing)
        self.gw = 640
        self.gh = 360
        
        # Phase grid
        self.theta = np.random.rand(self.gh, self.gw) * 2 * np.pi
        
        # Natural frequencies
        # Generate some spatial noise for frequencies using simple sine waves
        x = np.linspace(0, 10, self.gw)
        y = np.linspace(0, 10, self.gh)
        X, Y = np.meshgrid(x, y)
        self.omega = 1.0 + 0.5 * np.sin(X*1.5) * np.cos(Y*1.5) + 0.2 * np.sin(X*4 + Y*3)
        
        self.dt = 0.05
        self.K = 1.8 # Coupling strength
        
    def step(self):
        # Calculate phase differences with 4 neighbors
        theta_up = np.roll(self.theta, 1, axis=0)
        theta_down = np.roll(self.theta, -1, axis=0)
        theta_left = np.roll(self.theta, 1, axis=1)
        theta_right = np.roll(self.theta, -1, axis=1)
        
        coupling = (
            np.sin(theta_up - self.theta) +
            np.sin(theta_down - self.theta) +
            np.sin(theta_left - self.theta) +
            np.sin(theta_right - self.theta)
        )
        
        dtheta = self.omega + self.K * coupling
        self.theta += dtheta * self.dt
        self.theta = self.theta % (2 * np.pi)

sim = None

def setup():
    global sim
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    sim = KuramotoSim(py5.width, py5.height)

def draw():
    global sim
    
    # Run multiple substeps
    for _ in range(3):
        sim.step()
    
    # Calculate colors based on phase
    # sin(theta) gives an oscillating value [-1, 1]
    # We want flashes of light when phase is near pi/2
    intensity = np.sin(sim.theta)
    
    # Make the flash sharp
    flash = np.power(np.clip(intensity, 0, 1), 4.0)
    
    # Base background: Deep Indigo
    # Flash color: Cyan to Golden Glow
    
    # Colors (A, R, G, B)
    r = (10 + flash * 240).astype(np.uint8)
    g = (15 + flash * 200).astype(np.uint8)
    b = (35 + flash * 100).astype(np.uint8)
    a = np.full_like(r, 255)
    
    img = py5.create_image(sim.gw, sim.gh, py5.ARGB)
    img.load_np_pixels()
    # Write to channels. ARGB format: A, R, G, B
    img.np_pixels[:, :, 0] = a
    img.np_pixels[:, :, 1] = r
    img.np_pixels[:, :, 2] = g
    img.np_pixels[:, :, 3] = b
    img.update_np_pixels()
    
    # Draw scaled image to screen
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
