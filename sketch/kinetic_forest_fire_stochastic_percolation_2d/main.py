from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid params
SIM_W = 480
SIM_H = 270
dt = 0.05

# Fields
biomass = np.zeros((SIM_H, SIM_W), dtype=np.float32)
temp = np.zeros((SIM_H, SIM_W), dtype=np.float32)
smoke = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Wind vector (downwind advection direction)
W_X = 1.6
W_Y = 0.8

# Heat & smoke diffusion rates
D_T = 0.4
D_S = 0.6
cooling = 0.5
smoke_decay = 0.3

# Palette
COLOR_VOID = np.array([4, 6, 8], dtype=np.float32) / 255.0         # Pitch black void
COLOR_FOREST = np.array([12, 60, 48], dtype=np.float32) / 255.0     # Deep Forest Teal
COLOR_FIRE_LOW = np.array([255, 45, 0], dtype=np.float32) / 255.0   # Crimson Red
COLOR_FIRE_HIGH = np.array([255, 230, 40], dtype=np.float32) / 255.0 # Golden Solar
COLOR_SMOKE = np.array([140, 145, 155], dtype=np.float32) / 255.0   # Ash Grey

# Mid frame memory for preview
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global biomass, temp
    # 1. Initialize biomass with Perlin-like clustered noise
    x = np.linspace(0, 10, SIM_W)
    y = np.linspace(0, 10, SIM_H)
    xv, yv = np.meshgrid(x, y)
    
    # Octave noise combination
    noise = (
        np.sin(xv) * np.cos(yv) * 0.5 +
        np.sin(xv * 2.3) * np.sin(yv * 1.8) * 0.25 +
        np.cos(xv * 5.5) * np.sin(yv * 4.2) * 0.125
    )
    biomass = np.clip((noise + 0.5) * 1.2, 0.1, 1.0)
    
    # 2. Ignite center
    cx, cy = SIM_W // 2, SIM_H // 2
    r = 12
    Y, X = np.ogrid[:SIM_H, :SIM_W]
    dist_sq = (X - cx)**2 + (Y - cy)**2
    temp[dist_sq <= r**2] = 2.0


def draw():
    global biomass, temp, smoke, img_rgb_mid
    
    # 1. Combustion physics
    # If temp is hot, burn biomass and release heat + smoke
    burn_mask = (temp > 0.15) & (biomass > 0.02)
    burn_rate = np.zeros_like(biomass)
    burn_rate[burn_mask] = 2.2 * biomass[burn_mask] * temp[burn_mask]
    
    biomass -= burn_rate * dt
    biomass = np.clip(biomass, 0.0, 1.0)
    
    temp += burn_rate * 4.8 * dt
    smoke += burn_rate * 2.8 * dt
    
    # 2. Diffusion (5-point Laplacian stencil)
    lap_T = (
        np.roll(temp, 1, axis=0) + np.roll(temp, -1, axis=0) +
        np.roll(temp, 1, axis=1) + np.roll(temp, -1, axis=1) - 4.0 * temp
    )
    lap_S = (
        np.roll(smoke, 1, axis=0) + np.roll(smoke, -1, axis=0) +
        np.roll(smoke, 1, axis=1) + np.roll(smoke, -1, axis=1) - 4.0 * smoke
    )
    
    # 3. Wind Advection (First-order upwind method)
    # Wind moves fields in positive direction, so we roll from -1 (left/top)
    adv_T = W_X * (temp - np.roll(temp, 1, axis=1)) + W_Y * (temp - np.roll(temp, 1, axis=0))
    adv_S = W_X * (smoke - np.roll(smoke, 1, axis=1)) + W_Y * (smoke - np.roll(smoke, 1, axis=0))
    
    # 4. Apply updates
    temp += (D_T * lap_T - adv_T) * dt - cooling * temp * dt
    smoke += (D_S * lap_S - adv_S) * dt - smoke_decay * smoke * dt
    
    temp = np.clip(temp, 0.0, 10.0)
    smoke = np.clip(smoke, 0.0, 5.0)
    
    # Add random spot ignitions (sparks / lightning strikes) occasionally
    if py5.frame_count % 120 == 0 and py5.frame_count < 800:
        rx = np.random.randint(20, SIM_W // 2)
        ry = np.random.randint(20, SIM_H - 20)
        temp[ry-3:ry+3, rx-3:rx+3] = 3.0
        
    # 5. Shading and color mixing
    # Base background blends biomass forest with burned void
    color_forest = biomass[:, :, None] * COLOR_FOREST + (1.0 - biomass[:, :, None]) * COLOR_VOID
    
    # Flame overlay mapping temperature to red -> orange -> golden yellow
    t_norm = np.clip(temp / 3.0, 0.0, 1.0)[:, :, None]
    color_fire = (1.0 - t_norm) * COLOR_FIRE_LOW + t_norm * COLOR_FIRE_HIGH
    
    # Blend forest, fire, and smoke advection
    fire_mask = (temp > 0.05)[:, :, None]
    pixel_colors = np.where(fire_mask, color_fire, color_forest)
    
    # Add smoke overlay
    smoke_mask = smoke[:, :, None]
    pixel_colors += smoke_mask * COLOR_SMOKE * 0.35
    
    # 6. Upscale to 4K
    pixel_colors_full = cv2.resize(pixel_colors, (SIZE[0], SIZE[1]), interpolation=cv2.INTER_LINEAR)
    img_rgb = (np.clip(pixel_colors_full, 0.0, 1.0) * 255.0).astype(np.uint8)
    
    if py5.frame_count == TOTAL_FRAMES // 2:
        img_rgb_mid = img_rgb.copy()
        
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = img_rgb[:, :, 0]
    py5.np_pixels[:, :, 1] = img_rgb[:, :, 1]
    py5.np_pixels[:, :, 2] = img_rgb[:, :, 2]
    py5.np_pixels[:, :, 3] = 255
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Security check: blank canvas detection
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
        
        # Save preview snapshot
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
