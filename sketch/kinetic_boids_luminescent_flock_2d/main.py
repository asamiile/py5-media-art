import py5
import numpy as np
import os
import shutil

# ----------------------------------------------------------------------------
# 8. kinetic_boids_luminescent_flock_2d
# ----------------------------------------------------------------------------
# Concept: A swarm of glowing entities simulating flocking behavior (boids).
# Technique: Separation, alignment, cohesion algorithms. Glowing additive trails.
# Palette: Bioluminescence (deep ocean blue, cyan, aqua, glowing green).
# ----------------------------------------------------------------------------

WORK_NAME = "kinetic_boids_luminescent_flock_2d"
FRAMES_DIR = f"sketch/{WORK_NAME}/frames"
OUTPUT_MP4 = f"sketch/{WORK_NAME}/{WORK_NAME}.mp4"
TOTAL_FRAMES = 900
FPS = 30
SIZE = (1920, 1080)

# Boids parameters
NUM_BOIDS = 400
MAX_SPEED = 6.0
MAX_FORCE = 0.15
PERCEPTION_RADIUS = 100.0
DESIRED_SEPARATION = 30.0

# Arrays for boids
positions = None
velocities = None
accelerations = None
colors = None

def get_palette():
    return [
        "#011627", # Deep Ocean Dark (Background)
        "#00d2ff", # Bright Cyan
        "#3a7bd5", # Deep Blue
        "#20bdff", # Sky Blue
        "#00f2fe", # Aqua
        "#4facfe", # Light Blue
        "#73ffd1"  # Glowing Green
    ]

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(get_palette()[0])
    
    # Enable additive blending
    py5.blend_mode(py5.ADD)
    
    global positions, velocities, accelerations, colors
    
    positions = np.random.rand(NUM_BOIDS, 2) * [SIZE[0], SIZE[1]]
    
    angles = np.random.rand(NUM_BOIDS) * 2 * np.pi
    speeds = np.random.rand(NUM_BOIDS) * MAX_SPEED
    velocities = np.column_stack((np.cos(angles) * speeds, np.sin(angles) * speeds))
    
    accelerations = np.zeros((NUM_BOIDS, 2))
    
    # Assign colors from palette (excluding background)
    palette = get_palette()[1:]
    color_choices = np.random.choice(len(palette), NUM_BOIDS)
    colors = np.array([py5.color(c) for c in np.array(palette)[color_choices]])
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)

