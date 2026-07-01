import py5
import numpy as np
from scipy.spatial import Voronoi
import os

# ----------------------------------------------------------------------------
# 10. generative_stained_glass_voronoi_2d
# ----------------------------------------------------------------------------
# Concept: A dynamic, shifting Voronoi diagram resembling stained glass.
#          The seeds move organically via Perlin noise.
# Technique: scipy.spatial.Voronoi for rapid computation. Closed polygons
#            are drawn with heavy black outlines to mimic lead came in glass.
# Palette: Cathedral Glass (ruby red, sapphire blue, emerald green,
#          vibrant yellow, deep indigo, with stark black outlines).
# ----------------------------------------------------------------------------

WORK_NAME = "generative_stained_glass_voronoi_2d"
FRAMES_DIR = f"sketch/{WORK_NAME}/frames"
OUTPUT_MP4 = f"sketch/{WORK_NAME}/{WORK_NAME}.mp4"
TOTAL_FRAMES = 900
FPS = 30
SIZE = (1920, 1080)
NUM_POINTS = 150

# Variables for the points
points_base = None
points_colors = None

def get_palette():
    return [
        "#c0392b", # Ruby Red
        "#2980b9", # Sapphire Blue
        "#27ae60", # Emerald Green
        "#f39c12", # Vibrant Yellow
        "#8e44ad", # Deep Indigo
        "#d35400", # Burnt Orange
    ]

def setup():
    global points_base, points_colors
    
    py5.size(SIZE[0], SIZE[1])
    py5.color_mode(py5.RGB, 255)
    py5.stroke_join(py5.ROUND)
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)
        
    # Initialize base points within the screen bounds
    points_base = np.zeros((NUM_POINTS, 2))
    points_colors = []
    
    palette = get_palette()
    for i in range(NUM_POINTS):
        points_base[i, 0] = py5.random(0, py5.width)
        points_base[i, 1] = py5.random(0, py5.height)
        
        # Pick a color
        color_hex = palette[int(py5.random(0, len(palette)))]
        points_colors.append(py5.color(color_hex))

def draw():
    global points_base, points_colors
    
    py5.background(10) # Dark base
    
    t = py5.frame_count * 0.005
    
    # Calculate current point positions using noise offsets
    current_points = np.copy(points_base)
    for i in range(NUM_POINTS):
        # Noise for x and y movement, unique to each point
        nx = py5.noise(i * 10, t)
        ny = py5.noise(i * 10 + 500, t)
        
        # Move up to 300 pixels from base position
        dx = py5.remap(nx, 0, 1, -300, 300)
        dy = py5.remap(ny, 0, 1, -300, 300)
        
        current_points[i, 0] += dx
        current_points[i, 1] += dy
        
    # To avoid infinite regions for our visible points, we add bounding box points
    # far outside the screen.
    padding = 2000
    bounding_points = np.array([
        [-padding, -padding],
        [py5.width + padding, -padding],
        [py5.width + padding, py5.height + padding],
        [-padding, py5.height + padding]
    ])
    
    all_points = np.vstack((current_points, bounding_points))
    
    # Compute Voronoi
    try:
        vor = Voronoi(all_points)
    except Exception as e:
        print(f"Voronoi computation failed this frame: {e}")
        return
        
    py5.stroke(10) # Black outlines mimicking lead
    py5.stroke_weight(6)
    
    # Draw the Voronoi regions corresponding to our original points
    for i in range(NUM_POINTS):
        region_index = vor.point_region[i]
        region_vertices_indices = vor.regions[region_index]
        
        # -1 indicates an infinite region, which shouldn't happen for our internal points
        # thanks to the bounding box, but we skip just in case.
        if -1 in region_vertices_indices or len(region_vertices_indices) == 0:
            continue
            
        # Get actual vertex coordinates
        polygon = vor.vertices[region_vertices_indices]
        
        # A stained glass "pulse" effect
        # We vary the brightness slightly based on noise
        pulse = py5.noise(i * 5, t * 2)
        alpha_val = py5.remap(pulse, 0, 1, 150, 255)
        
        py5.fill(points_colors[i], alpha_val)
        
        # Draw the polygon
        py5.begin_shape()
        for point in polygon:
            py5.vertex(point[0], point[1])
        py5.end_shape(py5.CLOSE)
        
    # Lighting overlay (a soft radial gradient or vignette)
    # Simple vignette via a large semi-transparent black rectangle
    py5.no_stroke()
    for r in range(10):
        alpha = py5.remap(r, 0, 9, 0, 15)
        py5.fill(0, alpha)
        # Draw concentric rects covering the screen edge to center
        margin = r * 50
        py5.rect(margin, margin, py5.width - margin*2, py5.height - margin*2)

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_path)
    
    if py5.frame_count == TOTAL_FRAMES // 2:
        preview_path = f"sketch/{WORK_NAME}/{WORK_NAME}_p1.png"
        py5.save_frame(preview_path)
        
    if py5.frame_count % 30 == 0:
        print(f"Rendered {py5.frame_count}/{TOTAL_FRAMES} frames")
        
    if py5.frame_count >= TOTAL_FRAMES:
        compile_video()
        py5.exit_sketch()

def compile_video():
    print("Compiling video with ffmpeg...")
    os.system(f"ffmpeg -y -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 {OUTPUT_MP4}")
    print(f"Video saved to {OUTPUT_MP4}")

if __name__ == '__main__':
    py5.run_sketch()
    os._exit(0)
