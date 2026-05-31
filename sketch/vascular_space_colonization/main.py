from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.spatial import cKDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

# Space Colonization parameters
NUM_ATTRACTORS = 60000
ATTRACTION_DISTANCE = 150.0
KILL_DISTANCE = 8.0
BRANCH_LENGTH = 6.0

attractors = None
branches = None
branch_parents = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global attractors, branches, branch_parents
    
    # Generate attractors in a noisy pattern (to make it look organic)
    x = np.random.rand(NUM_ATTRACTORS) * W
    y = np.random.rand(NUM_ATTRACTORS) * H
    
    # Filter out a central circle to let it grow inward, or just start from center and grow outward
    dist = np.sqrt((x - W/2)**2 + (y - H/2)**2)
    valid = dist > 100 # Leave a small gap in the center
    attractors = np.column_stack((x[valid], y[valid]))
    
    # Initialize root branch in the center
    branches = np.array([[W / 2, H / 2]])
    branch_parents = np.array([-1]) # Root has no parent

def update_colonization():
    global attractors, branches, branch_parents
    
    if len(attractors) == 0:
        return False
        
    # Build KD-tree of current branches
    tree = cKDTree(branches)
    
    # For each attractor, find the closest branch
    dists, closest_branch_indices = tree.query(attractors)
    
    # Filter by attraction distance
    valid_mask = (dists < ATTRACTION_DISTANCE) & (dists > KILL_DISTANCE)
    
    if not np.any(valid_mask):
        # No attractors are within range, grow randomly or do nothing
        return True # Still running, just waiting for attractors? Actually if none are in range, it's stuck.
        # Let's expand attraction distance temporarily if stuck
        
    # Get active attractors and their targets
    active_attr = attractors[valid_mask]
    target_branches = closest_branch_indices[valid_mask]
    
    # Accumulate growth vectors for each branch
    # Multiple attractors can pull on the same branch
    unique_targets, inverse_indices = np.unique(target_branches, return_inverse=True)
    
    new_branches = []
    new_parents = []
    
    for i, branch_idx in enumerate(unique_targets):
        # Find all attractors pulling this branch
        pulling_attr = active_attr[inverse_indices == i]
        
        # Calculate average direction
        dirs = pulling_attr - branches[branch_idx]
        lengths = np.sqrt(np.sum(dirs**2, axis=1))
        # Normalize
        dirs = dirs / lengths[:, np.newaxis]
        
        avg_dir = np.mean(dirs, axis=0)
        avg_len = np.linalg.norm(avg_dir)
        
        if avg_len > 0:
            avg_dir /= avg_len
            
            # Create new branch
            new_pos = branches[branch_idx] + avg_dir * BRANCH_LENGTH
            new_branches.append(new_pos)
            new_parents.append(branch_idx)
            
    if new_branches:
        branches = np.vstack((branches, new_branches))
        branch_parents = np.concatenate((branch_parents, new_parents))
        
    # Remove attractors that are too close to ANY branch
    # Re-query with new tree to be precise, or just use the old tree + new branches
    tree = cKDTree(branches)
    dists, _ = tree.query(attractors)
    keep_mask = dists > KILL_DISTANCE
    attractors = attractors[keep_mask]
    
    return True

def draw():
    global attractors, branches, branch_parents
    
    py5.background(10, 5, 10)
    
    # We do several growth steps per frame
    for _ in range(5):
        update_colonization()
        
    # Draw attractors (Energy spores)
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    if len(attractors) > 0:
        py5.fill(255, 100, 150, 150)
        py5.no_stroke()
        # Drawing 60k points via py5 is slow, let's use pixels directly or just not draw them 
        # or draw them as a faint background. Let's draw them via pixels.
        coords = attractors.astype(np.int32)
        v = (coords[:, 0] >= 0) & (coords[:, 0] < W) & (coords[:, 1] >= 0) & (coords[:, 1] < H)
        vc = coords[v]
        pixels[vc[:, 1], vc[:, 0]] = [255, 255, 50, 150] # Pinkish points
        
    py5.update_np_pixels()
    
    # Draw branches
    # We only need to draw the connections
    py5.stroke(100, 255, 200, 200) # Cyan branches
    py5.stroke_weight(2.0)
    
    # Batch lines for extreme performance
    # Py5 begin_shape(py5.LINES)
    py5.begin_shape(py5.LINES)
    # To optimize, we only draw the newly added branches each frame, or redraw all.
    # Redrawing all 100,000 branches might drop FPS, but Py5 can handle 100k lines in 30fps.
    # Let's draw all.
    for i in range(1, len(branches)):
        p1 = branches[i]
        p2 = branches[branch_parents[i]]
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
    py5.end_shape()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Branches: {len(branches)} | Attractors left: {len(attractors)}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
