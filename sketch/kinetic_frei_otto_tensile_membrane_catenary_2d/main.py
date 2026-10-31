"""
Kinetic Frei Otto Tensile Membrane Catenary Net
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring the lightweight tensile architecture
and minimal surface form-finding experiments of Frei Otto (IL Stuttgart; Munich Olympic
Stadium 1972). Features a dual-bay interconnected hyperbolic paraboloid (hypar) tensile
cable-net canopy spanning between high steel compression masts and low ground anchors,
with orthogonal Prussian-blue suspension catenaries, rust-ochre stabilizing cables,
brass node swages, and translucent PTFE fabric shading on warm architectural drafting vellum.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_frei_otto_tensile_membrane_catenary_2d"
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
RNG_WIND_RATE = float(np.random.uniform(0.97, 1.03))

# Architectural Grid Parameters
NU, NV = 30, 30
U_VALS = np.linspace(-1.0, 1.0, NU)
V_VALS = np.linspace(-1.0, 1.0, NV)

# Projection scaling
SCALE_XY = 350.0
SCALE_Z = 220.0
COS_ANG = np.cos(np.radians(26.0))
SIN_ANG = np.sin(np.radians(26.0))

# Directional sun vector for architectural fabric shadow modeling
SUN_DIR = np.array([0.55, -0.65, 0.52])
SUN_DIR /= np.linalg.norm(SUN_DIR)

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def project_3d(cx, cy, xm, ym, zm):
    px = cx + SCALE_XY * (xm * 1.25 - ym * 0.85) * COS_ANG
    py = cy + SCALE_XY * (xm * 0.65 + ym * 0.90) * SIN_ANG - zm * SCALE_Z
    return px, py, zm * SCALE_Z

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # 1. Background: Warm Architectural Drafting Vellum
    py5.background(246, 242, 234)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5 + 10
    
    # Fine coordinate grid & construction datum lines
    py5.no_fill()
    py5.stroke(232, 226, 216)
    py5.stroke_weight(0.8)
    for x in range(60, WIDTH - 40, 36):
        py5.line(x, 40, x, HEIGHT - 40)
    for y in range(60, HEIGHT - 40, 36):
        py5.line(40, y, WIDTH - 40, y)
        
    # Drafting Margin Border
    py5.stroke(145, 128, 110, 190)
    py5.stroke_weight(2.0)
    py5.rect(50, 40, WIDTH - 100, HEIGHT - 80)
    py5.stroke(185, 170, 155, 130)
    py5.stroke_weight(0.9)
    py5.rect(44, 34, WIDTH - 88, HEIGHT - 68)
    
    # 2. Compute Dual-Bay Interconnected Hypar Tensile Canopy
    bays_data = []
    bay_configs = [
        (-1, -0.72, 0.0),
        (1, 0.72, np.pi * 0.5)
    ]
    
    for bay_id, x_off, phase_s in bay_configs:
        pts_grid = np.zeros((NU, NV, 3))
        for i in range(NU):
            u = U_VALS[i]
            for j in range(NV):
                v = V_VALS[j]
                
                # Saddle shape with aeroelastic wind breathing
                z_saddle = (u**2 - v**2) * (1.0 + 0.10 * np.sin(t_cycle * RNG_WIND_RATE + phase_s + RNG_PHASE_OFFSET))
                # Transverse wave ripple across fabric
                z_wave = 0.07 * np.sin(t_cycle * RNG_WIND_RATE + 2.4 * u + 1.6 * v + phase_s) * (1.0 - 0.35 * (u**2 + v**2))
                zm = z_saddle + z_wave + 0.32
                
                xm = x_off + u * 0.76
                ym = v * 0.94
                
                pts_grid[i, j] = project_3d(cx, cy, xm, ym, zm)
        bays_data.append((bay_id, pts_grid))
        
    # 3. Ground Datum Plane & Foundation Shadows
    base_y = cy + 280
    py5.stroke(140, 125, 110, 140)
    py5.stroke_weight(1.0)
    py5.line(cx - 720, base_y, cx + 720, base_y)
    
    # Soft ambient drop shadow of the canopy on the ground plane
    for bay_id, pts_grid in bays_data:
        py5.no_stroke()
        py5.fill(210, 202, 190, 75)
        py5.begin_shape()
        for i in range(NU):
            p = pts_grid[i, 0]
            py5.vertex(p[0] * 0.96 + cx * 0.04, base_y + 12 * (p[2] / SCALE_Z))
        for j in range(NV):
            p = pts_grid[NU - 1, j]
            py5.vertex(p[0] * 0.96 + cx * 0.04, base_y + 12 * (p[2] / SCALE_Z))
        for i in range(NU - 1, -1, -1):
            p = pts_grid[i, NV - 1]
            py5.vertex(p[0] * 0.96 + cx * 0.04, base_y + 12 * (p[2] / SCALE_Z))
        for j in range(NV - 1, -1, -1):
            p = pts_grid[0, j]
            py5.vertex(p[0] * 0.96 + cx * 0.04, base_y + 12 * (p[2] / SCALE_Z))
        py5.end_shape(py5.CLOSE)
        
    # 4. Render Translucent PTFE Fabric Membrane Facets (Depth Sorted)
    all_quads = []
    for bay_id, pts_grid in bays_data:
        for i in range(NU - 1):
            for j in range(NV - 1):
                p00 = pts_grid[i, j]
                p10 = pts_grid[i + 1, j]
                p11 = pts_grid[i + 1, j + 1]
                p01 = pts_grid[i, j + 1]
                
                v1 = np.array([p10[0] - p00[0], p10[1] - p00[1], p10[2] - p00[2]])
                v2 = np.array([p01[0] - p00[0], p01[1] - p00[1], p01[2] - p00[2]])
                norm = np.cross(v1, v2)
                norm_mag = np.linalg.norm(norm) + 1e-6
                norm /= norm_mag
                
                diff = max(0.0, np.dot(norm, SUN_DIR))
                avg_z = (p00[2] + p10[2] + p11[2] + p01[2]) * 0.25
                all_quads.append((avg_z, [p00, p10, p11, p01], diff, bay_id))
                
    all_quads.sort(key=lambda item: item[0])
    
    py5.no_stroke()
    for avg_z, pts, diff, bay_id in all_quads:
        # Translucent warm membrane wash with architectural light modeling
        cr = int(224 + 28 * diff)
        cg = int(216 + 26 * diff)
        cb = int(196 + 32 * diff)
        py5.fill(cr, cg, cb, 175)
        
        py5.begin_shape()
        for p in pts:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)

    # 5. Catenary Cable Grids (Suspension & Stabilizing Wire Ropes)
    for bay_id, pts_grid in bays_data:
        # Suspension cables along U direction (sagging catenaries in Prussian Blue)
        for j in range(0, NV, 2):
            py5.no_fill()
            py5.stroke(38, 62, 95, 170)
            py5.stroke_weight(1.2 if j % 4 == 0 else 0.8)
            py5.begin_shape()
            for i in range(NU):
                p = pts_grid[i, j]
                py5.vertex(p[0], p[1])
            py5.end_shape()
            
        # Stabilizing cables along V direction (arching catenaries in Rust Ochre)
        for i in range(0, NU, 2):
            py5.no_fill()
            py5.stroke(165, 58, 42, 170)
            py5.stroke_weight(1.2 if i % 4 == 0 else 0.8)
            py5.begin_shape()
            for j in range(NV):
                p = pts_grid[i, j]
                py5.vertex(p[0], p[1])
            py5.end_shape()
            
        # Cable intersection nodes (brass / gold swage fittings)
        py5.no_stroke()
        py5.fill(225, 175, 45, 220)
        for i in range(0, NU, 4):
            for j in range(0, NV, 4):
                p = pts_grid[i, j]
                py5.circle(p[0], p[1], 3.6)
                
        # Heavy perimeter boundary cables
        edge_indices = [
            [(i, 0) for i in range(NU)],
            [(NU - 1, j) for j in range(NV)],
            [(i, NV - 1) for i in range(NU - 1, -1, -1)],
            [(0, j) for j in range(NV - 1, -1, -1)],
        ]
        for edge in edge_indices:
            py5.no_fill()
            py5.stroke(25, 30, 40, 230)
            py5.stroke_weight(2.2)
            py5.begin_shape()
            for i, j in edge:
                p = pts_grid[i, j]
                py5.vertex(p[0], p[1])
            py5.end_shape()
            
    # 6. High Tubular Masts, Guy Wires & Ground Anchors
    mast_positions = [
        pts_grid[NU - 1, NV // 2] for _, pts_grid in bays_data
    ] + [
        pts_grid[0, NV // 2] for _, pts_grid in bays_data
    ]
    
    for top_pt in mast_positions:
        top_x, top_y = top_pt[0], top_pt[1]
        base_x = top_x * 0.94 + cx * 0.06
        
        # Steel tubular mast column
        py5.stroke(35, 42, 52, 220)
        py5.stroke_weight(3.4)
        py5.line(top_x, top_y, base_x, base_y)
        
        # Mast cap & pin joint
        py5.fill(45, 80, 135)
        py5.stroke(25, 30, 40)
        py5.stroke_weight(1.2)
        py5.circle(top_x, top_y, 8.5)
        py5.circle(base_x, base_y, 7.0)
        
        # Radiating guy wire tiebacks
        py5.stroke(90, 75, 65, 140)
        py5.stroke_weight(0.9)
        gw1 = base_x - 140
        gw2 = base_x + 140
        py5.line(top_x, top_y, gw1, base_y)
        py5.line(top_x, top_y, gw2, base_y)
        # Ground anchor stakes
        py5.stroke(185, 55, 40, 200)
        py5.stroke_weight(1.6)
        py5.line(gw1, base_y - 6, gw1, base_y + 12)
        py5.line(gw2, base_y - 6, gw2, base_y + 12)
        
    # 7. Architectural Telemetry: Prestress Tension Graticule & Wind Compass
    py5.stroke(130, 110, 90, 160)
    py5.stroke_weight(1.0)
    py5.line(80, HEIGHT - 75, 380, HEIGHT - 75)
    for tk in range(80, 400, 30):
        py5.line(tk, HEIGHT - 75, tk, HEIGHT - 85)
        
    # Wind angle azimuth indicator in top right
    ind_cx = WIDTH - 95
    ind_cy = 90
    py5.no_fill()
    py5.stroke(140, 120, 95, 160)
    py5.stroke_weight(1.0)
    py5.circle(ind_cx, ind_cy, 66.0)
    py5.line(ind_cx - 33, ind_cy, ind_cx + 33, ind_cy)
    py5.line(ind_cx, ind_cy - 33, ind_cx + 33, ind_cy)
    py5.stroke(185, 55, 42, 220)
    py5.stroke_weight(2.0)
    nd_x = ind_cx + 28.0 * np.cos(t_cycle * RNG_CHIRALITY)
    nd_y = ind_cy + 28.0 * np.sin(t_cycle * RNG_CHIRALITY)
    py5.line(ind_cx, ind_cy, nd_x, nd_y)
    py5.fill(185, 55, 42)
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
