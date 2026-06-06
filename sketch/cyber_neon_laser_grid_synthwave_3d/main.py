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
    py5.background(280, 80, 5) # Deep purple/black space
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    # Draw neon synthwave sun in the background
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 200, -1000)
    py5.no_stroke()
    for i in range(10, 0, -1):
        # Glow effect
        py5.fill(330, 90, 100, 10)
        py5.circle(0, 0, 600 + i * 20)
    
    # Core sun (gradient with cutouts usually, but here solid glowing pink/orange)
    py5.fill(15, 90, 100)
    py5.circle(0, 0, 600)
    # Cutout lines for synthwave aesthetic
    py5.blend_mode(py5.BLEND)
    py5.fill(280, 80, 5) # Match background
    for y in range(-300, 300, 40):
        thickness = py5.remap(y, -300, 300, 2, 25)
        py5.rect(-350, y + 100, 700, thickness)
    py5.blend_mode(py5.ADD)
    py5.pop_matrix()
    
    # Moving terrain grid
    py5.translate(py5.width / 2, py5.height / 2 + 100, -200)
    py5.rotate_x(py5.PI / 2.5)
    
    cols = 40
    rows = 40
    scl = 80
    w = cols * scl
    h = rows * scl
    
    py5.translate(-w / 2, -h / 2, 0)
    
    py5.stroke(180, 90, 100, 80) # Cyan grid
    py5.stroke_weight(3)
    py5.no_fill()
    
    # Flying effect
    flying = t * 2
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Calculate heights for current row
            x_off = x * 0.1
            y_off = (y * 0.1) - flying
            z1 = py5.os_noise(x_off, y_off) * 300
            
            # Attenuate height near the center path
            dist_center = abs(x - cols / 2)
            z1 *= py5.remap(dist_center, 0, cols / 2, 0.1, 1)
            
            y_off_next = ((y + 1) * 0.1) - flying
            z2 = py5.os_noise(x_off, y_off_next) * 300
            z2 *= py5.remap(dist_center, 0, cols / 2, 0.1, 1)
            
            # Fade out at the far edge
            alpha1 = py5.remap(y, 0, rows, 0, 100)
            alpha2 = py5.remap(y + 1, 0, rows, 0, 100)
            
            py5.stroke(180, 90, 100, alpha1)
            py5.vertex(x * scl, y * scl, z1)
            
            py5.stroke(180, 90, 100, alpha2)
            py5.vertex(x * scl, (y + 1) * scl, z2)
        py5.end_shape()

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

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
