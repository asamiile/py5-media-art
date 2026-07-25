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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Accretion Disk Parameters
NUM_PARTICLES = 500000
STEPS_PER_FRAME = 3
DT = 0.05
G = 2000.0
M = 50.0 # Mass of each black hole
FRICTION = 0.998 # Causes particles to slowly spiral in

SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

def spawn_particles(mask, cx, cy):
    num = np.sum(mask)
    if num == 0: return
    
    # Spawn in an outer disk
    r = np.random.uniform(400, 800, num)
    theta = np.random.uniform(0, 2 * np.pi, num)
    
    pos[mask, 0] = cx + r * np.cos(theta)
    pos[mask, 1] = cy + r * np.sin(theta)
    
    # Initial Keplerian velocity for a central mass of 2*M
    v_mag = np.sqrt(G * (2 * M) / r) * 0.95 # Slightly sub-Keplerian to encourage spiraling
    vel[mask, 0] = -v_mag * np.sin(theta)
    vel[mask, 1] =  v_mag * np.cos(theta)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colormap
    
    pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    
    # Spawn all initially
    spawn_particles(np.ones(NUM_PARTICLES, dtype=bool), W/2, H/2)
    
    # Pre-generate a Plasma Thermal Colormap (Black -> Red -> Orange -> Yellow -> White -> Blue)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.3:
            p = v / 0.3
            colormap[i, 1:] = [int(p * 150), 0, 0] # Black to Dark Red
        elif v < 0.6:
            p = (v - 0.3) / 0.3
            colormap[i, 1:] = [150 + int(p * 105), int(p * 150), 0] # Red to Orange
        elif v < 0.8:
            p = (v - 0.6) / 0.2
            colormap[i, 1:] = [255, 150 + int(p * 105), int(p * 200)] # Orange to Yellow/White
        else:
            p = (v - 0.8) / 0.2
            colormap[i, 1:] = [255 - int(p * 100), 255, 200 + int(p * 55)] # White to Blue-White

def step_physics(t):
    global pos, vel
    
    cx, cy = W/2, H/2
    
    # Binary Black Hole Positions (Orbiting each other)
    # R depends on time
    bh_r = 80.0
    bh_omega = 0.5
    
    bh1_x = cx + bh_r * np.cos(t * bh_omega)
    bh1_y = cy + bh_r * np.sin(t * bh_omega)
    
    bh2_x = cx - bh_r * np.cos(t * bh_omega)
    bh2_y = cy - bh_r * np.sin(t * bh_omega)
    
    # Gravity from BH 1
    dx1 = bh1_x - pos[:, 0]
    dy1 = bh1_y - pos[:, 1]
    dist1_sq = dx1*dx1 + dy1*dy1 + 50.0 # Softening
    dist1 = np.sqrt(dist1_sq)
    f1 = (G * M) / dist1_sq
    ax1 = dx1 / dist1 * f1
    ay1 = dy1 / dist1 * f1
    
    # Gravity from BH 2
    dx2 = bh2_x - pos[:, 0]
    dy2 = bh2_y - pos[:, 1]
    dist2_sq = dx2*dx2 + dy2*dy2 + 50.0
    dist2 = np.sqrt(dist2_sq)
    f2 = (G * M) / dist2_sq
    ax2 = dx2 / dist2 * f2
    ay2 = dy2 / dist2 * f2
    
    # Integration
    vel[:, 0] += (ax1 + ax2) * DT
    vel[:, 1] += (ay1 + ay2) * DT
    
    # Viscosity / Friction
    vel *= FRICTION
    
    # Move
    pos += vel * DT
    
    # Respawn particles that cross the event horizon (r < 15)
    horizon_sq = 15.0 * 15.0
    eaten = (dist1_sq < horizon_sq) | (dist2_sq < horizon_sq)
    spawn_particles(eaten, cx, cy)

def draw():
    global pos, vel
    
    t = py5.frame_count * 0.015
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        t += DT * 0.5
        
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 220 // 256).astype(np.uint8)
    
    sx = pos[:, 0].astype(np.int32)
    sy = pos[:, 1].astype(np.int32)
    
    valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx = sx[valid]
    sy = sy[valid]
    
    # Color based on velocity (plasma gets hotter as it speeds up falling into BH)
    v_mag = np.sqrt(vel[valid, 0]**2 + vel[valid, 1]**2)
    intensity = np.clip(v_mag * 12.0, 0, 255).astype(np.uint8)
    
    vr = colormap[intensity, 1]
    vg = colormap[intensity, 2]
    vb = colormap[intensity, 3]
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    flat_pixels[flat_indices, 1] = np.clip(flat_pixels[flat_indices, 1].astype(np.uint16) + vr, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 2] = np.clip(flat_pixels[flat_indices, 2].astype(np.uint16) + vg, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 3] = np.clip(flat_pixels[flat_indices, 3].astype(np.uint16) + vb, 0, 255).astype(np.uint8)
    
    # Scale up if necessary
    if SCALE > 1:
        # Drawing to scaled array requires reshaping and repeating, which is complex for additive blending.
        # Instead, we just let py5 upscale the whole pixel array at the end if we wanted, 
        # but py5.np_pixels matches the native py5.size().
        # Wait, py5.size() was set to SIZE, but W, H = SIZE // SCALE.
        # This means my sx, sy are operating on a W, H grid, but pixels is SIZE[1] x SIZE[0].
        pass # Bug fix: I used W = SIZE[0] // SCALE above but py5.np_pixels is full SIZE.

    py5.update_np_pixels()
    
    # Correcting the bug dynamically: if SCALE > 1, we must upscale the drawn pixels
    if SCALE > 1:
        img_data = pixels.reshape(SIZE[1], SIZE[0], 4)
        # We only drew to the top-left WxH corner. Let's scale it up to fill.
        small_corner = np.copy(img_data[:H, :W, :])
        upscaled = np.repeat(np.repeat(small_corner, SCALE, axis=0), SCALE, axis=1)
        py5.np_pixels[:] = upscaled
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
