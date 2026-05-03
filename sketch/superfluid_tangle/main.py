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

# Simulation params
NUM_VORTICES = 10
NUM_PARTICLES = 3000
vortex_pos = np.random.uniform(-400, 400, (NUM_VORTICES, 2))
vortex_strength = np.random.choice([-1, 1], NUM_VORTICES) * 1800.0
particles = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 2))
particle_history = [particles.copy()]

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 2, 12)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()
    # Set color mode once globally if possible, or at least at start of draw
    py5.color_mode(py5.HSB, 1.0)

def get_velocity(pos, v_pos, v_strength):
    diff = pos[:, np.newaxis, :] - v_pos[np.newaxis, :, :] 
    dist_sq = np.sum(diff**2, axis=-1)
    dist_sq = np.maximum(dist_sq, 800.0)
    r_perp = np.stack([-diff[:, :, 1], diff[:, :, 0]], axis=-1)
    vel = np.sum(v_strength[np.newaxis, :, np.newaxis] * r_perp / dist_sq[:, :, np.newaxis], axis=1)
    return vel

def draw():
    global vortex_pos, particles, particle_history
    
    # Use HSB 1.0 for everything
    py5.color_mode(py5.HSB, 1.0)
    py5.background(0.66, 0.8, 0.05) # Dark navy in HSB
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Update vortices
    v_vel = get_velocity(vortex_pos, vortex_pos, vortex_strength)
    v_noise = 2.0 * np.array([py5.noise(v[0]*0.1, v[1]*0.1, t*10) - 0.5 for v in vortex_pos]).reshape(-1, 1)
    vortex_pos += v_vel * 0.04 + v_noise
    
    # Update particles
    p_vel = get_velocity(particles, vortex_pos, vortex_strength)
    particles += p_vel * 0.04
    
    dist_from_center = np.linalg.norm(particles, axis=1, keepdims=True)
    particles -= 0.001 * particles * (dist_from_center > 1200)
    
    particle_history.append(particles.copy())
    if len(particle_history) > 30:
        particle_history.pop(0)
        
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    
    py5.blend_mode(py5.SCREEN)
    
    vel_mag = np.linalg.norm(p_vel, axis=1)
    
    # Draw trails
    for i in range(1, len(particle_history)):
        alpha = (i / len(particle_history)) * 0.5
        h1 = particle_history[i-1]
        h2 = particle_history[i]
        
        py5.begin_shape(py5.LINES)
        for p_idx in range(NUM_PARTICLES):
            v_norm = np.clip(vel_mag[p_idx] / 20.0, 0, 1)
            # Cyan (0.5) to Violet (0.8)
            py5.stroke(0.5 + 0.3 * v_norm, 0.7, 1.0, alpha)
            py5.vertex(h1[p_idx, 0], h1[p_idx, 1])
            py5.vertex(h2[p_idx, 0], h2[p_idx, 1])
        py5.end_shape()
        
    # Draw vortex cores
    py5.stroke_weight(2.0)
    for v in vortex_pos:
        py5.stroke(0, 0, 1.0, 0.8) # White in HSB
        py5.point(v[0], v[1])
        pulse = 8 + 6 * np.sin(py5.frame_count * 0.15)
        py5.stroke(0.8, 0.8, 0.8, 0.4) # Violet in HSB
        py5.stroke_weight(pulse)
        py5.point(v[0], v[1])
        py5.stroke_weight(2.0)

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
        # Ensure it overwrites
        subprocess.run(["cp", "-f", mid, str(SKETCH_DIR / "preview.png")], check=True)

py5.run_sketch()
