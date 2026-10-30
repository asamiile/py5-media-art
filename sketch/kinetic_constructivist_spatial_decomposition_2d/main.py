"""
kinetic_constructivist_spatial_decomposition_2d
Dynamic constructivist architectural deconstruction and spatial tension on tactile ivory vellum.
Explores interlocking monolithic concrete slabs, shifting soft cast shadow volumes,
rhythmic terracotta and Prussian indigo counterpoints, and architectural drafting linework.

Anti-Clustering Compliance:
- Genre: Architectural / Brutalism / Geometric (Zero physics / particles)
- Background: Light tactile warm ivory vellum (#f7f4ea, luminance > 90%)
- Primitives: Solid planar polygons, architectural silhouette weights, cast shadow volumes,
  millimeter drafting grid, procedural diagonal cross-hatching. NO particles.
- Palette: Warm ivory canvas, brutalist ash concrete, terracotta vermilion, Prussian indigo,
  raw ochre sienna, drafting charcoal ink.

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
WORK_NAME = "kinetic_constructivist_spatial_decomposition_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180  # 25% progress point

# Canvas dimensions
WIDTH = 3840
HEIGHT = 2160

# Axonometric projection parameters (30-degree isometric)
COS_30 = 0.8660254037844386
SIN_30 = 0.5
SCALE = 1.18
ORIGIN_X = WIDTH * 0.50
ORIGIN_Y = HEIGHT * 0.56

# Sunlight direction for cast shadows & shading: high upper-left
SUN_X = -0.65
SUN_Y = -0.85
SUN_Z = 1.35
# Shadow projection factors on ground Z=0
SHADOW_SX = -SUN_X / SUN_Z  # ~0.481
SHADOW_SY = -SUN_Y / SUN_Z  # ~0.630


class ArchitecturalSlab:
    """Represents an oriented modular rectangular monolith in 3D architectural space."""
    def __init__(self, idx, x0, y0, z0, hx, hy, hz, style_type, motion_params):
        self.idx = idx
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.z0 = float(z0)
        self.hx = float(hx)  # half-width X
        self.hy = float(hy)  # half-depth Y
        self.hz = float(hz)  # half-height Z
        self.style_type = style_type  # 0: Concrete, 1: Terracotta, 2: Prussian Indigo, 3: Ochre Sienna
        self.motion = motion_params  # (ax, ay, az, kx, ky, kz, px, py, pz)
        self.has_hatching = (idx % 3 == 0) and (style_type in [0, 2])
        self.has_annotation = (idx % 7 == 0)

    def get_current_state(self, theta):
        """Computes current center position and depth sorting metric at loop angle theta."""
        ax, ay, az, kx, ky, kz, px, py, pz = self.motion
        cx = self.x0 + ax * np.sin(kx * theta + px)
        cy = self.y0 + ay * np.cos(ky * theta + py)
        cz = self.z0 + az * np.sin(kz * theta + pz)
        # Depth metric for back-to-front painter's sorting in isometric projection
        # Higher (x + y) is closer to camera; higher z is closer to viewer
        depth = (cx + cy) - 0.45 * cz
        return cx, cy, cz, depth


def project_iso(x, y, z):
    """Projects 3D world coordinates to 2D screen coordinates."""
    u = ORIGIN_X + (x - y) * COS_30 * SCALE
    v = ORIGIN_Y + (x + y) * SIN_30 * SCALE - z * SCALE
    return u, v


def create_architectural_ensemble():
    """Generates an ensemble of 46 interlocking constructivist architectural monoliths."""
    slabs = []
    idx = 0

    # 1. Base podium terraces and ground anchoring monoliths (Z ~ 0..120)
    base_grid = [
        (-480, -380, 40, 220, 180, 40, 0, (40, 20, 0, 1, 1, 1, 0.0, 0.5, 0.0)),
        (120, -420, 50, 260, 200, 50, 0, (20, 30, 0, 1, 1, 1, 1.2, 0.2, 0.0)),
        (-380, 180, 45, 200, 240, 45, 0, (30, 25, 0, 1, 1, 1, 2.1, 1.5, 0.0)),
        (220, 120, 60, 280, 220, 60, 0, (35, 40, 0, 1, 1, 1, 0.8, 2.7, 0.0)),
        (-120, -100, 70, 190, 190, 70, 1, (25, 25, 0, 1, 1, 1, 3.1, 0.9, 0.0)),  # Terracotta base anchor
    ]
    for x, y, z, hx, hy, hz, st, mot in base_grid:
        slabs.append(ArchitecturalSlab(idx, x, y, z, hx, hy, hz, st, mot))
        idx += 1

    # 2. Intermediate monolithic blocks and cantilevered gallery decks (Z ~ 120..380)
    mid_blocks = [
        # Left wing cantilevers
        (-560, -160, 180, 160, 140, 80, 2, (70, 30, 25, 1, 1, 2, 0.4, 1.8, 0.0)),  # Indigo cantilever
        (-340, -320, 220, 140, 200, 100, 0, (40, 60, 30, 1, 1, 1, 1.5, 0.6, 1.2)),
        (-220, -120, 260, 150, 130, 90, 0, (50, 50, 40, 1, 1, 2, 2.8, 2.0, 0.8)),
        (-480, 120, 210, 180, 120, 75, 3, (80, 35, 20, 1, 1, 1, 0.2, 3.0, 1.6)),   # Ochre gallery
        (-260, 280, 240, 130, 170, 95, 0, (45, 75, 35, 1, 1, 2, 1.9, 0.3, 2.4)),

        # Central intersecting crossing & atriums
        (0, -280, 230, 210, 110, 70, 0, (60, 40, 45, 1, 1, 1, 0.7, 1.4, 0.5)),
        (-80, 60, 270, 160, 160, 110, 1, (90, 70, 50, 1, 1, 2, 3.4, 0.8, 1.9)),  # Terracotta heart block
        (140, -160, 250, 170, 140, 85, 0, (55, 65, 30, 1, 1, 1, 2.3, 2.1, 0.3)),
        (80, 180, 280, 150, 180, 90, 2, (75, 45, 60, 1, 1, 2, 1.1, 3.3, 2.7)),   # Indigo crossing block

        # Right wing cantilevers
        (380, -320, 220, 160, 150, 80, 0, (45, 80, 35, 1, 1, 1, 0.9, 1.2, 1.4)),
        (460, -100, 260, 140, 180, 105, 3, (65, 50, 40, 1, 1, 2, 2.4, 0.5, 0.6)), # Ochre cantilever
        (340, 140, 240, 180, 130, 85, 0, (70, 60, 30, 1, 1, 1, 1.8, 2.6, 2.1)),
        (520, 260, 210, 150, 160, 75, 0, (40, 55, 25, 1, 1, 2, 0.3, 1.9, 1.0)),
    ]
    for x, y, z, hx, hy, hz, st, mot in mid_blocks:
        slabs.append(ArchitecturalSlab(idx, x, y, z, hx, hy, hz, st, mot))
        idx += 1

    # 3. Upper soaring monoliths, shear walls, and sky bridges (Z ~ 340..720)
    high_towers = [
        # Brutalist vertical pylons & towers
        (-380, -180, 420, 110, 100, 190, 0, (30, 45, 75, 1, 1, 1, 0.5, 2.2, 1.1)),
        (-160, -340, 450, 90, 110, 210, 2, (40, 60, 85, 1, 1, 2, 2.0, 1.1, 2.5)),  # Tall Indigo pylon
        (-280, 40, 480, 120, 120, 230, 1, (50, 35, 95, 1, 1, 1, 1.4, 0.3, 0.4)),   # Towering Terracotta monolith
        (-100, 260, 430, 100, 130, 180, 0, (35, 50, 70, 1, 1, 2, 3.0, 2.8, 1.7)),

        # Central high interlocking nexus
        (40, -120, 510, 130, 130, 240, 0, (60, 55, 110, 1, 1, 1, 0.8, 1.7, 3.1)), # Main central concrete spire
        (180, -260, 460, 110, 100, 190, 3, (45, 65, 80, 1, 1, 2, 2.7, 0.9, 0.8)),  # Ochre pylon
        (220, 40, 490, 105, 125, 220, 0, (55, 40, 90, 1, 1, 1, 1.6, 2.4, 2.0)),
        (120, 280, 440, 115, 110, 175, 2, (35, 55, 75, 1, 1, 2, 0.1, 1.5, 1.3)),  # Indigo tower
        (380, -80, 450, 100, 115, 200, 0, (40, 50, 85, 1, 1, 1, 2.5, 3.2, 0.2)),

        # Sky bridges and floating horizontal constructivist beams
        (-220, -180, 640, 280, 65, 35, 1, (110, 45, 40, 1, 1, 1, 0.6, 1.3, 2.2)), # High Terracotta beam
        (80, -80, 670, 65, 290, 35, 0, (40, 120, 45, 1, 1, 2, 2.2, 0.7, 1.5)),    # High transverse concrete deck
        (160, 120, 630, 260, 60, 30, 3, (100, 50, 35, 1, 1, 1, 1.7, 2.9, 0.9)),   # Ochre sky bridge
        (-60, 140, 660, 60, 270, 32, 2, (35, 110, 40, 1, 1, 2, 3.3, 1.8, 2.8)),   # Indigo sky deck
    ]
    for x, y, z, hx, hy, hz, st, mot in high_towers:
        slabs.append(ArchitecturalSlab(idx, x, y, z, hx, hy, hz, st, mot))
        idx += 1

    # 4. Detail modular counterpoint slabs (sliding tectonic plates)
    detail_plates = [
        (-440, -420, 320, 75, 75, 25, 3, (80, 80, 30, 2, 2, 1, 0.3, 1.1, 0.7)),
        (-580, 20, 340, 80, 70, 28, 0, (70, 60, 25, 1, 2, 2, 1.8, 2.4, 1.9)),
        (-140, -440, 310, 70, 85, 25, 0, (65, 85, 30, 2, 1, 1, 2.9, 0.4, 1.2)),
        (300, -420, 330, 85, 75, 30, 1, (90, 75, 35, 1, 1, 2, 0.9, 3.1, 2.4)),
        (560, -200, 310, 70, 80, 26, 2, (75, 90, 28, 2, 1, 1, 2.1, 1.6, 0.5)),
        (480, 160, 320, 80, 70, 25, 0, (80, 65, 32, 1, 2, 2, 1.2, 0.8, 3.0)),
        (260, 380, 300, 75, 85, 28, 3, (70, 80, 26, 2, 2, 1, 3.2, 2.2, 1.4)),
        (-180, 420, 290, 85, 75, 25, 0, (85, 70, 30, 1, 1, 2, 0.5, 1.9, 0.2)),
        (-380, 340, 330, 70, 80, 28, 1, (75, 85, 34, 2, 1, 1, 2.6, 0.2, 2.1)),
    ]
    for x, y, z, hx, hy, hz, st, mot in detail_plates:
        slabs.append(ArchitecturalSlab(idx, x, y, z, hx, hy, hz, st, mot))
        idx += 1

    return slabs


# Color palettes: (Top Face, Left Face, Right Face)
PALETTES = {
    # 0: Brutalist Ash Concrete & Limestone
    0: {
        "top": (236, 232, 223),
        "left": (205, 200, 190),
        "right": (166, 160, 148),
        "stroke": (32, 30, 28),
        "hatch": (148, 142, 130),
    },
    # 1: Constructivist Terracotta Vermilion
    1: {
        "top": (218, 68, 50),
        "left": (186, 50, 34),
        "right": (140, 30, 18),
        "stroke": (36, 18, 14),
        "hatch": (240, 100, 80),
    },
    # 2: Prussian Slate Indigo
    2: {
        "top": (46, 80, 110),
        "left": (30, 56, 80),
        "right": (20, 38, 56),
        "stroke": (12, 22, 32),
        "hatch": (75, 120, 160),
    },
    # 3: Raw Ochre Sienna
    3: {
        "top": (228, 162, 60),
        "left": (200, 136, 42),
        "right": (154, 100, 26),
        "stroke": (38, 26, 12),
        "hatch": (250, 195, 110),
    },
}

# Pre-instantiate the architectural ensemble
ENSEMBLE = create_architectural_ensemble()


def draw_tactile_vellum_background():
    """Draws warm unbleached ivory vellum canvas with architectural millimeter grid & annotations."""
    # Warm ivory background
    py5.background(247, 244, 234)

    # 1. Subtle secondary grid (every 60px)
    py5.stroke(232, 228, 218, 140)
    py5.stroke_weight(1.0)
    for x in range(0, WIDTH, 60):
        py5.line(x, 0, x, HEIGHT)
    for y in range(0, HEIGHT, 60):
        py5.line(0, y, WIDTH, y)

    # 2. Primary architectural drafting grid (every 180px)
    py5.stroke(218, 212, 198, 190)
    py5.stroke_weight(1.5)
    for x in range(0, WIDTH, 180):
        py5.line(x, 0, x, HEIGHT)
    for y in range(0, HEIGHT, 180):
        py5.line(0, y, WIDTH, y)

    # 3. Technical registration marks & drafting crosses
    py5.stroke(185, 178, 164, 220)
    py5.stroke_weight(2.0)
    cross_coords = [
        (180, 180), (WIDTH - 180, 180),
        (180, HEIGHT - 180), (WIDTH - 180, HEIGHT - 180),
        (WIDTH // 2, 180), (WIDTH // 2, HEIGHT - 180),
        (180, HEIGHT // 2), (WIDTH - 180, HEIGHT // 2)
    ]
    for cx, cy in cross_coords:
        py5.line(cx - 14, cy, cx + 14, cy)
        py5.line(cx, cy - 14, cx, cy + 14)
        py5.no_fill()
        py5.circle(cx, cy, 18)

    # 4. Subtle drafting border frame
    py5.stroke(200, 194, 180, 240)
    py5.stroke_weight(2.5)
    py5.no_fill()
    py5.rect(90, 90, WIDTH - 180, HEIGHT - 180)


def draw_ground_shadow(cx, cy, cz, hx, hy, hz):
    """Renders soft contact shadow volume projected onto ground Z=0."""
    # Project 4 bottom/top vertices to ground along sunlight direction
    # A box from z-hz to z+hz casts shadow from its elevated mass
    z_top = cz + hz
    z_bot = max(0.0, cz - hz)

    # Offsets on ground Z=0
    ox_top = z_top * SHADOW_SX
    oy_top = z_top * SHADOW_SY
    ox_bot = z_bot * SHADOW_SX
    oy_bot = z_bot * SHADOW_SY

    # Polygon encompassing the projected footprint
    # Screen coordinates of top shadow quad and base footprint
    pts_3d = [
        (cx - hx + ox_bot, cy - hy + oy_bot, 0),
        (cx + hx + ox_bot, cy - hy + oy_bot, 0),
        (cx + hx + ox_top, cy - hy + oy_top, 0),
        (cx + hx + ox_top, cy + hy + oy_top, 0),
        (cx - hx + ox_top, cy + hy + oy_top, 0),
        (cx - hx + ox_bot, cy + hy + oy_bot, 0),
    ]

    py5.no_stroke()
    # Layer 1: Soft diffuse penumbra
    py5.fill(30, 26, 22, 18)
    py5.begin_shape()
    for px, py, pz in pts_3d:
        u, v = project_iso(px * 1.02, py * 1.02, pz)
        py5.vertex(u, v)
    py5.end_shape(py5.CLOSE)

    # Layer 2: Core contact umbra
    py5.fill(24, 20, 18, 32)
    py5.begin_shape()
    for px, py, pz in pts_3d:
        u, v = project_iso(px, py, pz)
        py5.vertex(u, v)
    py5.end_shape(py5.CLOSE)


def draw_cross_hatching(v0, v1, v2, v3, hatch_color, spacing=14):
    """Draws architectural drafting diagonal cross-hatching inside a quad face."""
    # Interpolate lines across opposite edges
    py5.stroke(*hatch_color, 160)
    py5.stroke_weight(1.4)

    # Edge 0: v0 -> v1, Edge 1: v3 -> v2
    num_steps = max(3, int(np.hypot(v1[0] - v0[0], v1[1] - v0[1]) / spacing))
    for step in range(1, num_steps):
        t = step / float(num_steps)
        p0x = (1.0 - t) * v0[0] + t * v1[0]
        p0y = (1.0 - t) * v0[1] + t * v1[1]
        p1x = (1.0 - t) * v3[0] + t * v2[0]
        p1y = (1.0 - t) * v3[1] + t * v2[1]
        py5.line(p0x, p0y, p1x, p1y)


def draw_slab(slab, cx, cy, cz):
    """Renders the 3 visible faces of an axonometric slab with shading, hatching, and crisp ink contours."""
    hx, hy, hz = slab.hx, slab.hy, slab.hz
    pal = PALETTES[slab.style_type]

    # Calculate 8 corner vertices in world space
    # Top face corners (Z = cz + hz)
    t0 = project_iso(cx - hx, cy - hy, cz + hz)  # Back-Top
    t1 = project_iso(cx + hx, cy - hy, cz + hz)  # Right-Top
    t2 = project_iso(cx + hx, cy + hy, cz + hz)  # Front-Top
    t3 = project_iso(cx - hx, cy + hy, cz + hz)  # Left-Top

    # Bottom face corners (Z = cz - hz)
    b1 = project_iso(cx + hx, cy - hy, cz - hz)  # Right-Bottom
    b2 = project_iso(cx + hx, cy + hy, cz - hz)  # Front-Bottom
    b3 = project_iso(cx - hx, cy + hy, cz - hz)  # Left-Bottom

    stroke_col = pal["stroke"]

    # 1. Right Face (+X normal, oriented towards East/Right, shaded facet)
    # Vertices: t1, t2, b2, b1
    py5.fill(*pal["right"])
    py5.stroke(*stroke_col)
    py5.stroke_weight(2.8)
    py5.begin_shape()
    py5.vertex(t1[0], t1[1])
    py5.vertex(t2[0], t2[1])
    py5.vertex(b2[0], b2[1])
    py5.vertex(b1[0], b1[1])
    py5.end_shape(py5.CLOSE)

    # Hatching on select shaded right faces
    if slab.has_hatching:
        draw_cross_hatching(t1, t2, b2, b1, pal["hatch"], spacing=16)

    # 2. Left Face (+Y normal, oriented towards West/Left, glancing facet)
    # Vertices: t3, t2, b2, b3
    py5.fill(*pal["left"])
    py5.stroke(*stroke_col)
    py5.stroke_weight(2.8)
    py5.begin_shape()
    py5.vertex(t3[0], t3[1])
    py5.vertex(t2[0], t2[1])
    py5.vertex(b2[0], b2[1])
    py5.vertex(b3[0], b3[1])
    py5.end_shape(py5.CLOSE)

    # 3. Top Face (+Z normal, oriented upward, receiving direct sunlight)
    # Vertices: t0, t1, t2, t3
    py5.fill(*pal["top"])
    py5.stroke(*stroke_col)
    py5.stroke_weight(3.5)
    py5.begin_shape()
    py5.vertex(t0[0], t0[1])
    py5.vertex(t1[0], t1[1])
    py5.vertex(t2[0], t2[1])
    py5.vertex(t3[0], t3[1])
    py5.end_shape(py5.CLOSE)

    # Heavy silhouette outline on key edges
    py5.stroke(*stroke_col, 240)
    py5.stroke_weight(4.2)
    py5.line(t0[0], t0[1], t1[0], t1[1])
    py5.line(t0[0], t0[1], t3[0], t3[1])
    py5.line(t2[0], t2[1], b2[0], b2[1])
    py5.line(t1[0], t1[1], b1[0], b1[1])
    py5.line(t3[0], t3[1], b3[0], b3[1])

    # 4. Technical drafting callout annotations on select slabs
    if slab.has_annotation:
        py5.stroke(140, 40, 30, 200) if slab.style_type == 1 else py5.stroke(60, 65, 75, 180)
        py5.stroke_weight(1.4)
        # Leader line extending from top edge
        lx0, ly0 = t2[0], t2[1]
        lx1, ly1 = lx0 + 55, ly0 - 45
        lx2 = lx1 + 90
        py5.line(lx0, ly0, lx1, ly1)
        py5.line(lx1, ly1, lx2, ly1)
        py5.circle(lx0, ly0, 5)
        py5.circle(lx2, ly1, 4)


def setup():
    """py5 setup lifecycle method: initializes 4K window and output directories."""
    py5.size(WIDTH, HEIGHT)
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[Setup Complete] Canvas: {WIDTH}x{HEIGHT} | Output: {OUTPUT_MP4}")


def draw():
    """py5 draw lifecycle method: renders frame, sorts depth, compiles MP4 on completion."""
    frame = py5.frame_count

    # Normalized loop parameter theta in [0, 2*pi)
    theta = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES) * 2.0 * np.pi

    # 1. Draw tactile ivory vellum canvas with millimeter architectural grid
    draw_tactile_vellum_background()

    # 2. Evaluate current 3D position and depth metric for all slabs
    evaluated_slabs = []
    for slab in ENSEMBLE:
        cx, cy, cz, depth = slab.get_current_state(theta)
        evaluated_slabs.append((depth, slab, cx, cy, cz))

    # 3. First pass: render all ground contact shadows (drawn below all geometry)
    for _, slab, cx, cy, cz in evaluated_slabs:
        draw_ground_shadow(cx, cy, cz, slab.hx, slab.hy, slab.hz)

    # 4. Second pass: back-to-front painter's sorting for solid geometry
    # Smallest depth is furthest from camera; render first
    evaluated_slabs.sort(key=lambda item: item[0])

    for _, slab, cx, cy, cz in evaluated_slabs:
        draw_slab(slab, cx, cy, cz)

    # 5. Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Constructivist preview captured: {PREVIEW_PATH}")

    # Progress logging every 60 frames
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 6. Finalize animation on reaching total frame count
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
