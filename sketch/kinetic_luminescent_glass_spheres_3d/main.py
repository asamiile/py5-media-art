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

spheres = []
num_spheres = 60
bounds = 800

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.sphere_detail(30)
    
    # Initialize spheres
    for _ in range(num_spheres):
        r = py5.random(30, 120)
        x = py5.random(-bounds + r, bounds - r)
        y = py5.random(-bounds + r, bounds - r)
        z = py5.random(-bounds + r, bounds - r)
        vx = py5.random(-5, 5)
        vy = py5.random(-5, 5)
        vz = py5.random(-5, 5)
        # Deep blue and cyan hues
        c = py5.color(py5.random(190, 240), py5.random(60, 100), py5.random(80, 100), 40)
        spheres.append({"x": x, "y": y, "z": z, "vx": vx, "vy": vy, "vz": vz, "r": r, "c": c})

def draw():
    py5.background(0) # Pitch black
    
    # Orbiting camera
    t = py5.frame_count / float(TOTAL_FRAMES)
    cam_radius = 2400
    cx = math.cos(t * math.pi * 2) * cam_radius
    cz = math.sin(t * math.pi * 2) * cam_radius
    py5.camera(cx, 0, cz, 0, 0, 0, 0, 1, 0)
    
    # Dynamic point lights to create reflections
    lx = math.sin(t * math.pi * 4) * 1000
    ly = math.cos(t * math.pi * 3) * 1000
    lz = math.sin(t * math.pi * 2) * 1000
    
    py5.ambient_light(0, 0, 10)
    py5.point_light(0, 0, 100, lx, ly, lz)
    py5.point_light(200, 50, 100, -lx, -ly, -lz)
    
    py5.light_specular(0, 0, 100)
    py5.specular(0, 0, 100)
    py5.shininess(100)
    
    # Additive blending for glass overlap
    py5.blend_mode(py5.ADD)
    
    # Update and draw spheres
    for i in range(num_spheres):
        s1 = spheres[i]
        
        # Move
        s1["x"] += s1["vx"]
        s1["y"] += s1["vy"]
        s1["z"] += s1["vz"]
        
        # Bounce off bounds
        if s1["x"] > bounds - s1["r"] or s1["x"] < -bounds + s1["r"]: s1["vx"] *= -1
        if s1["y"] > bounds - s1["r"] or s1["y"] < -bounds + s1["r"]: s1["vy"] *= -1
        if s1["z"] > bounds - s1["r"] or s1["z"] < -bounds + s1["r"]: s1["vz"] *= -1
        
        # Check collisions
        for j in range(i + 1, num_spheres):
            s2 = spheres[j]
            dx = s2["x"] - s1["x"]
            dy = s2["y"] - s1["y"]
            dz = s2["z"] - s1["z"]
            dist_sq = dx*dx + dy*dy + dz*dz
            min_dist = s1["r"] + s2["r"]
            if dist_sq < min_dist * min_dist:
                # Simple elastic collision (exchange velocities loosely)
                s1["vx"], s2["vx"] = s2["vx"], s1["vx"]
                s1["vy"], s2["vy"] = s2["vy"], s1["vy"]
                s1["vz"], s2["vz"] = s2["vz"], s1["vz"]
                
                # Separate them slightly to avoid sticking
                dist = math.sqrt(dist_sq) if dist_sq > 0 else 1
                overlap = (min_dist - dist) / 2
                s1["x"] -= (dx / dist) * overlap
                s1["y"] -= (dy / dist) * overlap
                s1["z"] -= (dz / dist) * overlap
                s2["x"] += (dx / dist) * overlap
                s2["y"] += (dy / dist) * overlap
                s2["z"] += (dz / dist) * overlap
                
        # Draw
        py5.push_matrix()
        py5.translate(s1["x"], s1["y"], s1["z"])
        py5.no_stroke()
        py5.fill(s1["c"])
        py5.sphere(s1["r"])
        
        # Subtle rim light ring
        py5.no_fill()
        py5.stroke(s1["c"])
        py5.stroke_weight(2)
        py5.circle(0, 0, s1["r"] * 2)
        
        py5.pop_matrix()

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
