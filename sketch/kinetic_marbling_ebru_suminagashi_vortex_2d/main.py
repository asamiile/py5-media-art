"""
Kinetic Marbling Ebru Suminagashi Vortex
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring traditional Turkish Ebru and Japanese
Suminagashi paper marbling fluid dynamics. Features multi-tier concentric mineral pigment
ribbons (Prussian indigo, madder carmine, turmeric gold, shoen sumi, malachite celadon,
and violet logwood) floating across a viscous carragheen sizing bath, subjected to periodic
Gelgit rake comb shearing, viscous core vortex shear, floating gold foil (kinpaku) flakes,
and archival basin calibration instrumentation on warm torinoko washi vellum.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_marbling_ebru_suminagashi_vortex_2d"
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
RNG_COMB_RATE = float(np.random.uniform(0.96, 1.04))

# Floating Gold Foil & Mineral Mica Flakes (Kinpaku) Data
NUM_GOLD_FLAKES = 200
GOLD_FLAKES_DATA = [
    (
        float(np.random.uniform(85, WIDTH - 85)),
        float(np.random.uniform(75, HEIGHT - 75)),
        float(np.random.uniform(2.2, 5.8)),
        float(np.random.uniform(0.0, 2.0 * np.pi)),
        float(np.random.uniform(6.0, 18.0)),
        [float(np.random.uniform(0.7, 1.3)) for _ in range(5)]
    )
    for _ in range(NUM_GOLD_FLAKES)
]

# Pigment Palette: Traditional Mineral Gouache & Plant Inks
PALETTE = [
    (22, 48, 88),    # Prussian Indigo (Ai)
    (185, 45, 62),   # Madder Carmine (Beni)
    (220, 162, 42),  # Turmeric Gold (Kihada)
    (20, 24, 30),    # Shoen Sumi Black
    (38, 115, 122),  # Malachite Celadon (Rokushō)
    (130, 68, 118),  # Violet Logwood (Murasaki)
]

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # 1. Background: Warm Torinoko Washi Vellum
    py5.background(246, 240, 228)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5
    
    # Subtle laid paper chain-line texture
    py5.no_fill()
    py5.stroke(234, 226, 212)
    py5.stroke_weight(0.9)
    for y_line in range(40, HEIGHT - 30, 24):
        py5.line(60, y_line, WIDTH - 60, y_line)
        
    # Archival Marbling Basin Outer Frame (Ebru Teknesi)
    py5.stroke(130, 105, 80, 190)
    py5.stroke_weight(2.0)
    py5.rect(60, 50, WIDTH - 120, HEIGHT - 100)
    py5.stroke(185, 165, 140, 120)
    py5.stroke_weight(1.0)
    py5.rect(54, 44, WIDTH - 108, HEIGHT - 88)
    
    # 2. Multi-Tier Concentric Liquid Pigment Ribbons
    num_rings = 46
    num_pts = 220
    theta = np.linspace(0, 2 * np.pi, num_pts, endpoint=False)
    
    comb_spacing = 92.0
    
    # Pre-calculate ring contours under Gelgit comb rake shearing & vortex shear
    ring_contours = []
    for r_idx in range(num_rings + 1):
        # Scale to ensure full visual impact while staying elegantly framed
        base_r = 14.0 + r_idx * 14.8
        pts = []
        for th in theta:
            x0 = cx + base_r * np.cos(th)
            y0 = cy + base_r * 0.70 * np.sin(th)
            
            # Gelgit rake comb shearing along X and Y axes
            comb_phase_x = t_cycle + (x0 / comb_spacing) * np.pi + RNG_PHASE_OFFSET
            comb_disp_y = 42.0 * np.sin(comb_phase_x * RNG_COMB_RATE) * np.cos(t_cycle * 0.5 + r_idx * 0.065)
            
            comb_phase_y = t_cycle + (y0 / 78.0) * np.pi - RNG_PHASE_OFFSET * 0.5
            comb_disp_x = 26.0 * np.cos(comb_phase_y)
            
            # Viscous vortex core shear
            dist_c = np.hypot(x0 - cx, y0 - cy)
            vortex_ang = 1.30 * np.exp(-dist_c / 280.0) * np.sin(t_cycle) * RNG_CHIRALITY
            
            dx = (x0 + comb_disp_x) - cx
            dy = (y0 + comb_disp_y) - cy
            rx = cx + dx * np.cos(vortex_ang) - dy * np.sin(vortex_ang)
            ry = cy + dx * np.sin(vortex_ang) + dy * np.cos(vortex_ang)
            
            pts.append((rx, ry))
        ring_contours.append(pts)
        
    # Render smooth filled pigment bands (QUAD_STRIP without transverse facets)
    for r_idx in range(num_rings):
        inner_pts = ring_contours[r_idx]
        outer_pts = ring_contours[r_idx + 1]
        col = PALETTE[r_idx % len(PALETTE)]
        
        # Soft gouache pigment wash opacity gradient
        alpha = 158 - int(r_idx * 1.35)
        py5.fill(col[0], col[1], col[2], max(42, alpha))
        py5.no_stroke()
        
        py5.begin_shape(py5.QUAD_STRIP)
        for k in range(num_pts):
            p_in = inner_pts[k]
            p_out = outer_pts[k]
            py5.vertex(p_in[0], p_in[1])
            py5.vertex(p_out[0], p_out[1])
        # Close strip loop
        py5.vertex(inner_pts[0][0], inner_pts[0][1])
        py5.vertex(outer_pts[0][0], outer_pts[0][1])
        py5.end_shape()
        
    # Draw crisp contour boundaries between bands
    for r_idx in range(num_rings + 1):
        pts = ring_contours[r_idx]
        col = PALETTE[r_idx % len(PALETTE)]
        py5.no_fill()
        py5.stroke(col[0] // 2, col[1] // 2, col[2] // 2, 125)
        py5.stroke_weight(0.95)
        py5.begin_shape()
        for p in pts:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
    # Center droplet nucleus (initial sumi pigment drop)
    core_pts = ring_contours[0]
    py5.fill(PALETTE[0][0], PALETTE[0][1], PALETTE[0][2], 215)
    py5.stroke(PALETTE[0][0] // 2, PALETTE[0][1] // 2, PALETTE[0][2] // 2, 170)
    py5.stroke_weight(1.2)
    py5.begin_shape()
    for p in core_pts:
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)
    
    # 3. Floating Gold Foil Flakes & Mineral Mica (Kinpaku)
    py5.fill(235, 192, 55, 220)
    py5.stroke(185, 145, 35, 160)
    py5.stroke_weight(0.7)
    for (gx_base, gy_base, gr, g_phase, g_amp, jitters) in GOLD_FLAKES_DATA:
        # Subtle harmonic surface drift
        gx = gx_base + g_amp * 0.4 * np.sin(t_cycle + g_phase)
        gy = gy_base + g_amp * 0.4 * np.cos(t_cycle + g_phase)
        
        py5.begin_shape()
        for pt in range(5):
            p_ang = pt * (2.0 * np.pi / 5.0)
            r_jitter = gr * jitters[pt]
            py5.vertex(gx + r_jitter * np.cos(p_ang), gy + r_jitter * np.sin(p_ang))
        py5.end_shape(py5.CLOSE)
        
    # 4. Technical Ebru Rake Coordinate Calibration Scale
    py5.stroke(130, 105, 80, 160)
    py5.stroke_weight(1.0)
    py5.line(80, HEIGHT - 75, 360, HEIGHT - 75)
    for tk in range(80, 380, 28):
        py5.line(tk, HEIGHT - 75, tk, HEIGHT - 85)
        
    # Comb stroke compass in top right
    ind_cx = WIDTH - 95
    ind_cy = 90
    py5.no_fill()
    py5.stroke(140, 115, 85, 160)
    py5.stroke_weight(1.0)
    py5.circle(ind_cx, ind_cy, 66.0)
    py5.line(ind_cx - 33, ind_cy, ind_cx + 33, ind_cy)
    py5.line(ind_cx, ind_cy - 33, ind_cx, ind_cy + 33)
    py5.stroke(185, 45, 62, 220)
    py5.stroke_weight(2.0)
    nd_x = ind_cx + 28.0 * np.cos(t_cycle * RNG_CHIRALITY)
    nd_y = ind_cy + 28.0 * np.sin(t_cycle * RNG_CHIRALITY)
    py5.line(ind_cx, ind_cy, nd_x, nd_y)
    py5.fill(185, 45, 62)
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
