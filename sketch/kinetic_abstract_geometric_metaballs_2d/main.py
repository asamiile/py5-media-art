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

# Grid resolution for evaluating the metaball field
W, H = 640, 360 
X, Y = np.meshgrid(np.linspace(0, SIZE[0], W), np.linspace(0, SIZE[1], H))
X_flat = X.flatten()
Y_flat = Y.flatten()

NUM_BALLS = 40
radii = np.random.uniform(50, 150, NUM_BALLS)
speeds = np.random.uniform(1.0, 4.0, NUM_BALLS)
phases = np.random.uniform(0, 2*np.pi, (NUM_BALLS, 2))
amplitudes = np.random.uniform(300, 800, (NUM_BALLS, 2))

# Centers
cx = np.zeros(NUM_BALLS)
cy = np.zeros(NUM_BALLS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    time_val = py5.frame_count * 0.015
    
    # Update metaball positions using Lissajous curves for smooth organic motion
    for i in range(NUM_BALLS):
        cx[i] = py5.width/2 + np.sin(time_val * speeds[i] + phases[i, 0]) * amplitudes[i, 0]
        cy[i] = py5.height/2 + np.cos(time_val * speeds[i] * 1.3 + phases[i, 1]) * amplitudes[i, 1]
    
    # Evaluate field: sum(r^2 / ((x-cx)^2 + (y-cy)^2))
    field = np.zeros(W * H)
    for i in range(NUM_BALLS):
        dist_sq = (X_flat - cx[i])**2 + (Y_flat - cy[i])**2
        # avoid division by zero
        dist_sq[dist_sq < 1.0] = 1.0
        field += (radii[i]**2) / dist_sq
    
    # Map field to colors
    # We create contours and glowing bands
    
    # To get nice bands, we can use a sine function on the field
    # field values are typically between 0.1 and 10.0
    
    # Smooth glowing effect
    # Hue maps to the field intensity, creating a rainbow liquid metal look
    hue = (field * 180.0 + time_val * 100.0) % 360.0
    
    # Brightness based on contours
    # sharp bands
    band = np.sin(field * 20.0 - time_val * 10.0)
    val = np.where(band > 0.8, 100, 20)
    val = np.where(field > 1.0, 100, val) # solid core
    
    sat = np.full_like(hue, 80)
    
    # Fade to black if field is very weak
    val = np.where(field < 0.2, val * (field / 0.2), val)
    
    # Convert HSB to ARGB
    h = hue / 60.0
    i = np.floor(h)
    f = h - i
    p = val * (1.0 - sat/100.0)
    q = val * (1.0 - sat/100.0 * f)
    t = val * (1.0 - sat/100.0 * (1.0 - f))
    
    i = (i % 6).astype(int)
    
    r = np.zeros_like(hue)
    g = np.zeros_like(hue)
    b = np.zeros_like(hue)
    
    r[i==0] = val[i==0]; g[i==0] = t[i==0]; b[i==0] = p[i==0]
    r[i==1] = q[i==1]; g[i==1] = val[i==1]; b[i==1] = p[i==1]
    r[i==2] = p[i==2]; g[i==2] = val[i==2]; b[i==2] = t[i==2]
    r[i==3] = p[i==3]; g[i==3] = q[i==3]; b[i==3] = val[i==3]
    r[i==4] = t[i==4]; g[i==4] = p[i==4]; b[i==4] = val[i==4]
    r[i==5] = val[i==5]; g[i==5] = p[i==5]; b[i==5] = q[i==5]
    
    R = (r * 2.55).astype(np.uint32)
    G_val = (g * 2.55).astype(np.uint32)
    B = (b * 2.55).astype(np.uint32)
    A = np.full_like(R, 255)
    
    pixels_argb = (A << 24) | (R << 16) | (G_val << 8) | B
    
    img = py5.create_image(W, H, py5.ARGB)
    img.load_pixels()
    img.pixels = pixels_argb
    img.update_pixels()
    
    py5.background(0)
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
