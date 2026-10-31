"""
kinetic_girih_arabesque_interlacing_strapwork_2d
Illuminated medieval Islamic Girih geometric strapwork and continuous interlaced star polygon tessellation.
Features a monumental 16-point central star medallion, four 12-point corner medallions, four 8-point
edge cartouches, interconnected bridging gold strapwork, and enameled lapis lazuli and Persian turquoise inlays.

Anti-Clustering Compliance:
- Genre: Textile / Calligraphy / Procedural Craft (Zero physics / particles)
- Background: Antique illuminated manuscript vellum (#f7f2e4, luminance > 90%)
- Primitives: Interlocking star polygons, strapwork cords with gilded bevels, enameled jewel inlays,
  continuous connecting bridges, sacred geometry drafting grid. NO particles.
- Palette: Burnished gold leaf (#d4af37), lapis lazuli (#162a45), Persian turquoise (#0d9488),
  carmine ruby (#991b1b), walnut sepia ink (#261912).

Format: 720 frames @ 60 FPS (12.0s seamless loop)
Native Output: 3840x2160 (Retina 4K master)
"""

import os
import shutil
import subprocess
import sys
import numpy as np
import py5

# Work configuration
WORK_NAME = "kinetic_girih_arabesque_interlacing_strapwork_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180

# Canvas dimensions
WIDTH = 3840
HEIGHT = 2160
CX = WIDTH // 2
CY = HEIGHT // 2
STRAP_W = 20.0

# Master colors
GOLD_HIGHLIGHT = (252, 242, 185)
GOLD_MAIN = (218, 175, 55)
GOLD_SHADOW = (180, 138, 38)
SEPIA_INK = (34, 22, 16)
LAPIS_BLUE = (22, 42, 72)
TURQUOISE = (13, 140, 130)
CARMINE = (160, 24, 34)


def setup():
    """py5 setup lifecycle method."""
    py5.size(WIDTH, HEIGHT)
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[Setup Complete] Canvas: {WIDTH}x{HEIGHT} | Output: {OUTPUT_MP4}")


