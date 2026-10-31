"""
Kinetic Radiolaria Siliceous Skeleton Morphogenesis 2D
4K 60fps 720 frames (12.0s seamless loop)

Deep-sea micro-paleontological architecture and siliceous biomineralization of
a colonial Polycystina radiolarian skeleton (homage to Ernst Haeckel's H.M.S.
Challenger monograph). Nested concentric geodesic silica shells (cortical,
medullary, and nuclear microsphere) and radiating tri-carinate spiculae spines
rotate and breathe in microscopic hydrodynamic suspension on antique zoological vellum.
"""

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import py5

# --- Artwork Constants ---
WORK_NAME = "kinetic_radiolaria_siliceous_skeleton_morphogenesis_2d"
WIDTH = 3840
HEIGHT = 2160
FPS = 60
TOTAL_FRAMES = 720
DURATION_SEC = 12.0

SKETCH_DIR = Path(__file__).resolve().parent
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_FILE = SKETCH_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_MP4 = SKETCH_DIR / "output.mp4"

START_TIME = 0.0

# --- Geodesic Geometry Setup ---
def get_icosahedron():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    verts = [
        (-1,  phi, 0), ( 1,  phi, 0), (-1, -phi, 0), ( 1, -phi, 0),
        (0, -1,  phi), (0,  1,  phi), (0, -1, -phi), (0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1),
    ]
    verts = np.array(verts, dtype=np.float64)
    verts /= np.linalg.norm(verts, axis=1, keepdims=True)
    
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]
    return verts, faces

def subdivide_geodesic(verts, faces, frequency=2):
    v_dict = {}
    new_verts = list(verts)
    
    for idx, v in enumerate(new_verts):
        v_dict[tuple(np.round(v, 6))] = idx

    new_faces = []
    edges_set = set()

    for f in faces:
        v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
        grid = []
        for i in range(frequency + 1):
            row = []
            for j in range(frequency + 1 - i):
                k = frequency - i - j
                w0, w1, w2 = i / frequency, j / frequency, k / frequency
                pt = w0 * v0 + w1 * v1 + w2 * v2
                pt = pt / np.linalg.norm(pt)
                key = tuple(np.round(pt, 6))
                if key in v_dict:
                    row.append(v_dict[key])
                else:
                    idx = len(new_verts)
                    new_verts.append(pt)
                    v_dict[key] = idx
                    row.append(idx)
            grid.append(row)
        
        for i in range(frequency):
            for j in range(frequency - i):
                pA = grid[i][j]
                pB = grid[i+1][j]
                pC = grid[i][j+1]
                new_faces.append((pA, pB, pC))
                for e in [(pA, pB), (pB, pC), (pC, pA)]:
                    edges_set.add(tuple(sorted(e)))
                if j + 1 < frequency - i:
                    pD = grid[i+1][j+1]
                    new_faces.append((pB, pD, pC))
                    for e in [(pB, pD), (pD, pC), (pC, pB)]:
                        edges_set.add(tuple(sorted(e)))

    return np.array(new_verts, dtype=np.float64), new_faces, np.array(list(edges_set), dtype=np.int32)

# Precompute geodesic models
BASE_ICO_V, BASE_ICO_F = get_icosahedron()
CORT_V, CORT_F, CORT_E = subdivide_geodesic(BASE_ICO_V, BASE_ICO_F, frequency=3)
MED_V, MED_F, MED_E = subdivide_geodesic(BASE_ICO_V, BASE_ICO_F, frequency=2)
NUC_V, NUC_F, NUC_E = subdivide_geodesic(BASE_ICO_V, BASE_ICO_F, frequency=1)

# Generate secondary by-spines directions (vertices of cortical shell not in icosahedron)
BY_SPINES = []
for idx, v in enumerate(CORT_V):
    dists = np.linalg.norm(BASE_ICO_V - v, axis=1)
    if np.min(dists) > 0.12:
        seed_val = math.sin(v[0] * 12.3 + v[1] * 34.5 + v[2] * 56.7)
        length_factor = 0.16 + 0.10 * (seed_val * 0.5 + 0.5)
        BY_SPINES.append((v, length_factor))

# Cytoplasmic granules streaming along axopodia
np.random.seed(42)
NUM_GRANULES = 240
GRANULE_DATA = []
for _ in range(NUM_GRANULES):
    ray = np.random.randn(3)
    ray = ray / np.linalg.norm(ray)
    speed = np.random.uniform(0.6, 1.4)
    phase = np.random.uniform(0.0, 1.0)
    color_type = np.random.choice(["amber", "celadon", "gold"])
    size = np.random.uniform(3.5, 7.0)
    GRANULE_DATA.append((ray, speed, phase, color_type, size))

