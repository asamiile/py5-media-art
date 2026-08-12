from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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
DURATION_SEC = 6
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Cell agents parameter
MAX_CELLS = 80
cells = []


class Cell:
    def __init__(self, x, y, radius):
        self.pos = np.array([x, y], dtype=np.float32)
        self.vel = np.zeros(2, dtype=np.float32)
        self.radius = radius
        self.target_radius = radius
        # Custom local offset phase for internal texture pulsing
        self.phase = random.uniform(0.0, py5.TWO_PI)
        self.growth_rate = random.uniform(0.1, 0.3)

    def update(self):
        # Gradual growth
        if self.radius < self.target_radius:
            self.radius += self.growth_rate
        # Cap velocity and apply drag
        v_len = np.linalg.norm(self.vel)
        if v_len > 4.0:
            self.vel = (self.vel / v_len) * 4.0
        self.pos += self.vel
        self.vel *= 0.85


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize with 4 starting cells
    cx = SIZE[0] / 2
    cy = SIZE[1] / 2
    for i in range(4):
        angle = i * py5.TWO_PI / 4
        dist = 80.0
        x = cx + dist * np.cos(angle)
        y = cy + dist * np.sin(angle)
        cells.append(Cell(x, y, 40.0))


def draw():
    global cells
    
    # Render dark background with trails
    py5.blend_mode(py5.BLEND)
    py5.fill(4, 3, 6, 25)
    py5.rect(0, 0, *SIZE)
    
    py5.blend_mode(py5.ADD)
    
    num_cells = len(cells)
    
    # 1. Physics: Mechanical repulsion between overlapping cells
    positions = np.array([c.pos for c in cells], dtype=np.float32)
    radii = np.array([c.radius for c in cells], dtype=np.float32)
    
    for i in range(num_cells):
        for j in range(i + 1, num_cells):
            diff = cells[i].pos - cells[j].pos
            dist = np.linalg.norm(diff)
            min_dist = cells[i].radius + cells[j].radius
            if dist < min_dist:
                overlap = min_dist - dist
                direction = diff / (dist if dist > 0.1 else 0.1)
                push = direction * overlap * 0.15
                cells[i].vel += push
                cells[j].vel -= push
                
    # 2. Update cell positions and limit boundaries
    cx = SIZE[0] / 2
    cy = SIZE[1] / 2
    for c in cells:
        c.update()
        # Keep inside circular boundary
        diff_center = c.pos - np.array([cx, cy])
        dist_center = np.linalg.norm(diff_center)
        max_boundary = 450.0 - c.radius
        if dist_center > max_boundary:
            dir_in = -diff_center / (dist_center if dist_center > 0.1 else 0.1)
            c.pos = np.array([cx, cy]) - dir_in * max_boundary
            c.vel += dir_in * 0.8
            
    # 3. Cell division mechanism
    if num_cells < MAX_CELLS and py5.frame_count % 8 == 0:
        # Find a random cell that has reached target size and divide it
        candidates = [c for c in cells if c.radius >= 65.0]
        if candidates:
            parent = random.choice(candidates)
            # Create two daughter cells slightly offset
            angle = random.uniform(0.0, py5.TWO_PI)
            offset = parent.radius * 0.4
            ox = offset * np.cos(angle)
            oy = offset * np.sin(angle)
            
            # Shrink parent size back and create daughter
            parent.radius = 35.0
            parent.target_radius = 70.0
            parent.pos += np.array([ox, oy], dtype=np.float32)
            
            daughter = Cell(parent.pos[0] - 2*ox, parent.pos[1] - 2*oy, 35.0)
            daughter.target_radius = 70.0
            cells.append(daughter)
            
    # 4. Render cells with internal reaction-diffusion patterns
    t = py5.frame_count * 0.05
    for c in cells:
        # Draw outer cell membrane glow
        py5.stroke(139, 0, 255, 60)
        py5.stroke_weight(12)
        py5.no_fill()
        py5.circle(c.pos[0], c.pos[1], c.radius * 2)
        
        py5.stroke(255, 0, 127, 180)
        py5.stroke_weight(3)
        py5.circle(c.pos[0], c.pos[1], c.radius * 2)
        
        # Draw inner reaction-diffusion spots using concentric circles mapped to a pseudo-RD field
        num_inner = 8
        for k in range(num_inner):
            r_ratio = (k + 1) / num_inner
            inner_r = c.radius * r_ratio
            
            # Local mathematical simulation of reaction-diffusion waves inside the cell
            val = np.sin(r_ratio * py5.TWO_PI * 2.0 - t + c.phase) * np.cos(c.phase + t * 0.7)
            if val > 0.05:
                # Cyan active spots
                py5.stroke(0, 255, 255, int(150 * val))
                py5.stroke_weight(2)
                py5.circle(c.pos[0], c.pos[1], inner_r * 2)
                
                # Faint white peaks
                if val > 0.7:
                    py5.stroke(255, 255, 255, int(200 * (val - 0.7) / 0.3))
                    py5.stroke_weight(1.5)
                    py5.circle(c.pos[0], c.pos[1], inner_r * 2)
                    
    # Draw boundary cage
    py5.no_fill()
    py5.stroke(139, 0, 255, 25)
    py5.stroke_weight(20)
    py5.circle(cx, cy, 900)
    py5.stroke(255, 255, 255, 60)
    py5.stroke_weight(2)
    py5.circle(cx, cy, 900)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Progress feedback
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
