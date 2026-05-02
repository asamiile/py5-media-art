import numpy as np
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Palette
CLR_BG = (10, 10, 21) # Obsidian Navy
CHANNELS = [
    (255, 30, 80, "R"),   # Vibrant Red
    (30, 255, 100, "G"),  # Vibrant Green
    (40, 100, 255, "B")   # Vibrant Blue
]

class DriftAgent:
    def __init__(self, w, h, channel_idx):
        self.pos = np.random.rand(2) * [w, h]
        self.vel = np.zeros(2)
        self.channel_idx = channel_idx
        self.life = np.random.rand()
        # Each channel has slightly different "mass" and "drag"
        self.speed = 1.0 + channel_idx * 0.08
        self.drag = 0.92 + channel_idx * 0.01
        self.phase = np.random.rand() * 1000

    def update(self, w, h):
        t = py5.frame_count * 0.006
        # Large scale flow field
        scale = 0.0015
        # Offset noise per channel for prismatic separation
        noise_off = self.channel_idx * 0.8
        
        angle = py5.noise(self.pos[0] * scale, self.pos[1] * scale, t + noise_off) * py5.TWO_PI * 3
        
        force = np.array([np.cos(angle), np.sin(angle)])
        self.vel += force * 0.22
        self.vel *= self.drag
        self.pos += self.vel * self.speed
        
        # Border wrap
        self.pos[0] %= w
        self.pos[1] %= h

    def draw(self):
        clr = CHANNELS[self.channel_idx]
        # Higher alpha for better visibility
        alpha_base = 15 + 25 * np.sin(py5.frame_count * 0.03 + self.phase)
        # Occasional "flare"
        if np.random.rand() > 0.999: alpha_base *= 5
        py5.stroke(clr[0], clr[1], clr[2], alpha_base)
        # Draw as tiny glowing particles or short segments
        py5.point(self.pos[0], self.pos[1])

def setup():
    py5.size(*SIZE)
    global agents
    agents = []
    # 20,000 agents per channel for a much denser look
    n_per_channel = 20000
    for c_idx in range(len(CHANNELS)):
        for _ in range(n_per_channel):
            agents.append(DriftAgent(py5.width, py5.height, c_idx))
            
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    py5.background(*CLR_BG)
    py5.stroke_weight(1.0)

def draw():
    # Slower fade for more accumulation
    py5.no_stroke()
    py5.fill(*CLR_BG, 5) # Extremely slow fade for cumulative light
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.SCREEN)
    
    # Update and draw agents
    for a in agents:
        a.update(py5.width, py5.height)
        a.draw()
        
    py5.blend_mode(py5.BLEND)
    
    # Occasional "refractive flash"
    if py5.frame_count % 120 == 0:
        py5.no_fill()
        py5.stroke(240, 240, 255, 2)
        py5.stroke_weight(200)
        py5.ellipse(py5.width/2, py5.height/2, py5.width*1.5, py5.height*1.5)
        py5.stroke_weight(1.2)
    
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
        # Capture a frame where the prismatic effect is well-developed
        mid_frame = int(TOTAL_FRAMES * 0.8)
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
