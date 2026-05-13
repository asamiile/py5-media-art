import numpy as np
import py5
from pathlib import Path
import subprocess
import sys

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 80000

# Particle state: [x, y, z, loop_idx, u, speed, active]
particles = np.zeros((NUM_PARTICLES, 7), dtype=np.float32)

# Loop parameters
NUM_LOOPS = 8
# loops: [x, y, z, height, radius, angle, twist, state]
loops = np.zeros((NUM_LOOPS, 8), dtype=np.float32)

# Reconnection burst particles
NUM_BURST = 20000
burst_particles = np.zeros((NUM_BURST, 7), dtype=np.float32) # [x, y, z, vx, vy, vz, life]

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    global particles, loops
    
    for i in range(NUM_LOOPS):
        loops[i, 0] = np.random.uniform(-300, 300)
        loops[i, 1] = 300 # base y
        loops[i, 2] = np.random.uniform(-300, 300)
        loops[i, 3] = np.random.uniform(500, 1000) # height
        loops[i, 4] = np.random.uniform(300, 600) # radius
        loops[i, 5] = np.random.uniform(0, np.pi) # angle
        loops[i, 6] = 0.0 # twist
        loops[i, 7] = 0.0 # state (0=normal, 1=reconnecting)
        
    particles[:, 3] = np.random.randint(0, NUM_LOOPS, NUM_PARTICLES)
    particles[:, 4] = np.random.uniform(0, np.pi, NUM_PARTICLES)
    particles[:, 5] = np.random.uniform(0.005, 0.02, NUM_PARTICLES)
    particles[:, 6] = 1.0

def get_loop_pos(loop, u):
    x = loop[0] + loop[4] * np.cos(u) * np.cos(loop[5])
    z = loop[2] + loop[4] * np.cos(u) * np.sin(loop[5])
    y = loop[1] - loop[3] * np.sin(u)
    
    twist = loop[6] * np.sin(u)
    tx = x * np.cos(twist) - z * np.sin(twist)
    tz = x * np.sin(twist) + z * np.cos(twist)
    
    return tx, y, tz

def draw():
    global particles, loops, burst_particles
    
    py5.background(280, 80, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200, 0)
    py5.rotate_y(py5.frame_count * 0.004)
    py5.rotate_x(0.2) # slight downward angle
    
    # Draw solar surface glow
    py5.push_matrix()
    py5.translate(0, 300, 0)
    py5.rotate_x(np.pi/2)
    py5.no_stroke()
    py5.fill(30, 100, 30, 10)
    py5.circle(0, 0, 1500)
    py5.fill(15, 100, 50, 20)
    py5.circle(0, 0, 800)
    py5.pop_matrix()
    
    # Update loops
    for i in range(NUM_LOOPS):
        # Driven by a complex sine wave to make twisting dynamic
        t = py5.frame_count * 0.01 + i * 2.1
        loops[i, 6] = (np.sin(t) + np.sin(t * 1.5) * 0.5) * 1.8
        
        # Trigger reconnection
        if abs(loops[i, 6]) > 2.2 and loops[i, 7] == 0:
            loops[i, 7] = 1.0
            inactive = np.where(burst_particles[:, 6] <= 0)[0]
            spawn_count = min(len(inactive), 4000)
            if spawn_count > 0:
                idx = inactive[:spawn_count]
                bx, by, bz = get_loop_pos(loops[i], np.pi/2)
                burst_particles[idx, 0] = bx
                burst_particles[idx, 1] = by
                burst_particles[idx, 2] = bz
                
                speeds = np.random.uniform(15, 60, spawn_count)
                phi = np.random.uniform(0, 2*np.pi, spawn_count)
                theta = np.random.uniform(0, np.pi, spawn_count)
                burst_particles[idx, 3] = speeds * np.sin(theta) * np.cos(phi)
                burst_particles[idx, 4] = speeds * np.cos(theta)
                burst_particles[idx, 5] = speeds * np.sin(theta) * np.sin(phi)
                burst_particles[idx, 6] = 100.0 # life
                
        elif abs(loops[i, 6]) < 1.0:
            loops[i, 7] = 0.0
            
    # Update particles
    particles[:, 4] += particles[:, 5]
    
    reset_mask = particles[:, 4] > np.pi
    particles[reset_mask, 4] = 0
    particles[reset_mask, 3] = np.random.randint(0, NUM_LOOPS, np.sum(reset_mask))
    
    pts = np.empty((NUM_PARTICLES, 3), dtype=np.float32)
    
    l_idx = particles[:, 3].astype(int)
    u = particles[:, 4]
    
    L_x = loops[l_idx, 0]
    L_y = loops[l_idx, 1]
    L_z = loops[l_idx, 2]
    L_h = loops[l_idx, 3]
    L_r = loops[l_idx, 4]
    L_a = loops[l_idx, 5]
    L_t = loops[l_idx, 6]
    
    cx = L_x + L_r * np.cos(u) * np.cos(L_a)
    cz = L_z + L_r * np.cos(u) * np.sin(L_a)
    cy = L_y - L_h * np.sin(u)
    
    twist = L_t * np.sin(u)
    
    pts[:, 0] = cx * np.cos(twist) - cz * np.sin(twist)
    pts[:, 1] = cy
    pts[:, 2] = cx * np.sin(twist) + cz * np.cos(twist)
    
    # Structural noise
    pts += np.random.normal(0, 8, pts.shape)
    
    # Batch draw by loop state
    normal_mask = loops[l_idx, 7] == 0
    reconn_mask = loops[l_idx, 7] == 1
    
    if np.any(normal_mask):
        py5.stroke(30, 100, 80, 40)
        py5.stroke_weight(2.5)
        py5.points(pts[normal_mask])
        
    if np.any(reconn_mask):
        py5.stroke(280, 100, 90, 80)
        py5.stroke_weight(3)
        py5.points(pts[reconn_mask])
        
    # Draw core
    py5.stroke(50, 20, 100, 60)
    py5.stroke_weight(1)
    py5.points(pts)
    
    # Burst particles
    active_burst = burst_particles[:, 6] > 0
    if np.any(active_burst):
        burst_particles[active_burst, 0:3] += burst_particles[active_burst, 3:6]
        burst_particles[active_burst, 3:6] *= 0.96 
        burst_particles[active_burst, 6] -= 2.5
        
        b_pts = burst_particles[active_burst, 0:3]
        ages = burst_particles[active_burst, 6]
        
        # Draw bursts with varying colors
        b1 = b_pts[ages > 60]
        b2 = b_pts[ages <= 60]
        
        if len(b1) > 0:
            py5.stroke(50, 20, 100, 100)
            py5.stroke_weight(5)
            py5.points(b1)
            
        if len(b2) > 0:
            py5.stroke(280, 100, 90, 60)
            py5.stroke_weight(3)
            py5.points(b2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
