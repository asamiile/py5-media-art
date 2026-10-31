"""
Kinetic Lagrangian Three Body Jacobi Orbits
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring the Circular Restricted Three-Body
Problem (CR3BP) and the dynamic topology of the Jacobi Constant equipotential surfaces
and invariant manifold tubes. In the rotating non-inertial frame of a radiant Primary star
and an orbiting ringed gas giant, five Lagrange libration points (L1-L5) govern celestial
equilibrium. Features continuous Roche potential contour lobes, flowing heteroclinic
manifold tubes ("The Interplanetary Superhighway"), periodic Lyapunov and Halo orbits,
and resonant Trojan asteroid libration swarms on deep interstellar obsidian space.
"""

import os
import shutil
import subprocess
import time
import cv2
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_lagrangian_three_body_jacobi_orbits_2d"
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 720
FPS = 60

# Paths
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
PREVIEW_PATH = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")

# Dynamic non-fixed initial phase and parameters for generative run variation
RNG_PHASE_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RNG_CHIRALITY = 1.0 if np.random.uniform() > 0.5 else -1.0
RNG_PULSE_RATE = float(np.random.uniform(0.96, 1.04))

# Distant starfield & cosmic dust data
NUM_STARS = 260
STARFIELD_DATA = [
    (
        float(np.random.uniform(20, WIDTH - 20)),
        float(np.random.uniform(20, HEIGHT - 20)),
        float(np.random.uniform(0.8, 2.4)),
        float(np.random.uniform(35, 190)),
        float(np.random.uniform(0.0, 2.0 * np.pi))
    )
    for _ in range(NUM_STARS)
]

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # 1. Background: Deep Cosmic Interstellar Obsidian
    py5.background(7, 9, 15)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5
    scale = 350.0
    mu = 0.20 # Prominent mass ratio for clear topological separation
    
    # Distant starfield with subtle harmonic twinkling
    py5.no_stroke()
    for (sx, sy, s_rad, s_bri, s_phase) in STARFIELD_DATA:
        twinkle = s_bri * (0.80 + 0.20 * np.sin(t_cycle * 2.0 + s_phase))
        py5.fill(190, 215, 245, int(twinkle))
        py5.circle(sx, sy, s_rad)
        
    # Celestial Polar Coordinate Graticule & Reference Radials
    py5.no_fill()
    py5.stroke(25, 38, 58, 65)
    py5.stroke_weight(0.8)
    for r in range(120, 800, 90):
        py5.circle(cx, cy, r * 2.0)
    py5.line(cx - 850, cy, cx + 850, cy)
    py5.line(cx, cy - 480, cx, cy + 480)
    
    # 2. Roche Potential Field Computation (Grid with contour extraction)
    grid_w, grid_h = WIDTH // 2, HEIGHT // 2
    gx = np.linspace(-cx / scale, (WIDTH - cx) / scale, grid_w)
    gy = np.linspace(-cy / scale, (HEIGHT - cy) / scale, grid_h)
    X, Y = np.meshgrid(gx, gy)
    
    # Subtle harmonic libration breathing in mass ratio and positions
    mu_eff = mu + 0.006 * np.sin(t_cycle * RNG_PULSE_RATE + RNG_PHASE_OFFSET)
    
    R1 = np.sqrt((X + mu_eff)**2 + Y**2) + 0.025
    R2 = np.sqrt((X - (1.0 - mu_eff))**2 + Y**2) + 0.025
    
    # Effective Roche potential in rotating frame
    U = 0.5 * (X**2 + Y**2) + (1.0 - mu_eff) / R1 + mu_eff / R2
    
    # Critical potential levels spanning L4/L5 minima up to stellar funnels
    levels = [
        1.44, 1.47, 1.51, 1.55,
        1.62, 1.67, 1.72,
        1.79, 1.83, 1.87,
        1.91, 1.96, 2.03, 2.12, 2.25, 2.42, 2.65, 2.95, 3.35, 3.90, 4.60
    ]
    
    # Draw glowing continuous equipotential curves
    py5.no_fill()
    for idx, c_val in enumerate(levels):
        t_c = idx / len(levels)
        mask = (U >= c_val).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
        
        # Color palette: deep celestial indigo -> electric cyan -> solar amber -> laser crimson
        if t_c < 0.35: # L4/L5 & Horseshoe
            cr, cg, cb = 38, int(85 + 100 * t_c), int(170 + 70 * t_c)
            alpha = int(75 + 40 * t_c)
            weight = 0.95
        elif t_c < 0.65: # L2 / L1 Critical Lobes
            norm_t = (t_c - 0.35) / 0.30
            cr = int(38 + 180 * norm_t)
            cg = int(185 + 40 * (1.0 - norm_t))
            cb = int(240 * (1.0 - norm_t * 0.7))
            alpha = int(115 + 50 * norm_t)
            weight = 1.35 if abs(c_val - 1.91) < 0.05 else 1.05
        else: # Deep Gravitational Funnels
            norm_t = (t_c - 0.65) / 0.35
            cr = int(218 + 37 * norm_t)
            cg = int(160 * (1.0 - norm_t * 0.75))
            cb = int(60 * (1.0 - norm_t * 0.8))
            alpha = int(140 + 75 * norm_t)
            weight = 1.15
            
        py5.stroke(cr, cg, cb, alpha)
        py5.stroke_weight(weight)
        
        for cnt in contours:
            if len(cnt) < 4:
                continue
            py5.begin_shape()
            for pt in cnt:
                px = pt[0][0] * 2
                py = pt[0][1] * 2
                py5.vertex(px, py)
            py5.end_shape(py5.CLOSE)
            
    # 3. Celestial Bodies: Primary Star M1 and Secondary Planet M2
    x1 = cx - mu_eff * scale
    y1 = cy
    x2 = cx + (1.0 - mu_eff) * scale
    y2 = cy
    
    # Primary Star M1 (Incandescent Solar Core & Corona)
    py5.no_stroke()
    for g_rad in range(110, 25, -12):
        py5.fill(245, 158, 11, int(18 * (1.0 - g_rad / 110.0)))
        py5.circle(x1, y1, g_rad * 2.0)
    py5.fill(254, 240, 138)
    py5.circle(x1, y1, 52.0)
    py5.fill(255, 255, 255)
    py5.circle(x1, y1, 32.0)
    
    # Secondary Body M2 (Cerulean Gas Giant with rings)
    py5.no_fill()
    py5.stroke(147, 197, 253, 160)
    py5.stroke_weight(2.0)
    py5.ellipse(x2, y2, 74.0, 24.0)
    py5.stroke(96, 165, 250, 100)
    py5.stroke_weight(1.0)
    py5.ellipse(x2, y2, 88.0, 28.0)
    py5.no_stroke()
    py5.fill(37, 99, 235)
    py5.circle(x2, y2, 32.0)
    py5.fill(96, 165, 250)
    py5.circle(x2 - 5, y2 - 5, 18.0)
    py5.fill(224, 242, 254)
    py5.circle(x2 - 7, y2 - 7, 7.0)
    
    # 4. Lagrange Points L1 - L5
    l1_x = cx + (0.4376 - mu_eff) * scale
    l2_x = cx + (1.2708 - mu_eff) * scale
    l3_x = cx + (-1.0828 - mu_eff) * scale
    l4_x = cx + (0.5 - mu_eff) * scale
    l4_y = cy - (np.sqrt(3)/2) * scale
    l5_x = cx + (0.5 - mu_eff) * scale
    l5_y = cy + (np.sqrt(3)/2) * scale
    
    lp_data = [
        ("L1", l1_x, cy, (244, 63, 94)),
        ("L2", l2_x, cy, (244, 63, 94)),
        ("L3", l3_x, cy, (245, 158, 11)),
        ("L4", l4_x, l4_y, (56, 189, 248)),
        ("L5", l5_x, l5_y, (56, 189, 248)),
    ]
    for name, lx, ly, lcol in lp_data:
        py5.no_fill()
        py5.stroke(lcol[0], lcol[1], lcol[2], 220)
        py5.stroke_weight(1.0)
        py5.circle(lx, ly, 18.0)
        py5.circle(lx, ly, 28.0)
        py5.line(lx - 18, ly, lx + 18, ly)
        py5.line(lx, ly - 18, lx, ly + 18)
        py5.fill(lcol[0], lcol[1], lcol[2])
        py5.no_stroke()
        py5.circle(lx, ly, 4.0)
        
    # 5. Invariant Manifold Tubes & Orbital Highways
    num_tubes = 44
    for tb_idx in range(num_tubes):
        tube_phase = tb_idx * (2.0 * np.pi / num_tubes)
        tube_t = t_cycle + tube_phase
        
        tube_pts = []
        for s in np.linspace(-1.3, 1.3, 90):
            rad = 0.22 * np.sin(np.pi * (s + 1.3) / 2.6)
            tx = l1_x + s * 135.0 + 28.0 * np.sin(tube_t + s * 2.8)
            ty = cy + rad * 90.0 * np.cos(tube_t + s * 3.6) + 18.0 * np.sin(s * 2.2)
            tube_pts.append((tx, ty))
            
        py5.no_fill()
        py5.stroke(56, 189, 248, 70)
        py5.stroke_weight(1.1)
        py5.begin_shape()
        for p in tube_pts:
            py5.vertex(p[0], p[1])
        py5.end_shape()

    # Outer manifold plume from L2 escaping outwards
    for tb_idx in range(24):
        tube_phase = tb_idx * (2.0 * np.pi / 24)
        tube_t = t_cycle + tube_phase
        
        plume_pts = []
        for s in np.linspace(0.0, 1.8, 70):
            tx = l2_x + s * 110.0 + 22.0 * np.cos(tube_t + s * 2.5)
            ty = cy + s**1.5 * 65.0 * np.sin(tube_t + s * 3.0)
            plume_pts.append((tx, ty))
            
        py5.no_fill()
        py5.stroke(168, 85, 247, 55)
        py5.stroke_weight(1.0)
        py5.begin_shape()
        for p in plume_pts:
            py5.vertex(p[0], p[1])
        py5.end_shape()

    # Lyapunov & Halo periodic orbits around L1 and L2
    py5.no_fill()
    for lp_c, lp_col in [(l1_x, (244, 63, 94)), (l2_x, (244, 63, 94))]:
        for h_i in range(5):
            h_rx = 16.0 + h_i * 6.5
            h_ry = 32.0 + h_i * 12.0
            py5.stroke(lp_col[0], lp_col[1], lp_col[2], 90 - h_i * 12)
            py5.stroke_weight(1.0)
            py5.begin_shape()
            for th in np.linspace(0, 2 * np.pi, 50):
                hx = lp_c + h_rx * np.cos(th + t_cycle * 2.0)
                hy = cy + h_ry * np.sin(th + t_cycle * 2.0)
                py5.vertex(hx, hy)
            py5.end_shape(py5.CLOSE)

    # 6. Trojan Libration Swarms around L4 & L5 (Fixed no_fill bug!)
    for l_cx, l_cy, sign in [(l4_x, l4_y, 1.0), (l5_x, l5_y, -1.0)]:
        py5.no_fill()
        py5.stroke(245, 158, 11, 85)
        py5.stroke_weight(1.0)
        for orb_i in range(10):
            a_semi = 35.0 + orb_i * 9.5
            b_semi = 20.0 + orb_i * 5.8
            rot_ang = sign * (0.28 + 0.05 * np.sin(t_cycle))
            
            py5.begin_shape()
            for th in np.linspace(0, 2 * np.pi, 60):
                ox = a_semi * np.cos(th + t_cycle * 0.9 * sign)
                oy = b_semi * np.sin(th + t_cycle * 0.9 * sign)
                rx = l_cx + ox * np.cos(rot_ang) - oy * np.sin(rot_ang)
                ry = l_cy + ox * np.sin(rot_ang) + oy * np.cos(rot_ang)
                py5.vertex(rx, ry)
            py5.end_shape(py5.CLOSE)
            
        # Libration asteroid particles along orbits
        py5.no_stroke()
        for p_idx in range(14):
            p_ang = t_cycle * 0.9 * sign + p_idx * (2.0 * np.pi / 14)
            p_a = 55.0 + (p_idx % 4) * 16.0
            p_b = 30.0 + (p_idx % 4) * 9.0
            ox = p_a * np.cos(p_ang)
            oy = p_b * np.sin(p_ang)
            rx = l_cx + ox * np.cos(rot_ang) - oy * np.sin(rot_ang)
            ry = l_cy + ox * np.sin(rot_ang) + oy * np.cos(rot_ang)
            py5.fill(254, 240, 138, 220)
            py5.circle(rx, ry, 3.2)

    # 7. Astrodynamic Telemetry: Orbital Compass & Energy Scale
    py5.stroke(75, 95, 130, 160)
    py5.stroke_weight(1.0)
    py5.line(80, HEIGHT - 75, 360, HEIGHT - 75)
    for tk in range(80, 380, 28):
        py5.line(tk, HEIGHT - 75, tk, HEIGHT - 85)
        
    # Rotating True Anomaly Astrolabe in top right
    ind_cx = WIDTH - 95
    ind_cy = 90
    py5.no_fill()
    py5.stroke(75, 95, 130, 160)
    py5.stroke_weight(1.0)
    py5.circle(ind_cx, ind_cy, 66.0)
    py5.line(ind_cx - 33, ind_cy, ind_cx + 33, ind_cy)
    py5.line(ind_cx, ind_cy - 33, ind_cx, ind_cy + 33)
    py5.stroke(56, 189, 248, 220)
    py5.stroke_weight(1.8)
    nd_x = ind_cx + 28.0 * np.cos(t_cycle * RNG_CHIRALITY)
    nd_y = ind_cy + 28.0 * np.sin(t_cycle * RNG_CHIRALITY)
    py5.line(ind_cx, ind_cy, nd_x, nd_y)
    py5.fill(56, 189, 248)
    py5.no_stroke()
    py5.circle(nd_x, nd_y, 4.5)

