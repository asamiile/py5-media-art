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

centers = [(0, 0)]
R = 300

for i in range(6):
    angle = i * math.pi / 3
    centers.append((math.cos(angle) * R, math.sin(angle) * R))
    
for i in range(6):
    angle = i * math.pi / 3
    centers.append((math.cos(angle) * 2 * R, math.sin(angle) * 2 * R))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(270, 80, 10)
    
def draw():
    py5.no_stroke()
    py5.fill(270, 80, 5, 15) 
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    py5.rotate(t * py5.TWO_PI / 6)
    
    py5.stroke_weight(3)
    
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            p1 = centers[i]
            p2 = centers[j]
            
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            dist = math.sqrt(mid_x**2 + mid_y**2)
            
            wave = (math.sin(dist * 0.005 - loop_t * 2) + 1) / 2
            
            hue = (40 + wave * 50 + py5.noise(mid_x * 0.01, mid_y * 0.01, t * 2) * 60) % 360 
            alpha = 10 + wave * 90
            
            py5.stroke(hue, 90, 100, alpha)
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
    py5.stroke_weight(5)
    py5.no_fill()
    for i, c in enumerate(centers):
        dist = math.sqrt(c[0]**2 + c[1]**2)
        wave = (math.sin(dist * 0.005 - loop_t * 2 + math.pi) + 1) / 2
        
        radius = R * (1.0 + wave * 0.05)
        
        hue = (180 + wave * 60) % 360 
        alpha = 40 + wave * 60
        
        py5.stroke(hue, 90, 100, alpha)
        py5.circle(c[0], c[1], radius * 2) 

    py5.color_mode(py5.RGB, 255)

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