def rotation_matrix(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return Rz @ Ry @ Rx

def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)

def setup():
    global START_TIME
    START_TIME = time.time()
    py5.frame_rate(FPS)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K render: {TOTAL_FRAMES} frames @ {FPS} fps...")

def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES)
    omega = 2.0 * math.pi

    # 1. Background & Laid-Paper Watermark
    py5.background(248, 245, 238) # Antique zoological parchment

    # Subtle laid-paper chain-lines
    py5.stroke(232, 226, 214, 120)
    py5.stroke_weight(1.0)
    for x in range(120, WIDTH, 80):
        py5.line(x, 80, x, HEIGHT - 80)
    for y in range(120, HEIGHT, 80):
        py5.line(80, y, WIDTH - 80, y)

    # 2. Kinematics & Rotation Matrix
    theta_y = tau * 2.0 * math.pi # Exact 360 deg seamless rotation
    theta_x = 0.28 * math.sin(omega * tau)
    theta_z = 0.18 * math.cos(omega * tau)
    R = rotation_matrix(theta_x, theta_y, theta_z)

    # Osmotic breathing modulation
    breathe = math.sin(2.0 * omega * tau)
    R_cort = 680.0 * (1.0 + 0.035 * breathe)
    R_med = 360.0 * (1.0 + 0.045 * math.sin(2.0 * omega * tau + 0.5))
    R_nuc = 160.0 * (1.0 + 0.055 * math.sin(2.0 * omega * tau + 1.0))
    R_spine = 980.0 * (1.0 + 0.025 * breathe)

    # Rotate 3D geometry
    r_cort_v = (R @ (CORT_V * R_cort).T).T
    r_med_v = (R @ (MED_V * R_med).T).T
    r_nuc_v = (R @ (NUC_V * R_nuc).T).T
    r_ico_v = (R @ BASE_ICO_V.T).T

    cam_dist = 3600.0
    cx = WIDTH / 2.0
    cy = HEIGHT / 2.0 + 30.0

    # 3. Cytoplasmic Streaming Axopodia & Zooxanthellae (Deep background layer)
    for ray, speed, phase_off, ctype, gsize in GRANULE_DATA:
        r_ray = R @ ray
        travel_range = R_spine + 220.0 - R_med
        t_cycle = (tau * speed + phase_off) % 1.0
        r_dist = R_med + travel_range * t_cycle
        
        pt3d = r_ray * r_dist
        if pt3d[2] < 200:
            denom = max(100.0, cam_dist - pt3d[2])
            sc = cam_dist / denom
            gu = cx + pt3d[0] * sc
            gv = cy + pt3d[1] * sc
            
            py5.no_stroke()
            if ctype == "amber":
                py5.fill(212, 151, 46, int(110 + 90 * sc))
            elif ctype == "celadon":
                py5.fill(46, 125, 107, int(110 + 90 * sc))
            else:
                py5.fill(229, 170, 56, int(120 + 100 * sc))
            py5.circle(gu, gv, gsize * sc)
            py5.fill(255, 252, 240, 160)
            py5.circle(gu - 0.7 * sc, gv - 0.7 * sc, gsize * 0.35 * sc)

    # 4. Spines: 12 primary tri-carinate spines
    spine_segments = []
    for axis in r_ico_v:
        perp1 = np.cross(axis, np.array([0, 0, 1]))
        if np.linalg.norm(perp1) < 1e-3:
            perp1 = np.cross(axis, np.array([0, 1, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(axis, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        angles = [0, 2 * math.pi / 3, 4 * math.pi / 3]
        fins = [math.cos(a) * perp1 + math.sin(a) * perp2 for a in angles]
        
        r_steps = np.linspace(R_nuc, R_spine, 20)
        for i in range(len(r_steps) - 1):
            rA, rB = r_steps[i], r_steps[i+1]
            pA = axis * rA
            pB = axis * rB
            mid_z = (pA[2] + pB[2]) * 0.5
            
            wA = 32.0 * math.sin(math.pi * (rA - R_nuc) / (R_spine - R_nuc))
            wB = 32.0 * math.sin(math.pi * (rB - R_nuc) / (R_spine - R_nuc))
            
            spine_segments.append(("spine_core", mid_z, pA, pB))
            for f in fins:
                fA = pA + f * wA
                fB = pB + f * wB
                spine_segments.append(("spine_fin", mid_z, fA, fB))
                spine_segments.append(("spine_strut", mid_z, pA, fA))

    # B. Secondary By-Spines (Spinulae) projecting outward from cortical shell
    for dir_v, l_factor in BY_SPINES:
        r_dir = R @ dir_v
        p_base = r_dir * R_cort
        p_tip = r_dir * (R_cort + R_cort * l_factor)
        mid_z = (p_base[2] + p_tip[2]) * 0.5
        spine_segments.append(("by_spine", mid_z, p_base, p_tip))

    # C. Shell Edges
    cort_edges_items = []
    for e in CORT_E:
        pA, pB = r_cort_v[e[0]], r_cort_v[e[1]]
        mid_z = (pA[2] + pB[2]) * 0.5
        cort_edges_items.append(("cortical", mid_z, pA, pB))

    med_edges_items = []
    for e in MED_E:
        pA, pB = r_med_v[e[0]], r_med_v[e[1]]
        mid_z = (pA[2] + pB[2]) * 0.5
        med_edges_items.append(("medullary", mid_z, pA, pB))

    nuc_edges_items = []
    for e in NUC_E:
        pA, pB = r_nuc_v[e[0]], r_nuc_v[e[1]]
        mid_z = (pA[2] + pB[2]) * 0.5
        nuc_edges_items.append(("nuclear", mid_z, pA, pB))

    # Combine all renderables and sort by mid_z ascending (back to front)
    all_renderables = spine_segments + cort_edges_items + med_edges_items + nuc_edges_items
    all_renderables.sort(key=lambda item: item[1])

    # Convert 3D endpoints to 2D line segments in batches
    lines_back = []
    lines_med = []
    lines_nuc = []
    lines_cort_front = []
    lines_cort_highlight = []
    lines_spine_front = []
    lines_spine_fin = []

    for item in all_renderables:
        cat = item[0]
        z = item[1]
        pA, pB = item[2], item[3]
        
        dA = max(100.0, cam_dist - pA[2])
        scA = cam_dist / dA
        uA = cx + pA[0] * scA
        vA = cy + pA[1] * scA
        
        dB = max(100.0, cam_dist - pB[2])
        scB = cam_dist / dB
        uB = cx + pB[0] * scB
        vB = cy + pB[1] * scB

        seg = [uA, vA, uB, vB]

        if cat == "nuclear":
            lines_nuc.append(seg)
        elif cat == "medullary":
            lines_med.append(seg)
        elif cat == "cortical":
            if z < 0:
                lines_back.append(seg)
            else:
                lines_cort_front.append(seg)
                lines_cort_highlight.append([uA - 1.2, vA - 1.2, uB - 1.2, vB - 1.2])
        elif cat == "spine_core":
            if z < 0:
                lines_back.append(seg)
            else:
                lines_spine_front.append(seg)
        elif cat in ("spine_fin", "spine_strut", "by_spine"):
            if z < 0:
                lines_back.append(seg)
            else:
                lines_spine_fin.append(seg)

    # Draw batches with py5.lines for sub-second 4K frame execution
    if lines_back:
        py5.stroke(110, 105, 120, 85)
        py5.stroke_weight(1.8)
        py5.lines(np.array(lines_back, dtype=np.float32))

    if lines_med:
        py5.stroke(140, 88, 53, 160)
        py5.stroke_weight(2.4)
        py5.lines(np.array(lines_med, dtype=np.float32))

    if lines_nuc:
        py5.stroke(212, 151, 46, 230)
        py5.stroke_weight(3.6)
        py5.lines(np.array(lines_nuc, dtype=np.float32))
        py5.stroke(255, 240, 200, 240)
        py5.stroke_weight(1.6)
        py5.lines(np.array(lines_nuc, dtype=np.float32))

    if lines_spine_fin:
        py5.stroke(140, 95, 65, 180)
        py5.stroke_weight(2.0)
        py5.lines(np.array(lines_spine_fin, dtype=np.float32))

    if lines_cort_front:
        py5.stroke(16, 26, 38, 240)
        py5.stroke_weight(4.0)
        py5.lines(np.array(lines_cort_front, dtype=np.float32))
        py5.stroke(255, 252, 245, 200)
        py5.stroke_weight(1.4)
        py5.lines(np.array(lines_cort_highlight, dtype=np.float32))

    if lines_spine_front:
        py5.stroke(14, 22, 34, 255)
        py5.stroke_weight(4.8)
        py5.lines(np.array(lines_spine_front, dtype=np.float32))
        py5.stroke(212, 151, 46, 210)
        py5.stroke_weight(1.8)
        py5.lines(np.array(lines_spine_front, dtype=np.float32))

    # 7. Pore fenestrations on front-facing cortical facets
    py5.no_fill()
    for f_idx, f in enumerate(CORT_F):
        p0, p1, p2 = r_cort_v[f[0]], r_cort_v[f[1]], r_cort_v[f[2]]
        face_center = (p0 + p1 + p2) / 3.0
        norm = np.cross(p1 - p0, p2 - p0)
        norm_len = np.linalg.norm(norm)
        if norm_len > 1e-4:
            norm = norm / norm_len
            if norm[2] > 0.08 and face_center[2] > -80:
                fc_denom = max(100.0, cam_dist - face_center[2])
                fc_scale = cam_dist / fc_denom
                fc_u = cx + face_center[0] * fc_scale
                fc_v = cy + face_center[1] * fc_scale
                
                phi_facet = math.sin(f_idx * 1.618) * math.pi
                r_pore = 18.0 * fc_scale * (1.0 + 0.22 * math.sin(2.0 * omega * tau + phi_facet))
                
                py5.stroke(20, 32, 46, int(150 + 105 * norm[2]))
                py5.stroke_weight(2.6 * fc_scale)
                py5.circle(fc_u, fc_v, r_pore * 2.0)
                
                py5.stroke(180, 135, 80, int(110 + 100 * norm[2]))
                py5.stroke_weight(1.5 * fc_scale)
                py5.circle(fc_u, fc_v, r_pore * 1.35)

    # 8. Silica beads at cortical nodes (vertices)
    for p_idx, p in enumerate(r_cort_v):
        if p[2] > -40:
            denom = max(100.0, cam_dist - p[2])
            sc = cam_dist / denom
            u = cx + p[0] * sc
            v = cy + p[1] * sc
            
            py5.no_stroke()
            py5.fill(212, 151, 46, int(190 + 65 * (p[2] / R_cort)))
            py5.circle(u, v, 9.0 * sc)
            py5.fill(255, 252, 242, 230)
            py5.circle(u - 1.5 * sc, v - 1.5 * sc, 3.6 * sc)

    # 9. Monograph Archival Borders and Scholarly Typography
    py5.no_fill()
    py5.stroke(36, 45, 55)
    py5.stroke_weight(4.0)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke_weight(2.0)
    py5.rect(72, 72, WIDTH - 144, HEIGHT - 144)

    # Corner rosettes
    for rx, ry in [(66, 66), (WIDTH - 66, 66), (66, HEIGHT - 66), (WIDTH - 66, HEIGHT - 66)]:
        py5.fill(212, 151, 46)
        py5.no_stroke()
        py5.circle(rx, ry, 12)
        py5.fill(26, 42, 58)
        py5.circle(rx, ry, 4)

    # Archival Monograph Header
    py5.fill(26, 42, 58)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(24)
    py5.text("VOYAGE OF H.M.S. CHALLENGER — ZOOLOGY VOL. XVIII", WIDTH / 2.0, 96)
    py5.text_size(36)
    py5.text("RADIOLARIA (POLYCYSTINA) — HEXACONTIUM ASTERACANTHION", WIDTH / 2.0, 134)
    py5.text_size(20)
    py5.fill(140, 88, 53)
    py5.text("CONCENTRIC SILICEOUS LATTICE SPHERES & TRI-CARINATE COLUMELLAE", WIDTH / 2.0, 182)

    # Bottom Anatomical Indices and Scale Bar
    py5.fill(26, 42, 58)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("FIG. 1: CORTICAL SPHERE (OUTER FENESTRATED LATTICE) — 100 µm", 108, HEIGHT - 104)
    py5.text_size(18)
    py5.fill(140, 88, 53)
    py5.text("FIG. 2: MEDULLARY SPHERE & CENTRAL NUCLEAR MICROSPHERE", 108, HEIGHT - 76)

    py5.fill(26, 42, 58)
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("MICROSCOPIC CAMERA LUCIDA — 4K GENERATIVE MORPHOGENESIS", WIDTH - 108, HEIGHT - 104)
    
    py5.stroke(26, 42, 58)
    py5.stroke_weight(2.5)
    py5.line(WIDTH - 348, HEIGHT - 84, WIDTH - 108, HEIGHT - 84)
    py5.line(WIDTH - 348, HEIGHT - 92, WIDTH - 348, HEIGHT - 76)
    py5.line(WIDTH - 228, HEIGHT - 89, WIDTH - 228, HEIGHT - 79)
    py5.line(WIDTH - 108, HEIGHT - 92, WIDTH - 108, HEIGHT - 76)

    # Save frame
    frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at frame 0
    if frame == 0:
        py5.save_frame(str(PREVIEW_FILE))
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_FILE}")

    if (frame + 1) % 60 == 0 or frame + 1 == TOTAL_FRAMES:
        elapsed = time.time() - START_TIME
        fps_calc = (frame + 1) / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - (frame + 1)) / max(0.01, fps_calc)
        print(f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")

def finish_and_encode():
    global START_TIME
    total_elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        str(OUTPUT_MP4)
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
            
    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
