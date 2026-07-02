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
    py5.background(0, 0, 5)
    py5.blend_mode(py5.ADD)
    
    # Move camera forward through the tunnel
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2, 400) # Camera pushed back
    
    # Rotate the whole tunnel slightly
    py5.rotate_z(t * 0.1)
    
    num_sides = 8
    radius = 350
    tunnel_length = 40
    segment_depth = 150
    
    py5.no_stroke()
    
    for i in range(tunnel_length):
        # Calculate actual Z depth based on time
        z = -((i * segment_depth + py5.frame_count * 15) % (tunnel_length * segment_depth))
        
        # Color based on depth and time
        hue = (100 + z * 0.05 + t * 20) % 360
        alpha = py5.remap(z, -tunnel_length * segment_depth, 0, 0, 80)
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        
        # Draw ring of panels
        for j in range(num_sides):
            angle1 = py5.TWO_PI * j / num_sides
            angle2 = py5.TWO_PI * (j + 1) / num_sides
            
            x1 = py5.cos(angle1) * radius
            y1 = py5.sin(angle1) * radius
            x2 = py5.cos(angle2) * radius
            y2 = py5.sin(angle2) * radius
            
            # Draw one quad panel
            py5.fill(hue, 80, 100, alpha)
            py5.begin_shape(py5.QUADS)
            py5.vertex(x1, y1, 0)
            py5.vertex(x2, y2, 0)
            # Add twist or expansion by changing scale/rotation for the next ring (fake it by modifying radius)
            radius_next = radius + py5.sin(t + i * 0.2) * 50
            x3 = py5.cos(angle2) * radius_next
            y3 = py5.sin(angle2) * radius_next
            x4 = py5.cos(angle1) * radius_next
            y4 = py5.sin(angle1) * radius_next
            py5.vertex(x3, y3, -segment_depth)
            py5.vertex(x4, y4, -segment_depth)
            py5.end_shape()
            
            # Add some bright inner edges
            py5.stroke(hue, 50, 100, alpha)
            py5.stroke_weight(2)
            py5.line(x1, y1, 0, x2, y2, 0)
            py5.no_stroke()
            
        py5.pop_matrix()


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
