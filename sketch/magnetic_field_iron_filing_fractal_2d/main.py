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

NUM_PARTICLES = 40000
particles = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    # [x, y, age, max_age]
    particles = np.zeros((NUM_PARTICLES, 4), dtype=np.float32)
    for i in range(NUM_PARTICLES):
        spawn_particle(i)
        particles[i, 2] = np.random.rand() * particles[i, 3] # Randomize starting age

def spawn_particle(i):
    particles[i, 0] = np.random.rand() * SIZE[0]
    particles[i, 1] = np.random.rand() * SIZE[1]
    particles[i, 2] = 0
    particles[i, 3] = 20 + np.random.rand() * 40

def dipole_field(x, y, m_pos, m_vec):
    # m_pos is (2,) position of dipole, m_vec is (2,) magnetic moment vector
    r_vec = np.array([x - m_pos[0], y - m_pos[1]])
    r_mag = np.linalg.norm(r_vec) + 1e-5
    r_hat = r_vec / r_mag
    
    # B = (3(m.r_hat)r_hat - m) / r^3
    m_dot_r = np.dot(m_vec, r_hat)
    b_vec = (3 * m_dot_r * r_hat - m_vec) / (r_mag**3)
    return b_vec * 1e7 # scale factor

def draw():
    global particles
    
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(255, 255, 255, 15)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    time_val = py5.frame_count * 0.02
    
    # Two rotating dipoles
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    m1_pos = np.array([cx + np.cos(time_val * 0.5) * 400, cy + np.sin(time_val * 0.5) * 400])
    m1_vec = np.array([np.cos(time_val), np.sin(time_val)])
    
    m2_pos = np.array([cx + np.cos(time_val * 0.7 + py5.PI) * 400, cy + np.sin(time_val * 0.7 + py5.PI) * 400])
    m2_vec = np.array([np.cos(-time_val * 1.3), np.sin(-time_val * 1.3)])
    
    py5.blend_mode(py5.MULTIPLY)
    py5.stroke(0, 0, 0, 40)
    py5.stroke_weight(1.5)
    
    # Update and draw particles
    for i in range(NUM_PARTICLES):
        px = particles[i, 0]
        py = particles[i, 1]
        
        # Calculate magnetic field
        b1 = dipole_field(px, py, m1_pos, m1_vec)
        b2 = dipole_field(px, py, m2_pos, m2_vec)
        b_total = b1 + b2
        
        # Normalize and use as velocity
        b_mag = np.linalg.norm(b_total) + 1e-5
        vx = (b_total[0] / b_mag) * 8.0
        vy = (b_total[1] / b_mag) * 8.0
        
        # Noise turbulence
        nx = py5.os_noise(px*0.002, py*0.002, time_val) * 2 - 1
        ny = py5.os_noise(px*0.002 + 100, py*0.002 + 100, time_val) * 2 - 1
        
        vx += nx * 1.5
        vy += ny * 1.5
        
        next_x = px + vx
        next_y = py + vy
        
        py5.line(px, py, next_x, next_y)
        
        particles[i, 0] = next_x
        particles[i, 1] = next_y
        particles[i, 2] += 1
        
        # Respawn if old or off screen
        if (particles[i, 2] >= particles[i, 3] or 
            next_x < 0 or next_x > SIZE[0] or 
            next_y < 0 or next_y > SIZE[1]):
            spawn_particle(i)

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