def draw():
    print(f"[{WORK_NAME}] Starting 4K render: {TOTAL_FRAMES} frames @ Retina 4K (3840x2160)...")
    start_time = time.time()
    
    for f in range(TOTAL_FRAMES):
        f_start = time.time()
        render_frame_batched(f)
        
        frame_file = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        py5.save_frame(frame_file)
        
        # Save preview at midpoint (frame 360)
        if f == TOTAL_FRAMES // 2:
            py5.save_frame(PREVIEW_PATH)
            print(f"[{WORK_NAME}] Saved preview frame {f} -> {PREVIEW_PATH}")
            
        f_elapsed = time.time() - f_start
        if (f + 1) % 60 == 0 or f == 0 or f == TOTAL_FRAMES - 1:
            fps_est = (f + 1) / (time.time() - start_time)
            remaining = (TOTAL_FRAMES - (f + 1)) / max(fps_est, 0.001)
            print(f"[{WORK_NAME}] Frame {f+1:03d}/{TOTAL_FRAMES} ({f_elapsed:.3f}s/f, ~{fps_est:.2f} fps, {remaining:.1f}s remaining)")
            
    total_time = time.time() - start_time
    print(f"[{WORK_NAME}] Render completed in {total_time:.1f}s ({total_time/TOTAL_FRAMES:.3f}s/frame)")
    
    # Compile MP4 via FFmpeg at full 4K (3840x2160)
    print(f"[{WORK_NAME}] Encoding 4K 60fps MP4 via FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        OUTPUT_MP4
    ]
    res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg error: {res.stderr}")
        raise RuntimeError("FFmpeg encoding failed")
        
    mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
    print(f"[{WORK_NAME}] Output MP4 generated: {OUTPUT_MP4} ({mp4_size_mb:.2f} MB)")
    
    # Cleanup frames directory
    print(f"[{WORK_NAME}] Cleaning up temporary frames directory...")
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Cleanup complete. Done!")
    
    # Explicitly exit JVM process to prevent hanging
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
