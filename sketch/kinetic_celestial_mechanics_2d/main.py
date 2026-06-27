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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.ADD)
    py5.background(5, 5, 10)

def draw():
    # Motion blur / fading trail effect instead of hard clear
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    time = py5.frame_count * 0.02
    
    # Draw central star pulse
    py5.no_stroke()
    py5.fill(255, 200, 50, 50)
    central_glow = 50 + py5.sin(time * 2) * 10
    py5.circle(0, 0, central_glow * 2)
    py5.fill(255, 255, 200, 150)
    py5.circle(0, 0, 30)
    
    # Draw rings and planets
    num_planets = 9
    for i in range(1, num_planets + 1):
        radius = 80 + i * 80 + py5.sin(time * 0.5 + i) * 20
        speed = 0.5 / i
        angle = time * speed + i * py5.PI / 3.1
        
        # Draw orbital path (faint)
        py5.no_fill()
        py5.stroke(212, 175, 55, 40)
        py5.stroke_weight(1)
        py5.circle(0, 0, radius * 2)
        
        # Compute planet position
        x = py5.cos(angle) * radius
        y = py5.sin(angle) * radius
        
        py5.push_matrix()
        py5.translate(x, y)
        
        # Connect to center with faint line
        py5.stroke(100, 150, 255, 20)
        py5.line(-x, -y, 0, 0)
        
        py5.no_stroke()
        if i % 2 == 0:
            py5.fill(150, 200, 255, 200) # Cyan/blue
            p_size = 8 + py5.sin(time + i)*3
        else:
            py5.fill(255, 100, 150, 200) # Pinkish
            p_size = 12 + py5.cos(time + i)*4
            
        py5.circle(0, 0, p_size * 2)
        
        # Moons
        num_moons = i % 4
        for m in range(1, num_moons + 1):
            moon_dist = p_size + 15 + m * 5
            moon_speed = speed * (3 + m)
            moon_angle = time * moon_speed * (1 if m%2==0 else -1)
            mx = py5.cos(moon_angle) * moon_dist
            my = py5.sin(moon_angle) * moon_dist
            py5.fill(200, 200, 200, 150)
            py5.circle(mx, my, 4)
            
            # Sub-orbital path
            py5.no_fill()
            py5.stroke(255, 255, 255, 20)
            py5.stroke_weight(0.5)
            py5.circle(0, 0, moon_dist * 2)
            
        py5.pop_matrix()

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
