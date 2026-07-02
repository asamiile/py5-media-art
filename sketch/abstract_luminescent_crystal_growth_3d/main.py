from pathlib import Path
import shutil
import subprocess
import sys
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

# Precompute crystal positions on a sphere
NUM_CRYSTALS = 200
crystals = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Fibonacci sphere point generation for even distribution
    golden_ratio = (1 + py5.sqrt(5)) / 2
    for i in range(NUM_CRYSTALS):
        theta = py5.TWO_PI * i / golden_ratio
        phi = py5.acos(1 - 2 * (i + 0.5) / NUM_CRYSTALS)
        
        dir_x = py5.sin(phi) * py5.cos(theta)
        dir_y = py5.sin(phi) * py5.sin(theta)
        dir_z = py5.cos(phi)
        
        base_radius = py5.random(SIZE[1] * 0.1, SIZE[1] * 0.2)
        target_length = py5.random(SIZE[1] * 0.1, SIZE[1] * 0.3)
        thickness = py5.random(20, 50)
        hue = py5.random(280, 340) # Purple/Pink crystals
        
        crystals.append({
            "dx": dir_x, "dy": dir_y, "dz": dir_z,
            "br": base_radius,
            "tl": target_length,
            "th": thickness,
            "hue": hue,
            "offset": py5.random(0, py5.TWO_PI)
        })

def draw():
    py5.background(10, 80, 10)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Dynamic camera
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Rotating light source
    lx = py5.cos(py5.frame_count * 0.02) * SIZE[1]
    lz = py5.sin(py5.frame_count * 0.02) * SIZE[1]
    py5.point_light(200, 50, 100, lx, -SIZE[1]/2, lz)
    py5.ambient_light(280, 80, 20)
    
    # Draw crystals
    for c in crystals:
        # Animate growth
        growth = (py5.sin(py5.frame_count * 0.02 + c["offset"]) + 1) * 0.5
        current_len = c["br"] + c["tl"] * growth
        
        py5.push_matrix()
        
        # Orient towards direction
        # We need to rotate the Z axis to align with (dx, dy, dz)
        axis_x = -c["dy"]
        axis_y = c["dx"]
        axis_z = 0
        angle = py5.acos(c["dz"])
        
        py5.rotate(angle, axis_x, axis_y, axis_z)
        py5.translate(0, 0, current_len/2)
        
        # Crystal material
        py5.no_stroke()
        py5.fill(c["hue"], 80, 100, 60)
        
        # Draw a stretched box (crystal shape)
        py5.box(c["th"], c["th"], current_len)
        
        py5.pop_matrix()
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
