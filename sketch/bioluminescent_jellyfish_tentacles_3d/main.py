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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(220, 90, 5) # Deep underwater blue
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height * 0.2, -300)
    
    t = py5.frame_count * 0.05
    py5.rotate_y(t * 0.2)
    py5.rotate_x(py5.sin(t * 0.1) * 0.2)
    
    num_tentacles = 18
    num_segments = 60
    
    py5.no_fill()
    py5.stroke_weight(4)
    
    for i in range(num_tentacles):
        angle = py5.TWO_PI * i / num_tentacles
        
        # Base position in a circle (the bell of the jellyfish)
        base_x = py5.cos(angle) * 100
        base_z = py5.sin(angle) * 100
        
        py5.begin_shape(py5.LINE_STRIP)
        for j in range(num_segments):
            # The tentacle flows downwards (positive Y)
            # Sway based on noise and sine waves
            
            # Phase shifts
            phase = t * 0.8 - j * 0.1
            
            # Complex sway
            sway_x = py5.sin(phase + angle) * (j * 1.5)
            sway_z = py5.cos(phase + angle * 2) * (j * 1.5)
            
            # Noise for organic feel
            n = py5.os_noise(i * 0.5, j * 0.1, t * 0.2) - 0.5
            sway_x += n * (j * 2)
            sway_z += n * (j * 2)
            
            px = base_x + sway_x
            py5.y = j * 20 # go down
            pz = base_z + sway_z
            
            # Pulse the color
            pulse = py5.sin(phase * 2) * 0.5 + 0.5
            hue = (180 + pulse * 40 + i * 10) % 360 # Cyan to blue to purple
            
            # Fade out at the bottom
            alpha = py5.remap(j, 0, num_segments, 90, 0)
            
            py5.stroke(hue, 90, 100, alpha)
            py5.vertex(px, py5.y, pz)
            
            # Sometimes add glowing orbs along the tentacle
            if j % 15 == 0 and j > 0:
                py5.push_matrix()
                py5.translate(px, py5.y, pz)
                py5.no_stroke()
                py5.fill(hue, 100, 100, alpha * 0.8)
                py5.sphere(8 + pulse * 5)
                py5.pop_matrix()
                py5.no_fill()
                py5.stroke_weight(4)
                
        py5.end_shape()


    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
