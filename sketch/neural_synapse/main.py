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
SIZE = PREVIEW_SIZE

# Graph params
NUM_NODES = 180
nodes_pos_base = np.random.uniform(-450, 450, (NUM_NODES, 3))
connections = []
MAX_DIST = 190
for i in range(NUM_NODES):
    for j in range(i + 1, NUM_NODES):
        d = np.linalg.norm(nodes_pos_base[i] - nodes_pos_base[j])
        if d < MAX_DIST:
            connections.append((i, j, d))

# State
signals = [] # {'from', 'to', 'p', 's', 'col', 'history'}
node_states = np.zeros(NUM_NODES)
node_cooldown = np.zeros(NUM_NODES)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 2, 8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def project(pos, angle_y, angle_x):
    # Rotate
    ry = np.array([[np.cos(angle_y), 0, np.sin(angle_y)], [0, 1, 0], [-np.sin(angle_y), 0, np.cos(angle_y)]])
    rx = np.array([[1, 0, 0], [0, np.cos(angle_x), -np.sin(angle_x)], [0, np.sin(angle_x), np.cos(angle_x)]])
    p = rx @ ry @ pos
    
    z = p[2] + 700
    scale = 750 / z
    x = p[0] * scale + py5.width / 2
    y = p[1] * scale + py5.height / 2
    return x, y, scale

def trigger_signal(from_idx, to_idx, col):
    d = np.linalg.norm(nodes_pos_base[from_idx] - nodes_pos_base[to_idx])
    speed = 5.5 / (d + 1)
    signals.append({'from': from_idx, 'to': to_idx, 'p': 0.0, 's': speed, 'col': col, 'hist': []})

def draw():
    global signals, node_states, node_cooldown
    
    py5.background(3, 3, 12)
    t = py5.frame_count / TOTAL_FRAMES
    angle_y = t * py5.TWO_PI * 0.1
    angle_x = np.sin(t * py5.PI) * 0.2
    
    # Update states
    node_states *= 0.92
    node_cooldown = np.maximum(0, node_cooldown - 1)
    
    # Continuous seeding
    if py5.frame_count % 8 == 0:
        start_node = np.random.randint(NUM_NODES)
        neighbors = [c[1] if c[0] == start_node else c[0] for c in connections if c[0] == start_node or c[1] == start_node]
        if neighbors:
            target = np.random.choice(neighbors)
            col = py5.color(255, 0, 180) if np.random.random() > 0.4 else py5.color(0, 255, 255)
            trigger_signal(start_node, target, col)

    # Draw Connections
    py5.stroke_weight(1.0)
    for i, j, d in connections:
        x1, y1, s1 = project(nodes_pos_base[i], angle_y, angle_x)
        x2, y2, s2 = project(nodes_pos_base[j], angle_y, angle_x)
        # Pulse connection based on endpoint activity
        activity = max(node_states[i], node_states[j])
        py5.stroke(40 + activity * 60, 45 + activity * 70, 90 + activity * 100, 20 + activity * 80)
        py5.line(x1, y1, x2, y2)
    
    # Update and Draw Signals
    py5.blend_mode(py5.ADD)
    new_signals = []
    for s in signals:
        s['p'] += s['s']
        x1, y1, scale1 = project(nodes_pos_base[s['from']], angle_y, angle_x)
        x2, y2, scale2 = project(nodes_pos_base[s['to']], angle_y, angle_x)
        px = x1 + (x2 - x1) * s['p']
        py = y1 + (y2 - y1) * s['p']
        avg_s = (scale1 + scale2) / 2
        
        # Draw Trail
        s['hist'].append((px, py))
        if len(s['hist']) > 12: s['hist'].pop(0)
        for i, (hx, hy) in enumerate(s['hist']):
            alpha = (i / len(s['hist'])) * 200
            py5.stroke(s['col'], alpha)
            py5.stroke_weight(1.5 * avg_s)
            if i > 0:
                prev_x, prev_y = s['hist'][i-1]
                py5.line(prev_x, prev_y, hx, hy)

        if s['p'] >= 1.0:
            target = s['to']
            node_states[target] = 1.0
            if node_cooldown[target] == 0:
                node_cooldown[target] = 8
                neighbors = [c[1] if c[0] == target else c[0] for c in connections if c[0] == target or c[1] == target]
                branch_count = np.random.randint(1, 4)
                for _ in range(min(branch_count, len(neighbors))):
                    next_node = np.random.choice(neighbors)
                    if next_node != s['from']:
                        trigger_signal(target, next_node, s['col'])
        else:
            # Head glow
            py5.fill(s['col'], 100)
            py5.ellipse(px, py, 8 * avg_s, 8 * avg_s)
            py5.fill(255, 150)
            py5.ellipse(px, py, 3 * avg_s, 3 * avg_s)
            new_signals.append(s)
    signals = new_signals

    # Draw Nodes
    for i in range(NUM_NODES):
        x, y, s = project(nodes_pos_base[i], angle_y, angle_x)
        activation = node_states[i]
        if activation > 0.02:
            # Core
            py5.fill(220, 240, 255, 100 + activation * 155)
            py5.ellipse(x, y, 5 * s * (1 + activation), 5 * s * (1 + activation))
            # Bloom
            for layer in range(3):
                py5.fill(0, 200, 255, (3-layer) * activation * 30)
                r = (layer + 1) * 12 * s * activation
                py5.ellipse(x, y, r, r)
        else:
            py5.fill(50, 50, 110, 50)
            py5.ellipse(x, y, 2.5 * s, 2.5 * s)

    py5.blend_mode(py5.BLEND)
    py5.no_stroke()

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
        subprocess.run(["cp", "-f", mid, str(SKETCH_DIR / "preview.png")], check=True)

py5.run_sketch()
