from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
STAR_COUNT = 1200
WAVE_SPEED = 8.0
DECAY = 0.995

class Emitter:
    def __init__(self, angle_offset):
        self.angle_offset = angle_offset
        self.pos = np.array([0.0, 0.0])
        
    def update(self, t):
        # Chirp-like orbit: frequency increases, radius decreases
        # t goes from 0 to 1
        freq = 1.0 + 5.0 * t**2
        radius = 300 * (1.0 - 0.9 * t**1.5)
        angle = self.angle_offset + py5.TWO_PI * freq * (t * 10)
        self.pos[0] = SIZE[0] / 2 + radius * np.cos(angle)
        self.pos[1] = SIZE[1] / 2 + radius * np.sin(angle)

emitters = [Emitter(0), Emitter(np.pi)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # High-density starfield
    for _ in range(STAR_COUNT):
        stars.append({
            "pos": np.array([np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])]),
            "size": np.random.uniform(0.5, 3.0),
            "alpha": np.random.uniform(100, 255),
            "orig_pos": None # set later
        })
        stars[-1]["orig_pos"] = stars[-1]["pos"].copy()
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Update Emitters
    for e in emitters:
        e.update(t)
        
    # 2. Draw Background
    py5.background(2, 2, 8) # Deep obsidian indigo
    
    # 3. Render Waves (as concentric rings/interference)
    # We use many rings to simulate the wavefronts
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    # Number of wave crests to draw
    num_waves = 40
    for i in range(num_waves):
        # Expansion phase
        phase = (py5.frame_count * 0.2 - i * 1.5) % 40
        radius = phase * WAVE_SPEED * 10
        
        if radius < 0: continue
        
        # Color based on emitter index
        # We'll draw two sets of waves
        for idx, e in enumerate(emitters):
            alpha = py5.remap(radius, 0, 2000, 150, 0)
            if alpha <= 0: continue
            
            if idx == 0:
                py5.stroke(0, 200, 255, alpha * 0.3) # Electric Cyan
            else:
                py5.stroke(200, 50, 255, alpha * 0.3) # Royal Amethyst
            
            py5.stroke_weight(2)
            py5.circle(e.pos[0], e.pos[1], radius)
            
            # Subtle second-order ripple
            py5.stroke_weight(0.5)
            py5.circle(e.pos[0], e.pos[1], radius * 1.05)

    # 4. Distortion Starfield
    # Stars shift based on local wave phase (simplified)
    py5.no_stroke()
    for s in stars:
        # Calculate distance to both emitters
        shift = np.array([0.0, 0.0])
        for e in emitters:
            diff = s["orig_pos"] - e.pos
            dist = np.linalg.norm(diff)
            if dist > 0:
                # Wave phase at star position
                w_phase = (dist / (WAVE_SPEED * 10)) - (py5.frame_count * 0.2)
                mag = np.sin(w_phase) * 5.0 * (100 / (dist + 100)) # stronger near emitters
                shift += (diff / dist) * mag
        
        s["pos"] = s["orig_pos"] + shift
        
        # Twinkle
        alpha = s["alpha"] + np.sin(py5.frame_count * 0.1 + s["orig_pos"][0]) * 50
        py5.fill(255, alpha)
        py5.circle(s["pos"][0], s["pos"][1], s["size"])

    # 5. Merger Core Glow
    # Blinding white-gold at the center
    core_alpha = py5.remap(t, 0, 1, 50, 255)
    core_size = py5.remap(t, 0, 1, 10, 150)
    for r in range(10, 0, -1):
        py5.fill(255, 255, 200, core_alpha / (r + 1))
        py5.circle(SIZE[0]/2, SIZE[1]/2, core_size * r * 0.2)

    py5.blend_mode(py5.BLEND)

    # 6. Capture Frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Encode Video
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Select preview frame (towards end of merger)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.9):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
