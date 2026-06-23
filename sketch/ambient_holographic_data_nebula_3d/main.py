from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class DataNode:
    def __init__(self):
        self.x = random.uniform(-600, 600)
        self.y = random.uniform(-600, 600)
        self.z = random.uniform(-600, 600)
        self.hue = random.choice([190, 280, 320]) # Cyan, Purple, Magenta
        self.size = random.uniform(2, 6)
        
    def update(self, t):
        noise_scale = 0.003
        angle1 = py5.os_noise(self.x * noise_scale, self.y * noise_scale, t) * py5.PI * 2
        angle2 = py5.os_noise(self.y * noise_scale, self.z * noise_scale, t + 50) * py5.PI * 2
        
        self.x += py5.cos(angle1) * 2
        self.y += py5.sin(angle1) * 2
        self.z += py5.sin(angle2) * 2
        
        # Wrap around
        if self.x > 600: self.x = -600
        if self.x < -600: self.x = 600
        if self.y > 600: self.y = -600
        if self.y < -600: self.y = 600
        if self.z > 600: self.z = -600
        if self.z < -600: self.z = 600

nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(500):
        nodes.append(DataNode())

def draw():
    py5.background(240, 90, 10) # Dark blue void
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera slow rotation
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.001)
    
    t = py5.frame_count * 0.01
    
    py5.blend_mode(py5.ADD)
    
    for n in nodes:
        n.update(t)
        
    # Draw connections
    py5.stroke_weight(1)
    for i, n1 in enumerate(nodes):
        connected = 0
        for j in range(i + 1, len(nodes)):
            n2 = nodes[j]
            d = py5.dist(n1.x, n1.y, n1.z, n2.x, n2.y, n2.z)
            if d < 120:
                alpha = py5.map_value(d, 0, 120, 80, 0)
                py5.stroke(n1.hue, 80, 100, alpha)
                py5.line(n1.x, n1.y, n1.z, n2.x, n2.y, n2.z)
                connected += 1
                if connected > 4:
                    break
                    
        py5.no_stroke()
        py5.fill(n1.hue, 50, 100, 90)
        py5.push_matrix()
        py5.translate(n1.x, n1.y, n1.z)
        py5.box(n1.size)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
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
