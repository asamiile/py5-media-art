import numpy as np
from pathlib import Path
import subprocess
import sys
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

# Simulation Parameters
NUM_DM = 120000
NUM_STARS = 4500
G_ATTR = 2.2
SOFTENING = 80.0

# State
dm_pos = None
dm_vel = None
starfield = None

def setup():
    global dm_pos, dm_vel, starfield
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    dm_pos = np.random.uniform(-1800, 1800, (NUM_DM, 3)).astype(np.float32)
    dm_vel = np.random.normal(0, 3.0, (NUM_DM, 3)).astype(np.float32)
    
    # Background Starfield
    sx = np.random.uniform(-py5.width*2.5, py5.width*2.5, NUM_STARS)
    sy = np.random.uniform(-py5.height*2.5, py5.height*2.5, NUM_STARS)
    sz = np.random.uniform(-6000, -2500, NUM_STARS) 
    sb = np.random.uniform(15, 75, NUM_STARS)
    starfield = np.stack([sx, sy, sz, sb], axis=-1).astype(np.float32)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global dm_pos, dm_vel
    
    # 1. Physics: Hub-based aggregation
    t = py5.frame_count * 0.012
    hubs = np.array([
        [700 * np.cos(t), 500 * np.sin(t*0.4), 300 * np.sin(t*0.8)],
        [-600 * np.sin(t*0.6), 400 * np.cos(t*0.7), -200 * np.cos(t)],
        [300 * np.cos(t*1.5), -700 * np.sin(t*0.3), 500 * np.cos(t*0.5)],
        [-200 * np.sin(t), 0, -800 * np.cos(t*0.4)],
        [800 * np.sin(t*0.2), 600 * np.cos(t*0.4), 0]
    ], dtype=np.float32)
    
    # Vectorized attraction to hubs
    for hub in hubs:
        diff = hub - dm_pos
        dist_sq = np.sum(diff**2, axis=-1) + SOFTENING**2
        dist = np.sqrt(dist_sq)
        dm_vel += (diff / dist[:, np.newaxis]) * G_ATTR
        
    dm_vel *= 0.94 
    dm_pos += dm_vel
    
    # 2. Render
    py5.background(0)
    
    # Background Starfield with Gravitational Lensing
    py5.push_matrix()
    py5.stroke_weight(1.2)
    for s in starfield:
        star_p = s[:3]
        lensing_offset = np.zeros(3, dtype=np.float32)
        # Lensing effect from hubs
        for hub in hubs:
            diff = hub - star_p
            d2 = np.sum(diff**2) + 20000.0
            lensing_offset += (diff / d2) * 80000.0
        
        py5.stroke(0, 0, s[3], 55)
        py5.point(s[0] + lensing_offset[0], s[1] + lensing_offset[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1200)
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_z(py5.frame_count * 0.0005)
    
    # Dark Matter Points
    speed = np.sqrt(np.sum(dm_vel**2, axis=-1))
    h = np.interp(speed, [0, 25], [280, 190]) # Violet to Cyan
    
    # Group by hue
    for hue_val in [190, 240, 280]:
        mask = (h >= hue_val - 30) & (h < hue_val + 30)
        if np.any(mask):
            py5.stroke(hue_val, 65, 90, 22) # Ghostly/Ethereal
            py5.stroke_weight(1.5)
            py5.points(dm_pos[mask])

    # Hub Halos (Soft volumetric glow)
    for hub in hubs:
        py5.push_matrix()
        py5.translate(*hub)
        for i in range(3):
            py5.no_stroke()
            py5.fill(275, 45, 100, 4 - i) # Very faint
            py5.sphere(150 + i*120)
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
