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

class Point:
    def __init__(self, x, y, pinned=False):
        self.x = x
        self.y = y
        self.oldx = x + random.uniform(-1, 1)
        self.oldy = y + random.uniform(-1, 1)
        self.pinned = pinned
        self.base_x = x

class Spring:
    def __init__(self, p1, p2, rest_length):
        self.p1 = p1
        self.p2 = p2
        self.rest_length = rest_length
        self.active = True
        self.tear_threshold = rest_length * random.uniform(3.0, 6.0)

points = []
springs = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize cloth
    cols = 80
    rows = 50
    spacing = 30
    
    start_x = (SIZE[0] - (cols - 1) * spacing) / 2
    start_y = 200
    
    grid = []
    for y in range(rows):
        row_points = []
        for x in range(cols):
            pinned = (y == 0)
            p = Point(start_x + x * spacing, start_y + y * spacing, pinned)
            points.append(p)
            row_points.append(p)
        grid.append(row_points)
        
    for y in range(rows):
        for x in range(cols):
            p = grid[y][x]
            if x < cols - 1:
                springs.append(Spring(p, grid[y][x+1], spacing))
            if y < rows - 1:
                springs.append(Spring(p, grid[y+1][x], spacing))
                
    py5.background(10, 10, 5)

def draw():
    # Motion blur background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 5, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    friction = 0.98
    gravity = 0.5
    wind_strength = 2.5
    
    # Move pinned points to simulate swinging
    swing_offset = py5.sin(time_val * 0.5) * 400
    
    for p in points:
        if p.pinned:
            p.x = p.base_x + swing_offset
            continue
            
        vx = (p.x - p.oldx) * friction
        vy = (p.y - p.oldy) * friction
        p.oldx = p.x
        p.oldy = p.y
        p.x += vx
        p.y += vy + gravity
        
        # Wind force
        noise_val = py5.os_noise(p.x * 0.001, p.y * 0.001, time_val)
        wind_vx = py5.cos(noise_val * py5.TWO_PI * 3) * wind_strength
        wind_vy = py5.sin(noise_val * py5.TWO_PI * 3) * wind_strength
        
        # Additional gust based on time
        gust = py5.os_noise(time_val * 2, 0) * 5
        
        p.x += wind_vx + gust
        p.y += wind_vy
        
        # Boundaries
        if p.y > SIZE[1] - 50:
            p.y = SIZE[1] - 50
            p.oldy = p.y + vy * 0.5

    # Relaxation passes
    for _ in range(3):
        for s in springs:
            if not s.active:
                continue
            dx = s.p2.x - s.p1.x
            dy = s.p2.y - s.p1.y
            dist = py5.sqrt(dx*dx + dy*dy)
            
            if dist == 0:
                dist = 0.001
                
            if dist > s.tear_threshold:
                s.active = False
                continue
                
            diff = (s.rest_length - dist) / dist
            ox = dx * 0.5 * diff
            oy = dy * 0.5 * diff
            
            if not s.p1.pinned:
                s.p1.x -= ox
                s.p1.y -= oy
            if not s.p2.pinned:
                s.p2.x += ox
                s.p2.y += oy

    # Drawing
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    
    hue_base = (time_val * 50) % 360
    
    for s in springs:
        if s.active:
            # Color based on strain
            dx = s.p2.x - s.p1.x
            dy = s.p2.y - s.p1.y
            dist = py5.sqrt(dx*dx + dy*dy)
            strain = min(1.0, max(0.0, (dist - s.rest_length) / (s.tear_threshold - s.rest_length)))
            
            hue = (hue_base + strain * 60) % 360
            brightness = 50 + strain * 50
            alpha = 100 + strain * 155
            
            py5.stroke(hue, 80, brightness, alpha)
            py5.vertex(s.p1.x, s.p1.y)
            py5.vertex(s.p2.x, s.p2.y)
            
    py5.end_shape()

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