def draw_strap_segment(p0, p1, fill_col, is_over=True, width_val=STRAP_W):
    """Draws a segment of gold strapwork with directional bevel highlight and crisp ink borders."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    L = np.hypot(dx, dy)
    if L < 1.0:
        return
    nx = -dy / L * (width_val / 2.0)
    ny = dx / L * (width_val / 2.0)

    # Core gold strap body
    py5.fill(*fill_col)
    py5.no_stroke()
    py5.begin_shape()
    py5.vertex(p0[0] + nx, p0[1] + ny)
    py5.vertex(p1[0] + nx, p1[1] + ny)
    py5.vertex(p1[0] - nx, p1[1] - ny)
    py5.vertex(p0[0] - nx, p0[1] - ny)
    py5.end_shape(py5.CLOSE)

    # Bevel highlight on sunlit top-left edge
    py5.stroke(*GOLD_HIGHLIGHT, 230)
    py5.stroke_weight(2.0)
    py5.line(p0[0] + nx, p0[1] + ny, p1[0] + nx, p1[1] + ny)

    # Dark walnut sepia ink borders
    py5.stroke(*SEPIA_INK)
    py5.stroke_weight(2.2)
    py5.line(p0[0] + nx, p0[1] + ny, p1[0] + nx, p1[1] + ny)
    py5.line(p0[0] - nx, p0[1] - ny, p1[0] - nx, p1[1] - ny)


def draw_star_medallion(cx, cy, r_outer, n_pts, step, theta, rot_speed):
    """Renders a fully interlaced Girih star medallion with enameled inlays."""
    rot = theta * rot_speed
    angles = np.linspace(0, 2.0 * np.pi, n_pts, endpoint=False) + rot
    vx = cx + r_outer * np.cos(angles)
    vy = cy + r_outer * np.sin(angles)
    verts = np.column_stack([vx, vy])

    # 1. Enameled circular backing (Lapis Lazuli)
    py5.fill(*LAPIS_BLUE)
    py5.stroke(185, 145, 45)
    py5.stroke_weight(3.5)
    py5.circle(cx, cy, r_outer * 2.08)

    # 2. Concentric inner turquoise star rosette
    inner_r = r_outer * 0.44 * (1.0 + 0.04 * np.sin(theta * 2.0))
    inner_angles = np.linspace(0, 2.0 * np.pi, n_pts, endpoint=False) - rot * 0.5
    ivx = cx + inner_r * np.cos(inner_angles)
    ivy = cy + inner_r * np.sin(inner_angles)
    py5.fill(*TURQUOISE)
    py5.stroke(220, 180, 60)
    py5.stroke_weight(2.0)
    py5.begin_shape()
    for x, y in zip(ivx, ivy):
        py5.vertex(x, y)
    py5.end_shape(py5.CLOSE)

    # 3. Core Carmine ruby jewel
    core_r = r_outer * 0.22
    py5.fill(*CARMINE)
    py5.stroke(245, 225, 160)
    py5.stroke_weight(2.5)
    py5.circle(cx, cy, core_r * 2)

    # Center gold pip
    py5.fill(*GOLD_MAIN)
    py5.no_stroke()
    py5.circle(cx, cy, core_r * 0.6)

    # 4. Generate star polygon cords
    lines = []
    for i in range(n_pts):
        j = (i + step) % n_pts
        lines.append((verts[i], verts[j], i))

    # Pass 1: Underpass cords
    for p0, p1, idx in lines:
        if idx % 2 == 1:
            draw_strap_segment(p0, p1, GOLD_SHADOW, is_over=False)

    # Pass 2: Overpass cords
    for p0, p1, idx in lines:
        if idx % 2 == 0:
            draw_strap_segment(p0, p1, GOLD_MAIN, is_over=True)

    return verts


def draw_connecting_strapwork(centers, theta):
    """Draws bridging gold strapwork connecting the medallions across the vellum canvas."""
    py5.stroke(170, 130, 40, 180)
    py5.stroke_weight(STRAP_W)

    # Connect central medallion to 4 corners and 4 edges
    c_center = centers["center"]
    for key, c_pos in centers.items():
        if key == "center":
            continue
        p0 = c_center
        p1 = c_pos
        # Draw dynamic braided double-strap bridge
        draw_strap_segment(p0, p1, GOLD_MAIN, is_over=True, width_val=STRAP_W * 0.85)


def draw_manuscript_ground(theta):
    """Draws warm antique manuscript vellum with sacred geometric drafting lines."""
    # Warm unbleached vellum ground
    py5.background(247, 242, 228)

    # Sacred geometry radial guidelines
    py5.stroke(215, 180, 55, 38)
    py5.stroke_weight(1.5)
    py5.no_fill()

    # Concentric circles
    for r in [320, 680, 1020, 1360, 1700]:
        r_dyn = r * (1.0 + 0.015 * np.sin(theta + r * 0.002))
        py5.circle(CX, CY, r_dyn * 2)

    # 32 radial ray lines
    for i in range(32):
        ang = i * (2.0 * np.pi / 32) + 0.015 * np.sin(theta)
        py5.line(CX, CY, CX + 1900 * np.cos(ang), CY + 1900 * np.sin(ang))

    # Outer illuminated border frame
    py5.stroke(170, 130, 45, 140)
    py5.stroke_weight(3.0)
    py5.rect(80, 80, WIDTH - 160, HEIGHT - 160)
    py5.stroke(210, 175, 60, 90)
    py5.stroke_weight(1.5)
    py5.rect(100, 100, WIDTH - 200, HEIGHT - 200)

    # Corner rosette ornaments
    for cpx, cpy in [(100, 100), (WIDTH - 100, 100), (100, HEIGHT - 100), (WIDTH - 100, HEIGHT - 100)]:
        py5.stroke(180, 140, 50, 200)
        py5.stroke_weight(2.0)
        py5.circle(cpx, cpy, 48)
        py5.circle(cpx, cpy, 24)


def draw():
    """py5 draw lifecycle method."""
    frame = py5.frame_count

    # Normalized loop angle theta in [0, 2*pi)
    theta = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES) * 2.0 * np.pi

    # 1. Antique manuscript vellum with sacred geometry drafting grid
    draw_manuscript_ground(theta)

    # Dynamic breathing radii
    r_center = 680 * (1.0 + 0.06 * np.sin(theta))
    r_corner = 400 * (1.0 - 0.04 * np.sin(theta))
    r_edge = 340 * (1.0 + 0.05 * np.cos(theta))

    # Medallion center positions
    centers = {
        "center": np.array([CX, CY], dtype=float),
        "c_tl": np.array([660, 520], dtype=float),
        "c_tr": np.array([WIDTH - 660, 520], dtype=float),
        "c_bl": np.array([660, HEIGHT - 520], dtype=float),
        "c_br": np.array([WIDTH - 660, HEIGHT - 520], dtype=float),
        "e_top": np.array([CX, 380], dtype=float),
        "e_bot": np.array([CX, HEIGHT - 380], dtype=float),
        "e_left": np.array([440, CY], dtype=float),
        "e_right": np.array([WIDTH - 440, CY], dtype=float),
    }

    # 2. Render connecting gold strapwork bridges between medallions
    draw_connecting_strapwork(centers, theta)

    # 3. Render 4 Corner 12-point star medallions
    for key in ["c_tl", "c_tr", "c_bl", "c_br"]:
        cp = centers[key]
        speed = 0.5 if "l" in key else -0.5
        draw_star_medallion(cp[0], cp[1], r_corner, 12, 4, theta, rot_speed=speed)

    # 4. Render 4 Edge 8-point star cartouches
    for key in ["e_top", "e_bot", "e_left", "e_right"]:
        ep = centers[key]
        speed = -0.6 if "top" in key or "bot" in key else 0.6
        draw_star_medallion(ep[0], ep[1], r_edge, 8, 3, theta, rot_speed=speed)

    # 5. Monumental central 16-point star medallion
    draw_star_medallion(CX, CY, r_center, 16, 6, theta, rot_speed=0.3)

    # 6. Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Girih Arabesque preview captured: {PREVIEW_PATH}")

    # Progress report
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 7. Finalize animation on reaching total frame count
    if frame == TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master 4K MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "17",
            "-preset", "slow",
            OUTPUT_MP4
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")
            shutil.rmtree(FRAMES_DIR, ignore_errors=True)
            print("[Render Cleanup] Temporary frames directory removed.")
        else:
            print(f"[FFmpeg Error] {res.stderr}")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
