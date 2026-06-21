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

def draw_tech_ring(radius, segments, rotation, time_val, hue):
    py5.push_matrix()
    py5.rotate_z(rotation)
    
    pulse = 1.0 + py5.sin(time_val * 2 + radius * 0.01) * 0.1
    
    py5.stroke(hue, 80, 100, 200)
    py5.no_fill()
    
    py5.stroke_weight(2)
    py5.circle(0, 0, radius * 2 * pulse)
    
    for i in range(segments):
        py5.push_matrix()
        angle = i * py5.TWO_PI / segments
        py5.rotate_z(angle)
        py5.translate(radius * pulse, 0, 0)
        
        # Cyber detail
        if i % 3 == 0:
            py5.fill(hue, 80, 100, 150)
            py5.box(radius * 0.1, radius * 0.05, radius * 0.05)
        else:
            py5.no_fill()
            # Draw outward spikes or nodes
            py5.line(0, 0, 0, radius * 0.15, 0, 0)
            py5.box(radius * 0.02)
            
        py5.pop_matrix()
        
    py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 20, 10)
    
    # Isometric/Orthographic feel
    py5.ortho(-SIZE[0]/2, SIZE[0]/2, -SIZE[1]/2, SIZE[1]/2, -SIZE[0], SIZE[0])
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_x(py5.PI / 3) # Tilt
    
    # Slow spin of the entire scene
    py5.rotate_z(py5.frame_count * 0.002)
    
    time_val = py5.frame_count * 0.02
    
    # Draw multiple concentric rings
    num_rings = 8
    for r in range(1, num_rings + 1):
        radius = r * (SIZE[1] * 0.1)
        segments = r * 6
        
        # Alternate rotation direction
        rot_dir = 1 if r % 2 == 0 else -1
        rotation = py5.frame_count * 0.005 * rot_dir
        
        # Color palette
        hue = (180 + r * 20 + py5.frame_count * 0.1) % 360 # Cyans to Blues to Purples
        
        draw_tech_ring(radius, segments, rotation, time_val, hue)

    # Center glowing core
    py5.fill(180, 20, 100, 200)
    py5.no_stroke()
    core_pulse = 1.0 + py5.sin(time_val * 4) * 0.2
    py5.box(SIZE[1] * 0.08 * core_pulse)

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
