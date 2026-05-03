from pathlib import Path
import subprocess
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()

def get_icosphere(subdivisions=2):
    phi = (1 + np.sqrt(5)) / 2
    v = np.array([
        [-1,  phi,  0], [ 1,  phi,  0], [-1, -phi,  0], [ 1, -phi,  0],
        [ 0, -1,  phi], [ 0,  1,  phi], [ 0, -1, -phi], [ 0,  1, -phi],
        [ phi,  0, -1], [ phi,  0,  1], [-phi,  0, -1], [-phi,  0,  1]
    ])
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    
    faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]
    
    for _ in range(subdivisions):
        new_faces = []
        midpoints = {}
        
        def get_midpoint(i1, i2, v):
            key = tuple(sorted((i1, i2)))
            if key in midpoints:
                return midpoints[key], v
            m = (v[i1] + v[i2]) / 2
            m = m / np.linalg.norm(m)
            v = np.vstack([v, m])
            idx = len(v) - 1
            midpoints[key] = idx
            return idx, v
        
        for f in faces:
            a, v = get_midpoint(f[0], f[1], v)
            b, v = get_midpoint(f[1], f[2], v)
            c, v = get_midpoint(f[2], f[0], v)
            new_faces.extend([
                [f[0], a, c],
                [f[1], b, a],
                [f[2], c, b],
                [a, b, c]
            ])
        faces = new_faces
        
    return v, faces

# Global geometry - Increase subdivisions for more detail
vertices, faces = get_icosphere(4)

def draw():
    py5.background(1, 2, 6)  # Deepest abyss
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Rotate vertices
    angle_x = py5.frame_count * 0.005
    angle_y = py5.frame_count * 0.007
    angle_z = py5.frame_count * 0.003
    
    def rot_x(a): return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    def rot_y(a): return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    def rot_z(a): return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    
    rmat = rot_x(angle_x) @ rot_y(angle_y) @ rot_z(angle_z)
    rotated = vertices @ rmat
    
    # Spherical Inversion with larger R and pulse
    # We want it to fill the screen
    inv_R = 400 + 200 * np.cos(2 * np.pi * t)
    norm_sq = np.sum(rotated**2, axis=-1, keepdims=True)
    
    # More aggressive organic noise
    shell_noise = 1.0 + 0.4 * np.array([py5.noise(v[0]*1.2 + t, v[1]*1.2 + t, v[2]*1.2 + t) for v in rotated]).reshape(-1, 1)
    inverted = (rotated * shell_noise) / np.maximum(norm_sq, 0.001) * inv_R
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.blend_mode(py5.SCREEN)
    
    edges = set()
    for f in faces:
        edges.add(tuple(sorted((f[0], f[1]))))
        edges.add(tuple(sorted((f[1], f[2]))))
        edges.add(tuple(sorted((f[2], f[0]))))
    
    # Draw logic with better scale
    # 1. Base Skeleton (Bone White)
    py5.stroke(249, 246, 238, 40)
    py5.stroke_weight(0.6)
    py5.begin_shape(py5.LINES)
    for e in edges:
        p1, p2 = inverted[e[0]], inverted[e[1]]
        if np.linalg.norm(p1-p2) < 600:
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
    py5.end_shape()
    
    # 2. Electric Cyan Glow
    py5.stroke(64, 224, 208, 25)
    py5.stroke_weight(2.0)
    py5.begin_shape(py5.LINES)
    for e in edges:
        p1, p2 = inverted[e[0]], inverted[e[1]]
        if np.linalg.norm(p1-p2) < 600:
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
    py5.end_shape()
    
    # 3. Floating "Pollen" (Accent Particles)
    py5.stroke_weight(3.0)
    for i in range(40):
        # Deterministic but pseudo-random movement
        idx = (i * 137 + py5.frame_count) % len(inverted)
        p = inverted[idx]
        offset = 20 * np.array([py5.noise(i, t), py5.noise(i+1, t), py5.noise(i+2, t)])
        pos = p + offset
        
        # Gold accent
        py5.stroke(255, 215, 0, 150)
        py5.point(pos[0], pos[1], pos[2])
        # Halo
        py5.stroke(255, 215, 0, 40)
        py5.stroke_weight(8.0)
        py5.point(pos[0], pos[1], pos[2])
        py5.stroke_weight(3.0)
        
    py5.pop_matrix()
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / "preview.png")], check=True)

py5.run_sketch()
