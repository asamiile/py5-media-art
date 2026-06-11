from pathlib import Path
import shutil
import subprocess
import sys
import py5

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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(3)

def draw_star(radius1, radius2, npoints):
    angle = py5.TWO_PI / npoints
    half_angle = angle / 2.0
    py5.begin_shape()
    for a in py5.np.arange(0, py5.TWO_PI, angle):
        sx = py5.cos(a) * radius2
        sy = py5.sin(a) * radius2
        py5.vertex(sx, sy)
        sx = py5.cos(a + half_angle) * radius1
        sy = py5.sin(a + half_angle) * radius1
        py5.vertex(sx, sy)
    py5.end_shape(py5.CLOSE)

def draw():
    # To use blend_mode(ADD) properly with background, we must clear screen manually or use blend_mode(BLEND) for background
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Scale up for 4K
    scale_factor = SIZE[1] / 1080.0
    
    layers = 16
    for i in range(layers):
        r = (i + 1) * 35 * scale_factor
        
        hue = (300 + i * 20 + t * 360 * 2) % 360
        py5.stroke(hue, 90, 100, 70)
        
        py5.push_matrix()
        
        rotation_speed = (i % 2 == 0 and 1 or -1) * (layers - i) * 0.2
        py5.rotate(t * py5.TWO_PI * rotation_speed)
        
        breath = py5.sin(t * py5.TWO_PI * 4 + i * 0.5) * 15 * scale_factor
        actual_r = r + breath
        
        nodes = 6 + (i * 2)
        angle_step = py5.TWO_PI / nodes
        
        for j in range(nodes):
            py5.push_matrix()
            py5.rotate(j * angle_step)
            py5.translate(actual_r, 0)
            
            shape_t = i % 3
            if shape_t == 0:
                py5.circle(0, 0, actual_r * 0.35)
            elif shape_t == 1:
                draw_star(actual_r * 0.1, actual_r * 0.25, 6)
            else:
                py5.rect_mode(py5.CENTER)
                py5.rotate(t * py5.TWO_PI * 3)
                py5.rect(0, 0, actual_r * 0.25, actual_r * 0.25)
                
            py5.pop_matrix()
            
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
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
