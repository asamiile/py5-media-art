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

# Data structures for coral growth
branches = []

class Branch:
    def __init__(self, x, y, z, length, radius, angle_x, angle_y, depth):
        self.x = x
        self.y = y
        self.z = z
        self.length = length
        self.radius = radius
        self.angle_x = angle_x
        self.angle_y = angle_y
        self.depth = depth
        self.children = []
        self.max_depth = 5
        self.seed = random.uniform(0, 1000)
        
    def draw(self, frame):
        py5.push_matrix()
        py5.translate(self.x, self.y, self.z)
        
        # Sway
        sway_x = (py5.os_noise(self.seed, frame * 0.005) - 0.5) * py5.PI / 8
        sway_y = (py5.os_noise(self.seed + 1000, frame * 0.005) - 0.5) * py5.PI / 8
        
        py5.rotate_x(self.angle_x + sway_x)
        py5.rotate_y(self.angle_y + sway_y)
        
        # Draw segment as a glowing line to simulate translucent coral
        color_val = py5.color(
            py5.remap(self.depth, 0, self.max_depth, 160, 280) % 360,
            80,
            100,
            50
        )
        py5.stroke(color_val)
        py5.stroke_weight(self.radius)
        py5.line(0, 0, 0, 0, -self.length, 0)
        
        py5.translate(0, -self.length, 0)
        
        if self.depth == self.max_depth:
            # Draw polyp tip
            py5.no_stroke()
            py5.fill((py5.remap(self.depth, 0, self.max_depth, 160, 280) + frame * 0.5) % 360, 90, 100, 80)
            py5.push_matrix()
            py5.scale(self.radius * 1.5)
            py5.sphere_detail(5)
            py5.sphere(1)
            py5.pop_matrix()
            
        for child in self.children:
            child.draw(frame)
            
        py5.pop_matrix()

def generate_coral(b, depth):
    if depth > b.max_depth:
        return
    num_children = random.randint(1, 3) if depth < b.max_depth else 0
    for _ in range(num_children):
        child = Branch(0, 0, 0,
                       b.length * random.uniform(0.6, 0.8),
                       b.radius * 0.7,
                       random.uniform(-py5.PI/4, py5.PI/4),
                       random.uniform(-py5.PI/4, py5.PI/4),
                       depth + 1)
        b.children.append(child)
        generate_coral(child, depth + 1)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate coral clusters
    for _ in range(12):
        root = Branch(
            random.uniform(-SIZE[0]/2, SIZE[0]/2),
            SIZE[1]/2,
            random.uniform(-SIZE[0]/2, SIZE[0]/2),
            random.uniform(100, 300),
            random.uniform(5, 15),
            0,
            0,
            0
        )
        generate_coral(root, 0)
        branches.append(root)

def draw():
    py5.background(220, 80, 10) # Dark deep sea blue
    py5.blend_mode(py5.ADD)
    
    # Camera movement
    cam_x = py5.sin(py5.frame_count * 0.005) * SIZE[0] * 0.8
    cam_z = py5.cos(py5.frame_count * 0.005) * SIZE[0] * 0.8 + SIZE[0] / 2
    py5.camera(cam_x, SIZE[1] * 0.2, cam_z, 0, SIZE[1]/2, 0, 0, 1, 0)
    
    # Fog / depth effect
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    for b in branches:
        b.draw(py5.frame_count)
        
    py5.hint(py5.ENABLE_DEPTH_TEST)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
