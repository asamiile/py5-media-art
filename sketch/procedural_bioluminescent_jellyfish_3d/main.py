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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Tentacle:
    def __init__(self, start_pos, length, num_segments):
        self.segments = [np.array(start_pos)]
        for i in range(1, num_segments):
            self.segments.append(np.array(start_pos) + np.array([0, i * (length/num_segments), 0]))
        self.velocities = [np.zeros(3) for _ in range(num_segments)]
        self.rest_length = length / num_segments

    def update(self, base_pos, time_t):
        self.segments[0] = base_pos
        for i in range(1, len(self.segments)):
            diff = self.segments[i-1] - self.segments[i]
            dist = np.linalg.norm(diff)
            force = (dist - self.rest_length) * 0.2
            dir_vec = diff / (dist + 1e-5)
            
            # Hooke's law
            self.velocities[i] += dir_vec * force
            
            # Water drag
            self.velocities[i] *= 0.85
            
            # Sine wave sway
            sway_force = np.array([np.sin(time_t * 2 + i * 0.2) * 2, 0, np.cos(time_t * 1.5 + i * 0.3) * 2])
            self.velocities[i] += sway_force
            
            # Upward propulsion from bell
            if i > 0:
                self.velocities[i] += np.array([0, -0.5 * np.sin(time_t * 3), 0])
                
            self.segments[i] += self.velocities[i]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global tentacles, num_tentacles, num_segments
    num_tentacles = 24
    num_segments = 30
    tentacles = []
    
    for i in range(num_tentacles):
        angle = (i / num_tentacles) * 2 * np.pi
        r = 150
        base_x = np.cos(angle) * r
        base_z = np.sin(angle) * r
        tentacles.append(Tentacle([base_x, 0, base_z], 600, num_segments))

def draw():
    py5.background(10, 20, 10)
    
    py5.push_matrix()
    t = py5.frame_count * 0.02
    
    # Smooth swim motion
    swim_y = py5.height / 2 + np.sin(t * 3) * 100
    py5.translate(py5.width / 2, swim_y - 200, 0)
    
    py5.rotate_y(t * 0.5)
    py5.rotate_z(np.sin(t * 1.2) * 0.1)
    py5.rotate_x(np.cos(t * 0.8) * 0.1)
    
    # Draw Bell
    num_lats = 20
    num_lons = 40
    pulse = 1.0 + np.sin(t * 3) * 0.3
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(num_lats - 1):
        lat1 = (i / num_lats) * (py5.PI / 2)
        lat2 = ((i+1) / num_lats) * (py5.PI / 2)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(num_lons + 1):
            lon = (j / num_lons) * py5.TWO_PI
            
            r1 = 300 * pulse * np.cos(lat1)
            y1 = -300 * np.sin(lat1)
            x1 = r1 * np.cos(lon)
            z1 = r1 * np.sin(lon)
            
            r2 = 300 * pulse * np.cos(lat2)
            y2 = -300 * np.sin(lat2)
            x2 = r2 * np.cos(lon)
            z2 = r2 * np.sin(lon)
            
            hue = (200 + i * 2 + t * 20) % 360
            py5.stroke(hue, 80, 100, 50)
            
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
        py5.end_shape()

    # Draw and update tentacles
    py5.stroke_weight(4)
    for i, tnt in enumerate(tentacles):
        angle = (i / num_tentacles) * py5.TWO_PI
        base_r = 150 * pulse
        base_x = np.cos(angle) * base_r
        base_z = np.sin(angle) * base_r
        
        tnt.update(np.array([base_x, 0, base_z]), t)
        
        py5.begin_shape(py5.LINE_STRIP)
        for j, seg in enumerate(tnt.segments):
            hue = (180 + j * 3 + t * 20) % 360
            py5.stroke(hue, 90, 100, 70 - j*2)
            py5.vertex(*seg)
        py5.end_shape()

    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
