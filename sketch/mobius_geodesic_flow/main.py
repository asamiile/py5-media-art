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

NUM_PARTICLES = 150000

class MobiusFlow:
    def __init__(self, num_particles):
        self.num = num_particles
        self.u = np.random.rand(self.num) * 4 * np.pi
        self.v = np.random.rand(self.num) * 2 - 1
        
        # Base hue based on initial v position (creates ribbons of color)
        self.hue = (self.v + 1) * 0.5 * 100 + 180 # 180 to 280 (Cyan to Violet)
        
    def step(self, t):
        # Time-varying flow
        # u is the long way around, v is across the strip
        du = 0.02 + 0.005 * np.sin(self.v * 5.0 + t * np.pi * 2)
        dv = 0.003 * np.cos(self.u * 4.0 - t * np.pi * 4)
        
        self.u += du
        self.v += dv
        
        # Soft bounce on v edges
        out_v = np.abs(self.v) > 1.0
        self.v[out_v] = np.sign(self.v[out_v]) * (2.0 - np.abs(self.v[out_v]))
        
        self.u = self.u % (4 * np.pi)
        
    def get_3d(self):
        R = py5.height * 0.25
        W = py5.height * 0.15
        
        v_scaled = self.v * W
        
        # Mobius strip parametric equations
        x = (R + v_scaled * np.cos(self.u / 2)) * np.cos(self.u)
        y = (R + v_scaled * np.cos(self.u / 2)) * np.sin(self.u)
        z = v_scaled * np.sin(self.u / 2)
        
        return x, y, z

sim = None

def setup():
    global sim
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 10)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    sim = MobiusFlow(NUM_PARTICLES)

def draw():
    global sim
    
    # Motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    sim.step(t)
    
    x, y, z = sim.get_3d()
    
    # Rotate the whole strip over time
    angle_x = t * np.pi * 2 + 0.5
    angle_y = t * np.pi * 4 * 0.2
    
    cx, sx = np.cos(angle_x), np.sin(angle_x)
    cy, sy = np.cos(angle_y), np.sin(angle_y)
    
    # Rotation Y
    x1 = x * cy + z * sy
    y1 = y
    z1 = -x * sy + z * cy
    
    # Rotation X
    x2 = x1
    y2 = y1 * cx - z1 * sx
    z2 = y1 * sx + z1 * cx
    
    # Simple perspective
    # Camera distance
    dist = py5.height * 0.8
    scale = dist / (dist - z2)
    
    px = x2 * scale + py5.width / 2
    py_ = y2 * scale + py5.height / 2
    
    # Rendering
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    # Group by color for performance (10 bins)
    num_bins = 10
    bins = np.linspace(180, 280, num_bins+1)
    
    for i in range(num_bins):
        mask = (sim.hue >= bins[i]) & (sim.hue < bins[i+1])
        if not np.any(mask): continue
        
        h = (bins[i] + bins[i+1]) / 2
        py5.stroke(h, 220, 255, 120)
        
        pts_x = px[mask]
        pts_y = py_[mask]
        
        coords = np.column_stack((pts_x, pts_y))
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
