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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PHOTONS = 120000
NUM_TRACKS = 6

tracks = []
photons = None

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 100, 5)
    
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    global photons, tracks
    # [x, y, z, vx, vy, vz, age, active, px, py, pz]
    photons = np.zeros((NUM_PHOTONS, 11), dtype=np.float32)
    
    for i in range(NUM_TRACKS):
        reset_track(i, initial=True)

def reset_track(i, initial=False):
    global tracks
    y = np.random.uniform(-SIZE[1]/3, SIZE[1]/3)
    z = np.random.uniform(-1500, 500)
    vx = np.random.uniform(30, 60)
    
    # Start at different x positions initially
    if initial:
        x = np.random.uniform(-SIZE[0], SIZE[0]/2)
    else:
        x = -SIZE[0] - np.random.uniform(0, 500)
        
    track_dict = {'pos': np.array([x, y, z], dtype=np.float32), 'vel': np.array([vx, 0, 0], dtype=np.float32), 'active': True}
    
    if len(tracks) <= i:
        tracks.append(track_dict)
    else:
        tracks[i] = track_dict

def spawn_photons_for_track(track):
    global photons
    inactive = np.where(photons[:, 7] == 0)[0]
    num_to_spawn = min(len(inactive), 600)
    if num_to_spawn == 0:
        return
    
    indices = inactive[:num_to_spawn]
    
    # Cherenkov angle is cos(theta) = c / (v * n)
    angle = np.radians(45)
    
    speeds = np.random.uniform(8, 25, num_to_spawn)
    phi = np.random.uniform(0, 2 * np.pi, num_to_spawn)
    
    # The cone points opposite to velocity? No, Cherenkov cone points forward in the direction of motion.
    # Velocity is +x, cone opens backward from the particle? No, cone wavefronts form a V shape trailing the particle.
    # The photons are emitted at an angle to the direction of motion.
    # If particle moves +x, photons move in +x with some angle.
    vx = speeds * np.cos(angle)
    vy = speeds * np.sin(angle) * np.cos(phi)
    vz = speeds * np.sin(angle) * np.sin(phi)
    
    dx = np.random.uniform(-10, 0, num_to_spawn)
    dy = np.random.uniform(-2, 2, num_to_spawn)
    dz = np.random.uniform(-2, 2, num_to_spawn)
    
    px = track['pos'][0] + dx
    py_pos = track['pos'][1] + dy
    pz = track['pos'][2] + dz
    
    photons[indices, 0] = px
    photons[indices, 1] = py_pos
    photons[indices, 2] = pz
    photons[indices, 3] = vx
    photons[indices, 4] = vy
    photons[indices, 5] = vz
    photons[indices, 6] = np.random.uniform(30, 80, num_to_spawn)  # Age
    photons[indices, 7] = 1.0
    # previous pos
    photons[indices, 8] = px
    photons[indices, 9] = py_pos
    photons[indices, 10] = pz

def draw():
    global tracks, photons
    
    py5.background(240, 100, 5)
    py5.blend_mode(py5.ADD)
    
    # We don't translate so that we can use absolute coordinates easily, or we translate to center.
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Update and draw tracks
    py5.stroke(0, 0, 100, 100)
    py5.stroke_weight(3)
    for i, track in enumerate(tracks):
        px, py_pos, pz = track['pos']
        track['pos'] += track['vel']
        nx, ny, nz = track['pos']
        py5.line(px, py_pos, pz, nx, ny, nz)
        spawn_photons_for_track(track)
        
        if nx > SIZE[0]:
            reset_track(i)
            
    # Update photons
    active_idx = np.where(photons[:, 7] == 1)[0]
    if len(active_idx) > 0:
        # store previous
        photons[active_idx, 8:11] = photons[active_idx, 0:3]
        
        # update position
        photons[active_idx, 0] += photons[active_idx, 3]
        photons[active_idx, 1] += photons[active_idx, 4]
        photons[active_idx, 2] += photons[active_idx, 5]
        
        # apply drag
        photons[active_idx, 3:6] *= 0.95
        
        # age
        photons[active_idx, 6] -= 1.0
        
        # deactivate old
        dead_idx = active_idx[photons[active_idx, 6] <= 0]
        photons[dead_idx, 7] = 0
        
        # Draw active photons
        still_active = np.where(photons[:, 7] == 1)[0]
        if len(still_active) > 0:
            py5.stroke_weight(2)
            
            # Since py5.lines() can take a Nx6 array [x1, y1, z1, x2, y2, z2], let's construct it.
            # We will draw them in two batches based on age to give them different colors.
            
            ages = photons[still_active, 6]
            
            # Batch 1: Cyan (Electric Cyan)
            cyan_idx = still_active[ages > 40]
            if len(cyan_idx) > 0:
                py5.stroke(180, 100, 90, 80)
                lines_cyan = np.empty((len(cyan_idx), 6), dtype=np.float32)
                lines_cyan[:, 0:3] = photons[cyan_idx, 8:11]
                lines_cyan[:, 3:6] = photons[cyan_idx, 0:3]
                py5.lines(lines_cyan)
                
            # Batch 2: Blue (Reactor Blue)
            blue_idx = still_active[ages <= 40]
            if len(blue_idx) > 0:
                py5.stroke(220, 100, 80, 50)
                lines_blue = np.empty((len(blue_idx), 6), dtype=np.float32)
                lines_blue[:, 0:3] = photons[blue_idx, 8:11]
                lines_blue[:, 3:6] = photons[blue_idx, 0:3]
                py5.lines(lines_blue)

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
