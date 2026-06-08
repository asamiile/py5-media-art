from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle data: x, y, z, vx, vy, vz, size
num_particles = 3000
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    for _ in range(num_particles):
        x = py5.random(-800, 800)
        y = py5.random(-800, 800)
        z = py5.random(-800, 800)
        vx = py5.random(-2, 2)
        vy = py5.random(-2, 2)
        vz = py5.random(-2, 2)
        sz = py5.random(5, 25)
        particles.append([x, y, z, vx, vy, vz, sz])

def draw():
    py5.background(240, 90, 5) # Dark void
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.3)
    
    # Draw central gravity well (black hole / glowing core)
    py5.push_matrix()
    py5.fill(280, 100, 100, 10)
    py5.sphere_detail(30)
    core_sz = 150 + py5.sin(t * 5) * 20
    py5.sphere(core_sz)
    py5.pop_matrix()
    
    for i, p in enumerate(particles):
        x, y, z, vx, vy, vz, sz = p
        
        # Gravity towards center
        dist_sq = x*x + y*y + z*z
        dist = py5.sqrt(dist_sq)
        if dist < 10: dist = 10 # prevent singularity
        
        force = 50000.0 / dist_sq
        fx = -x / dist * force
        fy = -y / dist * force
        fz = -z / dist * force
        
        # Swirl force (cross product with up vector)
        sx = -z / dist * force * 1.5
        sz_swirl = x / dist * force * 1.5
        
        # Update velocities
        vx += fx + sx
        vy += fy
        vz += fz + sz_swirl
        
        # Dampening
        vx *= 0.98
        vy *= 0.98
        vz *= 0.98
        
        x += vx
        y += vy
        z += vz
        
        particles[i] = [x, y, z, vx, vy, vz, sz]
        
        # Draw particle
        hue = (180 + py5.remap(dist, 0, 800, 0, 180) - py5.frame_count * 2) % 360
        py5.fill(hue, 90, 100, 80)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        # Orient particle along velocity vector
        vel_mag = py5.sqrt(vx*vx + vy*vy + vz*vz)
        if vel_mag > 0.1:
            # Simple hack to stretch along velocity: scale
            py5.scale(1, 1, 1 + vel_mag * 0.2)
            
        py5.box(sz)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES*100):.1f}%)")

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
