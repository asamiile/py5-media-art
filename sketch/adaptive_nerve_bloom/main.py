from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class Neuron:
    def __init__(self, x, y, node_id):
        self.x = x
        self.y = y
        self.id = node_id
        self.active = False
        self.activation = 0.0
        self.target_x = x
        self.target_y = y
        self.layer = node_id % 3

    def update(self, t):
        self.target_x += np.random.uniform(-0.5, 0.5)
        self.target_y += np.random.uniform(-0.5, 0.5)

        self.x = self.x * 0.95 + self.target_x * 0.05
        self.y = self.y * 0.95 + self.target_y * 0.05

        self.activation = max(0, self.activation - 0.02)

        if np.random.random() < 0.03:
            self.activate()

    def activate(self):
        self.activation = 1.0

class Synapse:
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2
        self.strength = 0.0
        self.signal = 0.0

    def update(self, t):
        dist = np.sqrt((self.n1.x - self.n2.x)**2 + (self.n1.y - self.n2.y)**2)

        if self.n1.activation > 0.5:
            self.signal = self.n1.activation
        else:
            self.signal = max(0, self.signal - 0.05)

        target_strength = 1.0 / (1.0 + dist / 100.0)
        self.strength = self.strength * 0.98 + target_strength * 0.02

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    global neurons, synapses

    num_neurons = 180
    neurons = []
    for i in range(num_neurons):
        x = np.random.uniform(0, SIZE[0])
        y = np.random.uniform(0, SIZE[1])
        neurons.append(Neuron(x, y, i))

    synapses = []
    for i, n1 in enumerate(neurons):
        for n2 in neurons[i+1:]:
            dist = np.sqrt((n1.x - n2.x)**2 + (n1.y - n2.y)**2)
            if dist < 250:
                synapses.append(Synapse(n1, n2))

def draw():
    t = py5.frame_count / FPS

    py5.background(15)
    py5.no_stroke()

    for neuron in neurons:
        neuron.update(t)

    for synapse in synapses:
        synapse.update(t)

    for synapse in synapses:
        alpha_val = int(synapse.strength * 150)
        color_mix = synapse.signal

        if color_mix > 0.5:
            color = py5.color(0, 255 * color_mix, 220)
        else:
            color = py5.color(255 * (1 - color_mix), 50, 220)

        py5.stroke(color, alpha_val)
        py5.stroke_weight(max(0.5, synapse.strength * 2))
        py5.line(synapse.n1.x, synapse.n1.y, synapse.n2.x, synapse.n2.y)

    py5.no_stroke()
    for neuron in neurons:
        brightness = 50 + neuron.activation * 200

        if neuron.layer == 0:
            color = py5.color(0, 255, 200, int(brightness))
        elif neuron.layer == 1:
            color = py5.color(255, 100, 200, int(brightness))
        else:
            color = py5.color(255, 200, 0, int(brightness))

        py5.fill(color)
        radius = 6 + neuron.activation * 14
        py5.circle(neuron.x, neuron.y, radius)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
