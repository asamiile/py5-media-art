from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
# 高速化のため10秒に変更
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# パラメータの最適化
GRID_SIZE = 128
NUM_PARTICLES = 40_000 
NUM_STARS = 5_000

# State
psi = np.zeros((GRID_SIZE, GRID_SIZE), dtype=complex)
particles = np.zeros((NUM_PARTICLES, 3), dtype=float)
velocities = np.zeros((NUM_PARTICLES, 3), dtype=float)
stars = np.zeros((NUM_STARS, 3), dtype=float)

def setup():
    global psi, particles, stars
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

    # 初期化
    r, i = np.random.normal(0, 0.2, (2, GRID_SIZE, GRID_SIZE))
    psi[:] = r + 1j * i
    particles[:, 0] = np.random.uniform(-SIZE[0]//2, SIZE[0]//2, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(-SIZE[1]//2, SIZE[1]//2, NUM_PARTICLES)
    particles[:, 2] = np.random.uniform(0, 800, NUM_PARTICLES)
    stars[:, 0] = np.random.uniform(-SIZE[0]//2, SIZE[0]//2, NUM_STARS)
    stars[:, 1] = np.random.uniform(-SIZE[1]//2, SIZE[1]//2, NUM_STARS)
    stars[:, 2] = np.random.uniform(800, 1500, NUM_STARS)

def evolve_field():
    global psi
    lap = np.roll(psi,1,0)+np.roll(psi,-1,0)+np.roll(psi,1,1)+np.roll(psi,-1,1)-4*psi
    dt = 0.05
    psi += dt * (lap + psi * (1.0 - np.abs(psi)**2))
    psi += 0.01 * (np.random.normal(0,1,psi.shape)+1j*np.random.normal(0,1,psi.shape))

def get_vel(pos):
    gx = ((pos[:,0]+SIZE[0]//2)/SIZE[0]*(GRID_SIZE-1)).astype(int)%(GRID_SIZE-1)
    gy = ((pos[:,1]+SIZE[1]//2)/SIZE[1]*(GRID_SIZE-1)).astype(int)%(GRID_SIZE-1)
    p = psi[gy, gx]
    grad_x = psi[gy, (gx+1)%GRID_SIZE] - p
    grad_y = psi[(gy+1)%GRID_SIZE, gx] - p
    msq = np.abs(p)**2 + 0.1
    return np.imag(np.conj(p)*grad_x)/msq, np.imag(np.conj(p)*grad_y)/msq, p

def project(pos):
    f = 600 / (600 + pos[:, 2])
    return pos[:, 0]*f + SIZE[0]//2, pos[:, 1]*f + SIZE[1]//2, f

def draw():
    global particles, velocities
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    # Stars (高速化のためまとめて描画)
    sx, sy, sf = project(stars)
    py5.stroke(255, 60); py5.stroke_weight(1)
    py5.points(np.stack([sx, sy], axis=1))

    evolve_field()
    vx, vy, p_f = get_vel(particles)
    
    # 物理演算の最適化
    ang = np.arctan2(particles[:, 1], particles[:, 0])
    velocities[:, 0] = velocities[:, 0]*0.85 + vx*6.0 - np.sin(ang)*1.2
    velocities[:, 1] = velocities[:, 1]*0.85 + vy*6.0 + np.cos(ang)*1.2
    velocities[:, 2] = velocities[:, 2]*0.9 + np.sin(np.angle(p_f)+py5.frame_count*0.1)*3.0
    particles += velocities
    
    # Wrap
    particles[particles[:,0]>SIZE[0]//2,0]-=SIZE[0]; particles[particles[:,0]<-SIZE[0]//2,0]+=SIZE[0]
    particles[particles[:,1]>SIZE[1]//2,1]-=SIZE[1]; particles[particles[:,1]<-SIZE[1]//2,1]+=SIZE[1]
    particles[particles[:,2]>800,2]-=800; particles[particles[:,2]<0,2]+=800
    
    # Rendering (バッチ処理で高速化)
    px, py, pf = project(particles)
    phase = np.angle(p_f)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for b in range(4):
        mask = (b*np.pi/2 - np.pi <= phase) & (phase < (b+1)*np.pi/2 - np.pi)
        if not np.any(mask): continue
        h = (py5.remap(b, 0, 4, 35, 235) + py5.frame_count*0.1)%360
        py5.stroke(h, 85, 100, 30); py5.stroke_weight(1.8)
        py5.points(np.stack([px[mask], py[mask]], axis=1))
            
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 100 == 0:
        print(f"Progress: {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", "60", "-i", str(FRAMES_DIR / "frame-%04d.png"),
                       "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "faster",
                       str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{TOTAL_FRAMES//2:04d}.png"), 
                       str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print("Completed.")

py5.run_sketch()
