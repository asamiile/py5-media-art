from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Internal resolution
W = 1920
H = 1080

NUM_BALLS = 30
pos = None
vel = None
radii_sq = None

grid_x = None
grid_y = None

def setup():
    global pos, vel, radii_sq, grid_x, grid_y
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize balls
    x = np.random.uniform(200, W - 200, NUM_BALLS)
    y = np.random.uniform(200, H - 200, NUM_BALLS)
    pos = np.column_stack((x, y))
    
    angle = np.random.uniform(0, np.pi * 2, NUM_BALLS)
    speed = np.random.uniform(1.0, 4.0, NUM_BALLS)
    vel = np.column_stack((np.cos(angle) * speed, np.sin(angle) * speed))
    
    radii = np.random.uniform(40, 160, NUM_BALLS)
    radii_sq = (radii ** 2).astype(np.float32)
    
    grid_x, grid_y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

def draw():
    global pos, vel
    
    # Update positions
    pos += vel
    
    # Bounce
    mask_x = (pos[:, 0] < 50) | (pos[:, 0] > W - 50)
    mask_y = (pos[:, 1] < 50) | (pos[:, 1] > H - 50)
    vel[mask_x, 0] *= -1
    vel[mask_y, 1] *= -1
    
    # Add a slight gravitational pull to the center to keep them clumped sometimes
    center = np.array([W/2, H/2])
    to_center = center - pos
    dist = np.linalg.norm(to_center, axis=1, keepdims=True) + 1.0
    vel += (to_center / dist) * 0.05
    
    # Calculate energy field
    energy = np.zeros((H, W), dtype=np.float32)
    
    for i in range(NUM_BALLS):
        dx = grid_x - pos[i, 0]
        dy = grid_y - pos[i, 1]
        dist_sq = dx*dx + dy*dy + 1.0
        energy += radii_sq[i] / dist_sq
        
    # Map energy to colors
    # We want a sharp threshold for the membrane, and a gradient for the glow
    # Energy ranges from ~0 to ~10. The boundary is at 1.0
    
    # c_b, c_g, c_r
    # Deep Indigo background (#11001C)
    # Glow Cyan (#00F0FF)
    # Membrane Purple (#4A00E0)
    # Core Pink (#FF007F)
    
    r = np.full((H, W), 17, dtype=np.uint8)
    g = np.full((H, W), 0, dtype=np.uint8)
    b_c = np.full((H, W), 28, dtype=np.uint8)
    
    # Masks
    # Glow: 0.3 to 1.0
    m_glow = (energy > 0.3) & (energy <= 1.0)
    f_glow = (energy[m_glow] - 0.3) / 0.7
    r[m_glow] = 17 + (0 - 17) * f_glow
    g[m_glow] = 0 + (240 - 0) * f_glow
    b_c[m_glow] = 28 + (255 - 28) * f_glow
    
    # Membrane: 1.0 to 1.2
    m_mem = (energy > 1.0) & (energy <= 1.2)
    f_mem = (energy[m_mem] - 1.0) / 0.2
    r[m_mem] = 0 + (74 - 0) * f_mem
    g[m_mem] = 240 + (0 - 240) * f_mem
    b_c[m_mem] = 255 + (224 - 255) * f_mem
    
    # Core: 1.2 to 2.5
    m_core = (energy > 1.2) & (energy <= 2.5)
    f_core = (energy[m_core] - 1.2) / 1.3
    r[m_core] = 74 + (255 - 74) * f_core
    g[m_core] = 0 + (0 - 0) * f_core
    b_c[m_core] = 224 + (127 - 224) * f_core
    
    # Deep Core: > 2.5
    m_deep = energy > 2.5
    r[m_deep] = 255
    g[m_deep] = 0
    b_c[m_deep] = 127
    
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    pixels[..., 0] = b_c
    pixels[..., 1] = g
    pixels[..., 2] = r
    pixels[..., 3] = 255
    
    img = py5.create_image_from_numpy(pixels, "ARGB")
    
    # Draw stretched to fill 4K screen
    py5.image(img, 0, 0, py5.width, py5.height)
    
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
