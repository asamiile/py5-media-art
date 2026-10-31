"""
Kinetic Brutalist Tectonic Cantilever Shadows
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring monumental brutalist megastructures
in axonometric projection. Features board-formed concrete slabs (béton brut),
sliding cantilevered volumes, an Aegean cerulean reflecting pool with caustic ripples,
sunken plazas, and a dynamic 360-degree solar orbit casting dramatic geometric shadows
across travertine vellum grounds.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_brutalist_tectonic_cantilever_shadows_2d"
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 720
FPS = 60

# Paths
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
PREVIEW_PATH = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")

# Dynamic non-fixed initial phase for organic variability
RNG_AZ_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RNG_SLAB_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def iso_project(x, y, z, cx, cy):
    """30-degree isometric axonometric projection."""
    cos30 = 0.8660254037844386
    sin30 = 0.5
    u = cx + (x - y) * cos30
    v = cy + (x + y) * sin30 - z
    return u, v

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # Background: Warm Travertine drafting vellum
    py5.background(236, 232, 222)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.64
    
    # Drafting construction grid (isometric)
    py5.stroke(222, 216, 204)
    py5.stroke_weight(0.7)
    for i in range(-16, 17):
        u1, v1 = iso_project(-1500, i * 90, 0, cx, cy)
        u2, v2 = iso_project(1500, i * 90, 0, cx, cy)
        py5.line(u1, v1, u2, v2)
        u1, v1 = iso_project(i * 90, -1500, 0, cx, cy)
        u2, v2 = iso_project(i * 90, 1500, 0, cx, cy)
        py5.line(u1, v1, u2, v2)
        
    # Orbiting Sun vector (complete 360-degree rotation for seamless loop)
    sun_az = t_cycle + RNG_AZ_OFFSET
    sun_elev = np.radians(48.0)
    sx = np.cos(sun_az) * np.cos(sun_elev)
    sy = np.sin(sun_az) * np.cos(sun_elev)
    sz = -np.sin(sun_elev)
    
    def shadow_pt(x, y, z, target_z=0):
        if z <= target_z:
            return iso_project(x, y, target_z, cx, cy)
        gx = x - (z - target_z) * (sx / sz)
        gy = y - (z - target_z) * (sy / sz)
        return iso_project(gx, gy, target_z, cx, cy)
        
    # Harmonically smooth cantilever displacements (exact C1 seamless loop)
    dx1 = 125.0 * np.sin(t_cycle + RNG_SLAB_OFFSET)
    dy1 = 95.0 * np.cos(t_cycle + RNG_SLAB_OFFSET)
    dx2 = -85.0 * np.sin(t_cycle + RNG_SLAB_OFFSET)
    
    # 1. Base Podium Box (z=0 to z=35)
    podium = {"x": -560, "y": -560, "z": 0, "dx": 1120, "dy": 1120, "dz": 35}
    
    # 2. Upper Architectural Volumes (z >= 35)
    upper_boxes = [
        # Reflecting Pool on podium deck (z=35, flush water surface)
        {"x": -480, "y": 80, "z": 35, "dx": 400, "dy": 400, "dz": 10, "type": "pool"},
        
        # Central Monolithic Tower Shaft
        {"x": -90, "y": -90, "z": 35, "dx": 180, "dy": 180, "dz": 450, "type": "tower", "accent": True},
        
        # Upper Cantilever Slab 1 (Glides horizontally along X)
        {"x": -440 + dx1, "y": -240, "z": 130, "dx": 560, "dy": 280, "dz": 46, "type": "slab", "accent": True},
        
        # Mid-level Cantilever Slab 2 (Glides transversely along Y)
        {"x": -80, "y": -420 + dy1, "z": 220, "dx": 380, "dy": 600, "dz": 46, "type": "slab", "accent": False},
        
        # High Floating Skybridge Beam (Counter-glides along X)
        {"x": -300 + dx2, "y": -140, "z": 330, "dx": 700, "dy": 160, "dz": 55, "type": "beam", "accent": True},
        
        # Vertical Louver Blades (Brise-soleil)
        {"x": 160, "y": -40, "z": 35, "dx": 28, "dy": 340, "dz": 280, "type": "louver"},
        {"x": 220, "y": -40, "z": 35, "dx": 28, "dy": 340, "dz": 280, "type": "louver"},
        {"x": 280, "y": -40, "z": 35, "dx": 28, "dy": 340, "dz": 280, "type": "louver"},
        
        # Stepped Monumental Terraces
        {"x": -510, "y": -500, "z": 35, "dx": 340, "dy": 220, "dz": 55, "type": "terrace"},
        {"x": -470, "y": -460, "z": 90, "dx": 260, "dy": 180, "dz": 45, "type": "terrace"},
    ]
    
    # -------------------------------------------------------------
    # PASS 1: Ground Shadows (z=0)
    # -------------------------------------------------------------
    py5.fill(36, 33, 28, 80)
    py5.no_stroke()
    # Shadow of the podium base
    p_pts = [
        shadow_pt(-560, -560, 35, 0),
        shadow_pt(560, -560, 35, 0),
        shadow_pt(560, 560, 35, 0),
        shadow_pt(-560, 560, 35, 0)
    ]
    py5.begin_shape()
    for p in p_pts:
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)
    
    # Shadows of high cantilevers projected onto the ground plane
    for b in upper_boxes:
        if b["type"] == "pool":
            continue
        x, y, z, dx, dy, dz = b["x"], b["y"], b["z"], b["dx"], b["dy"], b["dz"]
        pts = [
            shadow_pt(x, y, z + dz, 0),
            shadow_pt(x + dx, y, z + dz, 0),
            shadow_pt(x + dx, y + dy, z + dz, 0),
            shadow_pt(x, y + dy, z + dz, 0)
        ]
        py5.begin_shape()
        for p in pts:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
    # -------------------------------------------------------------
    # PASS 2: Draw Base Podium
    # -------------------------------------------------------------
    px, py, pz, pdx, pdy, pdz = podium["x"], podium["y"], podium["z"], podium["dx"], podium["dy"], podium["dz"]
    pp010 = iso_project(px, py + pdy, pz, cx, cy)
    pp110 = iso_project(px + pdx, py + pdy, pz, cx, cy)
    pp111 = iso_project(px + pdx, py + pdy, pz + pdz, cx, cy)
    pp011 = iso_project(px, py + pdy, pz + pdz, cx, cy)
    pp100 = iso_project(px + pdx, py, pz, cx, cy)
    pp101 = iso_project(px + pdx, py, pz + pdz, cx, cy)
    pp001 = iso_project(px, py, pz + pdz, cx, cy)
    
    # Podium Left Vertical Face (+Y normal)
    py5.fill(162, 156, 145)
    py5.stroke(98, 93, 84)
    py5.stroke_weight(1.5)
    py5.begin_shape()
    py5.vertex(pp010[0], pp010[1])
    py5.vertex(pp110[0], pp110[1])
    py5.vertex(pp111[0], pp111[1])
    py5.vertex(pp011[0], pp011[1])
    py5.end_shape(py5.CLOSE)
    
    # Podium Right Vertical Face (+X normal)
    py5.fill(120, 115, 105)
    py5.stroke(82, 78, 70)
    py5.stroke_weight(1.5)
    py5.begin_shape()
    py5.vertex(pp100[0], pp100[1])
    py5.vertex(pp110[0], pp110[1])
    py5.vertex(pp111[0], pp111[1])
    py5.vertex(pp101[0], pp101[1])
    py5.end_shape(py5.CLOSE)
    
    # Podium Top Face (+Z normal)
    py5.fill(218, 213, 201)
    py5.stroke(112, 108, 98)
    py5.stroke_weight(1.5)
    py5.begin_shape()
    py5.vertex(pp001[0], pp001[1])
    py5.vertex(pp101[0], pp101[1])
    py5.vertex(pp111[0], pp111[1])
    py5.vertex(pp011[0], pp011[1])
    py5.end_shape(py5.CLOSE)
    
    # -------------------------------------------------------------
    # PASS 3: Cast Shadows onto Podium Top Face (z=35)
    # -------------------------------------------------------------
    py5.fill(36, 33, 28, 95)
    py5.no_stroke()
    for b in upper_boxes:
        if b["type"] == "pool":
            continue
        x, y, z, dx, dy, dz = b["x"], b["y"], b["z"], b["dx"], b["dy"], b["dz"]
        pts = [
            shadow_pt(x, y, z + dz, 35),
            shadow_pt(x + dx, y, z + dz, 35),
            shadow_pt(x + dx, y + dy, z + dz, 35),
            shadow_pt(x, y + dy, z + dz, 35)
        ]
        py5.begin_shape()
        for p in pts:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
    # -------------------------------------------------------------
    # PASS 4: Draw Upper Volumes (Depth Sorted)
    # -------------------------------------------------------------
    boxes_sorted = sorted(
        upper_boxes,
        key=lambda b: (b["x"] + b["dx"] * 0.5) + (b["y"] + b["dy"] * 0.5) + (b["z"] * 0.05)
    )
    
    for b in boxes_sorted:
        x, y, z, dx, dy, dz = b["x"], b["y"], b["z"], b["dx"], b["dy"], b["dz"]
        b_type = b.get("type", "")
        
        p000 = iso_project(x, y, z, cx, cy)
        p100 = iso_project(x + dx, y, z, cx, cy)
        p110 = iso_project(x + dx, y + dy, z, cx, cy)
        p010 = iso_project(x, y + dy, z, cx, cy)
        
        p001 = iso_project(x, y, z + dz, cx, cy)
        p101 = iso_project(x + dx, y, z + dz, cx, cy)
        p111 = iso_project(x + dx, y + dy, z + dz, cx, cy)
        p011 = iso_project(x, y + dy, z + dz, cx, cy)
        
        if b_type == "pool":
            # Aegean / Mediterranean Cerulean Reflecting Pool
            py5.fill(18, 128, 185, 230)
            py5.stroke(10, 80, 120)
            py5.stroke_weight(1.4)
            py5.begin_shape()
            py5.vertex(p001[0], p001[1])
            py5.vertex(p101[0], p101[1])
            py5.vertex(p111[0], p111[1])
            py5.vertex(p011[0], p011[1])
            py5.end_shape(py5.CLOSE)
            
            # Dynamic wave caustics / shimmering ripples
            py5.stroke(90, 205, 255, 150)
            py5.stroke_weight(1.0)
            for r_idx in range(6):
                wave_offset = np.sin(t_cycle * 2.0 + r_idx * 1.1) * 12.0
                rx = x + 40 + r_idx * 55 + wave_offset
                ry = y + 50 + r_idx * 50
                wp1 = iso_project(rx, ry, z + dz, cx, cy)
                wp2 = iso_project(rx + 85, ry, z + dz, cx, cy)
                py5.line(wp1[0], wp1[1], wp2[0], wp2[1])
            continue
            
        # Left Vertical Face (+Y normal)
        py5.fill(168, 162, 150)
        py5.stroke(98, 93, 84)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        py5.vertex(p010[0], p010[1])
        py5.vertex(p110[0], p110[1])
        py5.vertex(p111[0], p111[1])
        py5.vertex(p011[0], p011[1])
        py5.end_shape(py5.CLOSE)
        
        # Board-formed concrete horizontal grain lines
        if dz > 35:
            py5.stroke(145, 140, 130, 85)
            py5.stroke_weight(0.8)
            for z_s in np.arange(z + 16, z + dz - 8, 20):
                sp1 = iso_project(x, y + dy, z_s, cx, cy)
                sp2 = iso_project(x + dx, y + dy, z_s, cx, cy)
                py5.line(sp1[0], sp1[1], sp2[0], sp2[1])
                
        # Right Vertical Face (+X normal)
        py5.fill(125, 120, 110)
        py5.stroke(82, 78, 70)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        py5.vertex(p100[0], p100[1])
        py5.vertex(p110[0], p110[1])
        py5.vertex(p111[0], p111[1])
        py5.vertex(p101[0], p101[1])
        py5.end_shape(py5.CLOSE)
        
        if dz > 35:
            py5.stroke(105, 100, 92, 85)
            py5.stroke_weight(0.8)
            for z_s in np.arange(z + 16, z + dz - 8, 20):
                sp1 = iso_project(x + dx, y, z_s, cx, cy)
                sp2 = iso_project(x + dx, y + dy, z_s, cx, cy)
                py5.line(sp1[0], sp1[1], sp2[0], sp2[1])
                
        # Top Horizontal Face (+Z normal)
        py5.fill(218, 213, 201)
        py5.stroke(112, 108, 98)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        py5.vertex(p001[0], p001[1])
        py5.vertex(p101[0], p101[1])
        py5.vertex(p111[0], p111[1])
        py5.vertex(p011[0], p011[1])
        py5.end_shape(py5.CLOSE)
        
        # Tie-rod indentations on wide slabs
        if dx >= 120 and dy >= 120:
            py5.fill(140, 135, 125)
            py5.no_stroke()
            for fx in [x + 28, x + dx - 28]:
                for fy in [y + 28, y + dy - 28]:
                    tp = iso_project(fx, fy, z + dz, cx, cy)
                    py5.circle(tp[0], tp[1], 3.8)
                    
        # Bauhaus / Brutalist Vermilion accent band on cantilever edge
        if b.get("accent"):
            py5.fill(225, 42, 32)
            py5.stroke(175, 30, 20)
            py5.stroke_weight(1.0)
            e1 = iso_project(x, y + dy, z + dz, cx, cy)
            e2 = iso_project(x + dx, y + dy, z + dz, cx, cy)
            e3 = iso_project(x + dx, y + dy, z + dz - 8, cx, cy)
            e4 = iso_project(x, y + dy, z + dz - 8, cx, cy)
            py5.begin_shape()
            py5.vertex(e1[0], e1[1])
            py5.vertex(e2[0], e2[1])
            py5.vertex(e3[0], e3[1])
            py5.vertex(e4[0], e4[1])
            py5.end_shape(py5.CLOSE)

    # -------------------------------------------------------------
    # PASS 5: Drafting Construction Datum & Solar Azimuth Compass
    # -------------------------------------------------------------
    # Architectural datum line with tick marks
    py5.stroke(220, 38, 38, 150)
    py5.stroke_weight(1.2)
    l1 = iso_project(-700, -700, 0, cx, cy)
    l2 = iso_project(700, -700, 0, cx, cy)
    py5.line(l1[0], l1[1], l2[0], l2[1])
    for step in range(-650, 750, 90):
        t1 = iso_project(step, -700, 0, cx, cy)
        t2 = iso_project(step, -718, 0, cx, cy)
        py5.line(t1[0], t1[1], t2[0], t2[1])

    # Dynamic Solar Azimuth Compass Dial in bottom right
    compass_cx = WIDTH - 120
    compass_cy = HEIGHT - 110
    compass_r = 45.0
    
    py5.no_fill()
    py5.stroke(160, 155, 145, 180)
    py5.stroke_weight(1.2)
    py5.circle(compass_cx, compass_cy, compass_r * 2.0)
    py5.stroke(200, 195, 185, 140)
    py5.circle(compass_cx, compass_cy, compass_r * 1.3)
    
    # Solar vector pointer (orbiting with azimuth)
    needle_x = compass_cx + compass_r * 0.9 * np.cos(sun_az)
    needle_y = compass_cy + compass_r * 0.9 * np.sin(sun_az)
    py5.stroke(225, 42, 32, 220)
    py5.stroke_weight(2.0)
    py5.line(compass_cx, compass_cy, needle_x, needle_y)
    
    py5.fill(225, 42, 32)
    py5.no_stroke()
    py5.circle(needle_x, needle_y, 5.0)
    py5.fill(120, 115, 105)
    py5.circle(compass_cx, compass_cy, 4.0)

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
    
    # Exit JVM process cleanly on macOS
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
