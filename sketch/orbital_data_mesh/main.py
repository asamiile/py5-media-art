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
SATELLITE_COUNT = 3000
SHELLS = [200, 300, 450]
PLANET_RADIUS = 180
STAR_COUNT = 4000

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global sats, stars
    sats = []
    for r in SHELLS:
        # Create satellites for each shell
        count = int(SATELLITE_COUNT * (r / sum(SHELLS)))
        theta = np.random.uniform(0, py5.PI, count)
        phi = np.random.uniform(0, py5.TWO_PI, count)
        speed = np.random.uniform(0.005, 0.02)
        sats.append({
            'r': r,
            'theta': theta,
            'phi': phi,
            'speed': speed,
            'phase': np.random.uniform(0, py5.TWO_PI, count)
        })
        
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    py5.background(0, 0, 5)
    
    time_val = py5.frame_count / 60.0
    
    # Camera
    cam_dist = 1000 + py5.sin(time_val * 0.2) * 100
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               300 * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Planet
    py5.push_matrix()
    py5.no_stroke()
    # Dark side with "city lights" (amber noise)
    py5.fill(10, 10, 20)
    py5.sphere(PLANET_RADIUS)
    
    # Atmosphere glow
    py5.blend_mode(py5.ADD)
    for i in range(2):
        r_glow = PLANET_RADIUS * (1.0 + i * 0.03)
        py5.fill(50, 50, 200, 20)
        py5.sphere(r_glow)
    py5.blend_mode(py5.BLEND)
    py5.pop_matrix()
    
    # 3. Orbital Mesh
    py5.blend_mode(py5.ADD)
    for shell in sats:
        r = shell['r']
        # Update phi
        shell['phi'] += shell['speed']
        
        # Calculate Cartesian positions
        theta = shell['theta']
        phi = shell['phi']
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        pos = np.stack([x, y, z], axis=1)
        
        # Render Satellites
        py5.stroke(255, 255, 255, 150)
        py5.stroke_weight(2)
        py5.points(pos)
        
        # Render Links (optimized neighbor search by index proximity)
        py5.stroke_weight(1)
        py5.stroke(0, 255, 255, 40)
        py5.begin_shape(py5.LINES)
        # We'll just link adjacent points in the array for a structured-but-random mesh look
        for i in range(len(pos) - 1):
            if i % 10 < 3: # Only draw some links to keep it light
                py5.vertex(*pos[i])
                py5.vertex(*pos[i+1])
            if (i + 5) < len(pos):
                py5.vertex(*pos[i])
                py5.vertex(*pos[i+5])
        py5.end_shape()
        
        # Random "Data Bursts"
        if py5.frame_count % 10 == 0:
            burst_idx = int(py5.random(len(pos)-5))
            py5.stroke(255, 255, 255, 200)
            py5.stroke_weight(2)
            py5.line(*pos[burst_idx], *pos[burst_idx+5])

    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "8M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
