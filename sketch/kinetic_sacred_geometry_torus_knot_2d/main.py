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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    py5.background(270, 95, 3) 
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    p = 5
    q = 13
    
    num_points = 12000
    
    rot_x = loop_t * 1.0
    rot_y = loop_t * 2.0
    rot_z = loop_t * 0.5
    
    cx, sx = math.cos(rot_x), math.sin(rot_x)
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    
    R1 = SIZE[1] * 0.3 
    R2 = SIZE[1] * 0.15 
    
    py5.no_stroke()
    
    # We sort points by Z depth so they overlap correctly if we were using BLEND,
    # but since we are using ADD blending, order doesn't matter mathematically!
    
    for i in range(num_points):
        theta = (i / num_points) * py5.TWO_PI
        
        r = R1 + R2 * math.cos(q * theta)
        x = r * math.cos(p * theta)
        y = r * math.sin(p * theta)
        z = R2 * math.sin(q * theta)
        
        xy = y * cx - z * sx
        xz = y * sx + z * cx
        y = xy
        z = xz
        
        yx = x * cy + z * sy
        yz = -x * sy + z * cy
        x = yx
        z = yz
        
        zx = x * cz - y * sz
        zy = x * sz + y * cz
        x = zx
        y = zy
        
        z_offset = SIZE[1] * 1.5
        z_factor = z_offset / (z_offset + z)
        
        px = x * z_factor
        py_val = y * z_factor
        
        thickness = py5.remap(z, -R1, R1, 15, 3)
        
        base_hue = (theta / py5.TWO_PI * 360 * 4 + t * 360 * 2) % 360
        # Synthwave remap: push hues towards Cyan (180), Pink (320), Purple (280)
        hue = 260 + math.sin(base_hue * py5.PI / 180) * 80
        
        alpha = py5.remap(z, -R1, R1, 200, 30)
        
        py5.fill(hue, 95, 100, alpha)
        py5.circle(px, py_val, thickness)
        
        if i % 8 == 0:
            py5.fill(hue, 90, 100, alpha * 0.15)
            py5.circle(px, py_val, thickness * 6)

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
