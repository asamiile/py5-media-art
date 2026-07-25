from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import map_coordinates

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
W, H = SIZE

# LBM Parameters
SCALE = 3
W_sim, H_sim = W // SCALE, H // SCALE

NUM_PARTICLES = 1000000
STEPS_PER_FRAME = 6
OMEGA = 1.85 # Relaxation time (high = lower viscosity)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global f, e, w, opp, obstacle, u, v, p_pos, colormap
    
    # D2Q9 LBM constants
    e = np.array([[0,0], [1,0], [0,1], [-1,0], [0,-1], [1,1], [-1,1], [-1,-1], [1,-1]], dtype=np.int32)
    w = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36], dtype=np.float32)
    opp = [0, 3, 4, 1, 2, 7, 8, 5, 6]
    
    # Init distributions
    f = np.zeros((9, H_sim, W_sim), dtype=np.float32)
    for i in range(9):
        f[i] = w[i]
        
    u = np.zeros((H_sim, W_sim), dtype=np.float32)
    v = np.zeros((H_sim, W_sim), dtype=np.float32)
    
    # Define obstacles (Three cylinders)
    y, x = np.mgrid[0:H_sim, 0:W_sim]
    c1 = (x - W_sim * 0.2)**2 + (y - H_sim * 0.5)**2 < 25**2
    c2 = (x - W_sim * 0.4)**2 + (y - H_sim * 0.3)**2 < 15**2
    c3 = (x - W_sim * 0.4)**2 + (y - H_sim * 0.7)**2 < 15**2
    obstacle = c1 | c2 | c3
    
    # Init particles
    p_pos = np.random.uniform(0, 1, (NUM_PARTICLES, 2)).astype(np.float32)
    p_pos[:, 0] *= W
    p_pos[:, 1] *= H
    
    # Fluid Dynamics Colormap (Deep Blue -> Cyan -> Yellow/Orange for high velocity)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        val = i / 255.0
        colormap[i, 0] = 255
        if val < 0.33:
            p = val / 0.33
            colormap[i, 1:] = [0, int(p * 150), 50 + int(p * 205)]
        elif val < 0.66:
            p = (val - 0.33) / 0.33
            colormap[i, 1:] = [int(p * 255), 150 + int(p * 105), 255 - int(p * 255)]
        else:
            p = (val - 0.66) / 0.34
            colormap[i, 1:] = [255, 255 - int(p * 155), 0]

def step_physics():
    global f, u, v, p_pos
    
    # 1. Stream
    for i in range(9):
        f[i] = np.roll(f[i], e[i,0], axis=1)
        f[i] = np.roll(f[i], e[i,1], axis=0)
        
    # 2. Bounce-back boundary conditions (Obstacles)
    bndryF = f.copy()
    for i in range(9):
        f[i, obstacle] = bndryF[opp[i], obstacle]
        
    # 3. Inlet boundary condition (Constant wind from left)
    # To maintain mass, we just inject equilibrium distribution at the left edge
    inlet_u = 0.12
    inlet_v = 0.0
    u_sq = inlet_u**2 + inlet_v**2
    for i in range(9):
        cu = e[i,0]*inlet_u + e[i,1]*inlet_v
        feq = w[i] * (1.0 + 3.0*cu + 4.5*cu**2 - 1.5*u_sq)
        f[i, :, 0] = feq
        
    # 4. Macroscopic variables
    rho = np.sum(f, axis=0)
    u = np.sum(f * e[:,0,None,None], axis=0) / rho
    v = np.sum(f * e[:,1,None,None], axis=0) / rho
    
    # Ensure zero velocity inside obstacles
    u[obstacle] = 0.0
    v[obstacle] = 0.0
    
    # 5. Collision (BGK)
    u_sq = u**2 + v**2
    inv_obstacle = ~obstacle
    
    for i in range(9):
        cu = e[i,0]*u + e[i,1]*v
        feq = rho * w[i] * (1.0 + 3.0*cu + 4.5*cu**2 - 1.5*u_sq)
        # Relax only non-obstacle nodes
        f[i, inv_obstacle] = (f[i, inv_obstacle] * (1.0 - OMEGA) + feq[inv_obstacle] * OMEGA)
        
    # 6. Advect Particles
    p_y_sim = p_pos[:, 1] / SCALE
    p_x_sim = p_pos[:, 0] / SCALE
    
    p_u = map_coordinates(u, [p_y_sim, p_x_sim], mode='wrap', order=1)
    p_v = map_coordinates(v, [p_y_sim, p_x_sim], mode='wrap', order=1)
    
    p_pos[:, 0] = (p_pos[:, 0] + p_u * SCALE * 10.0) % W
    p_pos[:, 1] = (p_pos[:, 1] + p_v * SCALE * 10.0) % H

def draw():
    global p_pos, u, v
    
    for _ in range(STEPS_PER_FRAME):
        step_physics()
        
    py5.load_np_pixels()
    
    # Motion blur fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    
    # Color particles based on fluid velocity magnitude
    speed = np.hypot(u, v)
    
    p_y_sim = p_pos[:, 1] / SCALE
    p_x_sim = p_pos[:, 0] / SCALE
    p_speed = map_coordinates(speed, [p_y_sim, p_x_sim], mode='wrap', order=1)
    
    # Map speed (0 to ~0.15) to colormap (0 to 255)
    normalized_speed = np.clip(p_speed / 0.15, 0.0, 1.0)
    color_indices = (normalized_speed * 255).astype(np.uint8)
    
    sx = p_pos[:, 0].astype(np.int32)
    sy = p_pos[:, 1].astype(np.int32)
    
    valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx = sx[valid]
    sy = sy[valid]
    c_idx = color_indices[valid]
    
    colors = colormap[c_idx]
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    np.add.at(flat_pixels[:, 1], flat_indices, colors[:, 1])
    np.add.at(flat_pixels[:, 2], flat_indices, colors[:, 2])
    np.add.at(flat_pixels[:, 3], flat_indices, colors[:, 3])
    
    # Clamp to 255
    flat_pixels[:, 1:] = np.clip(flat_pixels[:, 1:], 0, 255)
    
    # Dim the obstacle regions to show the cylinders clearly
    # Map obstacle back to screen resolution
    obs_screen = np.repeat(np.repeat(obstacle, SCALE, axis=0), SCALE, axis=1)
    
    # Ensure dimensions match (in case SCALE doesn't perfectly divide)
    obs_screen = obs_screen[:H, :W]
    flat_pixels = pixels.reshape(H, W, 4)
    flat_pixels[obs_screen, 1:] = 0
    
    py5.update_np_pixels()

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
        import os
        os._exit(0)

py5.run_sketch()
