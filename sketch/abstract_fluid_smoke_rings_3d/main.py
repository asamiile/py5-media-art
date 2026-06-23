from pathlib import Path
import shutil
import subprocess
import sys
import math
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

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize initial ring of particles
    create_ring(0, 300, 1)

def create_ring(offset_y, hue_val, scale):
    num_particles = 300
    for i in range(num_particles):
        angle = py5.remap(i, 0, num_particles, 0, py5.TWO_PI)
        radius = 400 * scale
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius
        
        particles.append({
            "x": x,
            "y": offset_y,
            "z": z,
            "angle": angle,
            "radius": radius,
            "hue": hue_val,
            "life": py5.random(1.0, 2.0),
            "age": 0
        })

def draw():
    global particles
    # Motion blur / fade effect
    py5.blend_mode(py5.BLEND)
    py5.push_matrix()
    py5.translate(0, 0, -100)
    py5.no_stroke()
    py5.fill(240, 100, 5, 20) # Very dark blue
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    
    # Alternatively just clear background for this implementation
    py5.background(240, 100, 5) 
    
    t = py5.frame_count / 60.0
    
    # Camera
    cam_radius = 1600
    cx = math.cos(t * 0.5) * cam_radius
    cz = math.sin(t * 0.5) * cam_radius
    py5.camera(cx, -600, cz, 0, 0, 0, 0, 1, 0)
    
    # Add new rings periodically
    if py5.frame_count % 30 == 0:
        create_ring(800, 320, py5.random(0.5, 1.5)) # Magenta
    if py5.frame_count % 45 == 0:
        create_ring(800, 180, py5.random(0.5, 1.5)) # Cyan
        
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    for p in particles:
        # Move up
        p["y"] -= 10
        
        # 3D Noise turbulence
        nx = py5.os_noise(p["x"] * 0.005, p["y"] * 0.005, t)
        nz = py5.os_noise(p["z"] * 0.005, p["y"] * 0.005, t + 100)
        
        p["x"] += py5.remap(nx, -1, 1, -15, 15)
        p["z"] += py5.remap(nz, -1, 1, -15, 15)
        
        p["age"] += 0.01
        
        # Draw particle
        alpha = py5.remap(math.sin(p["age"] * math.pi / p["life"]), 0, 1, 0, 60)
        if alpha < 0: alpha = 0
        
        py5.fill(p["hue"], 80, 100, alpha)
        
        py5.push_matrix()
        py5.translate(p["x"], p["y"], p["z"])
        py5.circle(0, 0, 25) # Use 2D circles in 3D space (billboarding effect approximated)
        py5.pop_matrix()
        
    # Remove dead particles

    particles = [p for p in particles if p["age"] < p["life"]]

    py5.blend_mode(py5.BLEND)

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