def draw():
    global positions, velocities, accelerations
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        return

    # Subtractive background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(py5.color(get_palette()[0], 20)) # Very transparent background for long trails
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Calculate boids forces (vectorized for speed)
    # We will use simple approximations or distance matrices
    
    # Distance matrix (can be heavy for large N, but N=400 is fine)
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dist_sq = np.sum(diff**2, axis=-1)
    np.fill_diagonal(dist_sq, np.inf)
    dist = np.sqrt(dist_sq)
    
    # Alignment
    align_mask = dist < PERCEPTION_RADIUS
    align_counts = np.sum(align_mask, axis=1)[:, np.newaxis]
    align_sum = np.dot(align_mask.astype(float), velocities)
    align_steer = np.zeros_like(velocities)
    valid_align = np.squeeze(align_counts > 0)
    if np.any(valid_align):
        align_avg = align_sum[valid_align] / align_counts[valid_align]
        speed = np.linalg.norm(align_avg, axis=1, keepdims=True)
        speed[speed == 0] = 1.0
        align_avg = (align_avg / speed) * MAX_SPEED
        align_steer[valid_align] = align_avg - velocities[valid_align]
        # Limit force
        force_norm = np.linalg.norm(align_steer, axis=1, keepdims=True)
        exceed = np.squeeze(force_norm > MAX_FORCE)
        if np.any(exceed):
            align_steer[exceed] = (align_steer[exceed] / force_norm[exceed]) * MAX_FORCE
            
    # Cohesion
    coh_sum = np.dot(align_mask.astype(float), positions)
    coh_steer = np.zeros_like(velocities)
    if np.any(valid_align):
        coh_avg = coh_sum[valid_align] / align_counts[valid_align]
        desired = coh_avg - positions[valid_align]
        d_norm = np.linalg.norm(desired, axis=1, keepdims=True)
        d_norm[d_norm == 0] = 1.0
        desired = (desired / d_norm) * MAX_SPEED
        coh_steer[valid_align] = desired - velocities[valid_align]
        # Limit force
        force_norm = np.linalg.norm(coh_steer, axis=1, keepdims=True)
        exceed = np.squeeze(force_norm > MAX_FORCE)
        if np.any(exceed):
            coh_steer[exceed] = (coh_steer[exceed] / force_norm[exceed]) * MAX_FORCE
            
    # Separation
    sep_mask = dist < DESIRED_SEPARATION
    sep_counts = np.sum(sep_mask, axis=1)[:, np.newaxis]
    
    # Weight diff by 1/distance
    safe_dist = dist.copy()
    safe_dist[safe_dist == 0] = 1.0
    weighted_diff = diff / safe_dist[:, :, np.newaxis]
    sep_sum = np.sum(weighted_diff * sep_mask[:, :, np.newaxis], axis=1)
    
    sep_steer = np.zeros_like(velocities)
    valid_sep = np.squeeze(sep_counts > 0)
    if np.any(valid_sep):
        sep_avg = sep_sum[valid_sep] / sep_counts[valid_sep]
        s_norm = np.linalg.norm(sep_avg, axis=1, keepdims=True)
        s_norm[s_norm == 0] = 1.0
        sep_avg = (sep_avg / s_norm) * MAX_SPEED
        sep_steer[valid_sep] = sep_avg - velocities[valid_sep]
        # Limit force
        force_norm = np.linalg.norm(sep_steer, axis=1, keepdims=True)
        exceed = np.squeeze(force_norm > MAX_FORCE)
        if np.any(exceed):
            sep_steer[exceed] = (sep_steer[exceed] / force_norm[exceed]) * MAX_FORCE

    # Add a gentle pull towards the center to keep them on screen
    center_pull = [SIZE[0]/2, SIZE[1]/2] - positions
    c_norm = np.linalg.norm(center_pull, axis=1, keepdims=True)
    c_norm[c_norm == 0] = 1.0
    center_pull = (center_pull / c_norm) * 0.05
    
    # Introduce some noise to make movement organic
    noise_angles = np.array([py5.noise(p[0]*0.005, p[1]*0.005, py5.frame_count*0.01) * np.pi * 4 for p in positions])
    noise_steer = np.column_stack((np.cos(noise_angles), np.sin(noise_angles))) * 0.1

    accelerations = align_steer * 1.0 + coh_steer * 1.0 + sep_steer * 1.5 + center_pull + noise_steer

    velocities += accelerations
    
    # Limit max speed
    v_norm = np.linalg.norm(velocities, axis=1, keepdims=True)
    exceed = np.squeeze(v_norm > MAX_SPEED)
    if np.any(exceed):
        velocities[exceed] = (velocities[exceed] / v_norm[exceed]) * MAX_SPEED
        
    positions += velocities
    
    # Wrap around edges gracefully (using a margin)
    margin = 100
    positions[:, 0] = np.where(positions[:, 0] > py5.width + margin, -margin, positions[:, 0])
    positions[:, 0] = np.where(positions[:, 0] < -margin, py5.width + margin, positions[:, 0])
    positions[:, 1] = np.where(positions[:, 1] > py5.height + margin, -margin, positions[:, 1])
    positions[:, 1] = np.where(positions[:, 1] < -margin, py5.height + margin, positions[:, 1])

    # Draw boids
    py5.no_stroke()
    for i in range(NUM_BOIDS):
        px, py = positions[i]
        vx, vy = velocities[i]
        angle = np.arctan2(vy, vx)
        
        py5.fill(int(colors[i]))
        
        # Draw chevron/arrow shape
        py5.push_matrix()
        py5.translate(px, py)
        py5.rotate(angle)
        
        # Outer glow
        py5.fill(int(colors[i]) & 0xFFFFFF | (30 << 24)) # Add alpha
        py5.ellipse(0, 0, 20, 20)
        
        # Core shape
        py5.fill(int(colors[i]))
        py5.begin_shape()
        py5.vertex(8, 0)
        py5.vertex(-6, -4)
        py5.vertex(-3, 0)
        py5.vertex(-6, 4)
        py5.end_shape(py5.CLOSE)
        py5.pop_matrix()

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_path)
    
    # Save a specific preview image for review
    if py5.frame_count == TOTAL_FRAMES // 2:
        preview_path = f"sketch/{WORK_NAME}/{WORK_NAME}_p1.png"
        py5.save_frame(preview_path)
        
    if py5.frame_count % 30 == 0:
        print(f"Rendered {py5.frame_count}/{TOTAL_FRAMES} frames")

def compile_video():
    print("Compiling video with ffmpeg...")
    os.system(f"ffmpeg -y -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 {OUTPUT_MP4}")
    print(f"Video saved to {OUTPUT_MP4}")

if __name__ == '__main__':
    py5.run_sketch()
    compile_video()
    os._exit(0)
