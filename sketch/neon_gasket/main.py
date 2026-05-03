from pathlib import Path
import subprocess
import sys
import py5
import numpy as np
from collections import deque
import cmath

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class Circle:
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r
        self.k = 1.0/r if r != 0 else 0

circles = []

def solve_descartes(c1, c2, c3):
    k1, k2, k3 = c1.k, c2.k, c3.k
    z1 = complex(c1.x, c1.y)
    z2 = complex(c2.x, c2.y)
    z3 = complex(c3.x, c3.y)

    # Curvature k4
    k4_base = k1 + k2 + k3
    k4_root = 2 * cmath.sqrt(k1*k2 + k2*k3 + k3*k1)
    k4s = [k4_base + k4_root.real, k4_base - k4_root.real]

    # Position z4
    term1 = k1*z1 + k2*z2 + k3*z3
    term2 = 2 * cmath.sqrt(k1*k2*z1*z2 + k2*k3*z2*z3 + k3*k1*z3*z1)
    
    results = []
    for k4 in k4s:
        if abs(k4) < 1e-6: continue
        z4a = (term1 + term2) / k4
        z4b = (term1 - term2) / k4
        results.append(Circle(z4a.real, z4a.imag, 1.0/k4))
        results.append(Circle(z4b.real, z4b.imag, 1.0/k4))
    return results

def is_tangent(c1, c2, tol=2.0):
    d = np.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)
    # Internal or external tangency
    return abs(d - abs(c1.r + c2.r)) < tol or abs(d - abs(c1.r - c2.r)) < tol

def setup():
    global circles
    py5.size(*SIZE)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initial circles
    r_outer = py5.height * 0.45
    c_outer = Circle(py5.width/2, py5.height/2, -r_outer)
    
    # Two internal circles
    r_inner = r_outer / 2
    c1 = Circle(py5.width/2 - r_inner, py5.height/2, r_inner)
    c2 = Circle(py5.width/2 + r_inner, py5.height/2, r_inner)
    
    all_circles = [c_outer, c1, c2]
    queue = deque([(c_outer, c1, c2)])
    
    # Generate gasket
    while queue and len(all_circles) < 800:
        ca, cb, cc = queue.popleft()
        new_candidates = solve_descartes(ca, cb, cc)
        
        for nc in new_candidates:
            if nc.r < 1.5: continue
            
            # Check if nc is new
            is_new = True
            for existing in all_circles:
                d = np.sqrt((nc.x - existing.x)**2 + (nc.y - existing.y)**2)
                if d < 1.0 and abs(nc.r - existing.r) < 1.0:
                    is_new = False
                    break
            
            if is_new:
                # Must be tangent to all three parents
                if is_tangent(nc, ca) and is_tangent(nc, cb) and is_tangent(nc, cc):
                    all_circles.append(nc)
                    queue.append((nc, ca, cb))
                    queue.append((nc, ca, cc))
                    queue.append((nc, cb, cc))

    circles = all_circles[1:] # Skip outer bounding circle
    # Sort for back-to-front rendering in isometric projection
    # Back is low y, front is high y. In this projection, high y is bottom-right.
    circles.sort(key=lambda c: c.y + c.x)


def draw_building(c, t):
    r = abs(c.r)
    # Height based on radius - cap it more reasonably
    h_base = (1.0 / (r + 5)) * 8000 
    h_base = min(h_base, 600) # Cap height
    h = h_base * (1.0 + 0.15 * np.sin(t + r * 0.1))
    
    cx, cy = c.x, c.y
    
    def project(px, py, pz):
        # Shift and rotate slightly for dynamic feel
        px_rel = px - py5.width/2
        py_rel = py - py5.height/2
        
        # Isometric projection with a bit more tilt
        ix = (px_rel - py_rel) * 0.866
        iy = (px_rel + py_rel) * 0.5 - pz
        return ix + py5.width/2, iy + py5.height/2

    steps = 6
    top_pts = []
    bot_pts = []
    for i in range(steps):
        angle = py5.TWO_PI * i / steps
        px = cx + np.cos(angle) * r
        py = cy + np.sin(angle) * r
        top_pts.append(project(px, py, h))
        bot_pts.append(project(px, py, 0))

    # Neon Colors
    if r > 100: col = (0, 119, 255)    # Blue for base
    elif r > 30: col = (255, 0, 255)   # Pink for mid
    else: col = (57, 255, 20)          # Lime for towers
        
    # Draw side faces (simple shading)
    py5.no_stroke()
    for i in range(steps):
        next_i = (i + 1) % steps
        shade = 0.4 + 0.6 * abs(np.cos(py5.TWO_PI * i / steps))
        py5.fill(col[0]*shade, col[1]*shade, col[2]*shade, 180)
        py5.begin_shape()
        py5.vertex(*top_pts[i])
        py5.vertex(*top_pts[next_i])
        py5.vertex(*bot_pts[next_i])
        py5.vertex(*bot_pts[i])
        py5.end_shape(py5.CLOSE)
        
    # Draw top face (bright)
    py5.fill(col[0], col[1], col[2], 220)
    py5.begin_shape()
    for pt in top_pts:
        py5.vertex(*pt)
    py5.end_shape(py5.CLOSE)
    
    # Glow edge
    py5.stroke(255, 255, 255, 120)
    py5.stroke_weight(0.5)
    py5.no_fill()
    py5.begin_shape()
    for pt in top_pts:
        py5.vertex(*pt)
    py5.end_shape(py5.CLOSE)


def draw():
    py5.background(5, 5, 10)
    t = py5.frame_count * 0.06
    
    # Subtle background bloom effect would be nice, but keep it simple for now
    for c in circles:
        draw_building(c, t)

    # Video recording
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error encoding video: {e}")

if __name__ == "__main__":
    py5.run_sketch()
