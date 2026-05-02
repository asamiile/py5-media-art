import numpy as np
from pathlib import Path
import subprocess
import py5
from scipy.ndimage import gaussian_filter

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
# Use preview size for development; the user can switch to OUTPUT_SIZE for final render
SIZE = PREVIEW_SIZE

# Physarum Parameters
NUM_AGENTS = 100000
SENSOR_OFFSET = 12.0
SENSOR_ANGLE = np.radians(25)
TURN_SPEED = np.radians(15)
MOVE_SPEED = 1.8
DECAY_FACTOR = 0.94
DIFFUSION_SIGMA = 0.7

class SlimeSimulation:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # Agents: x, y, angle
        # Start in a circle
        angles = np.random.rand(NUM_AGENTS) * 2 * np.pi
        radii = np.sqrt(np.random.rand(NUM_AGENTS)) * (min(w, h) * 0.45)
        self.pos = np.zeros((NUM_AGENTS, 2))
        self.pos[:, 0] = w / 2 + np.cos(angles) * radii
        self.pos[:, 1] = h / 2 + np.sin(angles) * radii
        self.angle = angles + np.pi # face inward
        
        self.trail = np.zeros((h, w), dtype=np.float32)

    def update(self):
        # 1. Sense
        dist = SENSOR_OFFSET
        
        # Sense Left
        al = self.angle - SENSOR_ANGLE
        xl = (self.pos[:, 0] + np.cos(al) * dist).astype(int) % self.w
        yl = (self.pos[:, 1] + np.sin(al) * dist).astype(int) % self.h
        
        # Sense Center
        ac = self.angle
        xc = (self.pos[:, 0] + np.cos(ac) * dist).astype(int) % self.w
        yc = (self.pos[:, 1] + np.sin(ac) * dist).astype(int) % self.h
        
        # Sense Right
        ar = self.angle + SENSOR_ANGLE
        xr = (self.pos[:, 0] + np.cos(ar) * dist).astype(int) % self.w
        yr = (self.pos[:, 1] + np.sin(ar) * dist).astype(int) % self.h
        
        val_l = self.trail[yl, xl]
        val_c = self.trail[yc, xc]
        val_r = self.trail[yr, xr]

        # 2. Rotate
        mask_l = (val_l > val_c) & (val_l > val_r)
        mask_r = (val_r > val_c) & (val_r > val_l)
        mask_lr = (val_l == val_r) & (val_l > val_c)
        
        self.angle[mask_l] -= TURN_SPEED
        self.angle[mask_r] += TURN_SPEED
        # Equal case: random turn
        mask_eq = mask_lr
        if np.any(mask_eq):
            self.angle[mask_eq] += (np.random.rand(np.sum(mask_eq)) - 0.5) * 2 * TURN_SPEED
        
        # Small random jitter to all
        self.angle += (np.random.rand(NUM_AGENTS) - 0.5) * 0.05

        # 3. Move
        self.pos[:, 0] += np.cos(self.angle) * MOVE_SPEED
        self.pos[:, 1] += np.sin(self.angle) * MOVE_SPEED
        
        # Wrap
        self.pos[:, 0] %= self.w
        self.pos[:, 1] %= self.h

        # 4. Deposit
        px = self.pos[:, 0].astype(int)
        py = self.pos[:, 1].astype(int)
        # Clip to ensure valid indices even if wrap-around logic has edge cases
        px = np.clip(px, 0, self.w - 1)
        py = np.clip(py, 0, self.h - 1)
        np.add.at(self.trail, (py, px), 1.0)

        # 5. Diffuse & Decay
        self.trail = gaussian_filter(self.trail, sigma=DIFFUSION_SIGMA)
        self.trail *= DECAY_FACTOR

sim = None

def setup():
    py5.size(*SIZE)
    # Get actual pixel size (Retina support)
    py5.load_np_pixels()
    ph, pw = py5.np_pixels.shape[:2]
    
    global sim
    sim = SlimeSimulation(pw, ph)
    
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    py5.background(5)

def draw():
    sim.update()
    
    py5.load_np_pixels()
    
    # Normalize trail for color mapping
    # Adjust scaling factor for desired brightness/contrast
    t = np.clip(sim.trail * 0.06, 0, 1)
    
    # Map t [0, 1] to the palette
    # BG: (5, 5, 5)
    # Indigo: (75, 0, 130)  - 60% transition
    # Teal: (0, 255, 204)   - 30% transition
    # Gold: (255, 215, 0)   - 10% transition
    
    # Layer 1: Indigo base
    r = 5 + (75 - 5) * t
    g = 5 + (0 - 5) * t
    b = 5 + (130 - 5) * t
    
    # Layer 2: Teal overlay (mid-range)
    mask2 = t > 0.35
    t2 = np.clip((t[mask2] - 0.35) / 0.45, 0, 1)
    r[mask2] = r[mask2] * (1 - t2) + 0 * t2
    g[mask2] = g[mask2] * (1 - t2) + 255 * t2
    b[mask2] = b[mask2] * (1 - t2) + 204 * t2
    
    # Layer 3: Gold highlights (top range)
    mask3 = t > 0.8
    t3 = np.clip((t[mask3] - 0.8) / 0.2, 0, 1)
    r[mask3] = r[mask3] * (1 - t3) + 255 * t3
    g[mask3] = g[mask3] * (1 - t3) + 215 * t3
    b[mask3] = b[mask3] * (1 - t3) + 0 * t3

    py5.np_pixels[:, :, 0] = r.astype(np.uint8)
    py5.np_pixels[:, :, 1] = g.astype(np.uint8)
    py5.np_pixels[:, :, 2] = b.astype(np.uint8)
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print("Rendering video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        
        # Save preview (middle frame)
        mid_frame = min(TOTAL_FRAMES, max(1, int(TOTAL_FRAMES * 0.7))) # Pick a frame where it's well developed
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
