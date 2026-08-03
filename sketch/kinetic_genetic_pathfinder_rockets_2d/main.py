import math
import shutil
import subprocess
import sys
from pathlib import Path
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

# 16 seconds @ 60 FPS (Exactly 4 generations of 240 frames each)
DURATION_SEC = 16
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
LIFE_SPAN = 240
MUTATION_RATE = 0.015

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Offscreen drawing resolution (half 4K)
SIM_W, SIM_H = 1920, 1080

# Environment entities
class Obstacle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, px, py):
        return (self.x <= px <= self.x + self.w) and (self.y <= py <= self.y + self.h)

    def draw_3d(self):
        # Draw volumetric vector block in 4K
        py5.fill(255, 150, 20, 30)
        py5.stroke(255, 150, 20, 180)
        py5.stroke_weight(2)
        py5.rect(self.x, self.y, self.w, self.h)
        
        # Inner cybernetic grid line
        py5.line(self.x, self.y + self.h/2, self.x + self.w, self.y + self.h/2)

class DNA:
    def __init__(self, genes=None):
        if genes is not None:
            self.genes = genes
        else:
            self.genes = []
            for _ in range(LIFE_SPAN):
                angle = random.uniform(0, math.tau)
                # Max force vector
                self.genes.append((math.cos(angle) * 0.16, math.sin(angle) * 0.16))

    def crossover(self, partner):
        mid = random.randint(0, LIFE_SPAN - 1)
        child_genes = self.genes[:mid] + partner.genes[mid:]
        return DNA(child_genes)

    def mutate(self):
        for i in range(LIFE_SPAN):
            if random.random() < MUTATION_RATE:
                angle = random.uniform(0, math.tau)
                self.genes[i] = (math.cos(angle) * 0.16, math.sin(angle) * 0.16)

class Rocket:
    def __init__(self, dna=None):
        self.x = SIM_W / 2.0
        self.y = SIM_H - 100.0
        self.vx = 0.0
        self.vy = 0.0
        self.ax = 0.0
        self.ay = 0.0
        
        self.dna = dna if dna else DNA()
        self.hit_obstacle = False
        self.reached_target = False
        self.cycles_to_target = 0
        self.fitness = 0.0
        self.prev_x = self.x
        self.prev_y = self.y

    def apply_force(self, fx, fy):
        self.ax += fx
        self.ay += fy

    def update(self, step, obstacles, target):
        if self.hit_obstacle or self.reached_target:
            return

        self.prev_x = self.x
        self.prev_y = self.y

        # Apply DNA vector force
        fx, fy = self.dna.genes[step]
        self.apply_force(fx, fy)
        
        # Simple dynamics
        self.vx += self.ax
        self.vy += self.ay
        # Terminal velocity limit
        speed = math.hypot(self.vx, self.vy)
        if speed > 6.0:
            self.vx = (self.vx / speed) * 6.0
            self.vy = (self.vy / speed) * 6.0
            
        self.x += self.vx
        self.y += self.vy
        self.ax = 0.0
        self.ay = 0.0

        # Boundary checks
        if self.x < 0 or self.x > SIM_W or self.y < 0 or self.y > SIM_H:
            self.hit_obstacle = True

        # Obstacle checks
        for obs in obstacles:
            if obs.contains(self.x, self.y):
                self.hit_obstacle = True
                break

        # Target checks
        dist = math.hypot(self.x - target[0], self.y - target[1])
        if dist < 24.0:
            self.reached_target = True
            self.cycles_to_target = step

    def calc_fitness(self, target):
        d = math.hypot(self.x - target[0], self.y - target[1])
        # Proximity fitness
        self.fitness = 1.0 / (d + 1.0)
        
        if self.reached_target:
            # Time speed bonus (earlier arrival gets higher fitness multiplier)
            time_factor = LIFE_SPAN / max(10.0, float(self.cycles_to_target))
            self.fitness *= 15.0 * time_factor
        elif self.hit_obstacle:
            self.fitness *= 0.04

class Population:
    def __init__(self, size):
        self.rockets = [Rocket() for _ in range(size)]
        self.generation = 1
        self.success_count = 0
        self.prev_success_rate = 0.0
        self.best_rocket = self.rockets[0]

    def run(self, step, obstacles, target, pg):
        pg.begin_draw()
        pg.color_mode(py5.HSB, 360, 100, 100, 100)
        
        for r in self.rockets:
            r.update(step, obstacles, target)
            
            # Draw trails on offscreen graphics (fades organically via setup background)
            if not r.hit_obstacle:
                hue = 180 if not r.reached_target else 280
                sat = 90
                val = 95
                alpha = 25
                pg.stroke(hue, sat, val, alpha)
                pg.stroke_weight(1.5)
                pg.line(r.prev_x, r.prev_y, r.x, r.y)
                
        pg.end_draw()

    def evaluate(self, target):
        # Calculate fitness for all
        for r in self.rockets:
            r.calc_fitness(target)
            
        # Extract best rocket
        self.best_rocket = max(self.rockets, key=lambda r: r.fitness)
        
        # Count successes
        self.success_count = sum(1 for r in self.rockets if r.reached_target)
        self.prev_success_rate = (self.success_count / len(self.rockets)) * 100.0

    def selection_and_reproduction(self):
        new_rockets = []
        size = len(self.rockets)
        
        # Elite survival (Keep the best dna unchanged)
        new_rockets.append(Rocket(self.best_rocket.dna))
        
        for _ in range(size - 1):
            # Tournament selection (size 5)
            parent_a = self.tournament_select()
            parent_b = self.tournament_select()
            
            # Crossover & Mutate
            child_dna = parent_a.dna.crossover(parent_b.dna)
            child_dna.mutate()
            
            new_rockets.append(Rocket(child_dna))
            
        self.rockets = new_rockets
        self.generation += 1

    def tournament_select(self):
        candidates = random.sample(self.rockets, 5)
        return max(candidates, key=lambda r: r.fitness)

# Global variables
population = None
obstacles = []
target = (SIM_W / 2.0, 120.0)
pg = None
life_step = 0

def setup():
    global pg, population, obstacles
    py5.size(*SIZE)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize offscreen trail buffer
    pg = py5.create_graphics(SIM_W, SIM_H)
    pg.begin_draw()
    pg.background(6, 4, 10)  # Obsidian Space Void
    pg.end_draw()
    
    # Obstacle layout (Three layers creating a challenging slit labyrinth)
    obstacles = [
        Obstacle(SIM_W/2 - 600, SIM_H * 0.65, 800, 24),    # Slit on right side
        Obstacle(SIM_W/2 - 200, SIM_H * 0.42, 800, 24),    # Slit on left side
        Obstacle(SIM_W/2 - 500, SIM_H * 0.22, 600, 24)     # Narrow slits on edges
    ]
    
    population = Population(200)

def draw():
    global life_step
    fc = py5.frame_count
    
    # 1. Update Genetic Engine
    if life_step < LIFE_SPAN:
        population.run(life_step, obstacles, target, pg)
        life_step += 1
    else:
        # Evaluate current generation and perform selection
        population.evaluate(target)
        population.selection_and_reproduction()
        life_step = 0
        
        # Soft reset trail buffer on new generation (keep partial trails of previous gen)
        pg.begin_draw()
        pg.fill(6, 4, 10, 45)  # Fade out old trails on crossover transition
        pg.no_stroke()
        pg.rect(0, 0, SIM_W, SIM_H)
        pg.end_draw()

    # 2. Blit upscaled trail buffer to 4K canvas
    py5.image(pg, 0, 0, py5.width, py5.height)

    # 3. Draw active obstacles and target in 4K
    scale_x = py5.width / SIM_W
    scale_y = py5.height / SIM_H
    
    # Draw Target Gravity Well (Pulsing cybernetic rings)
    tx_4k = target[0] * scale_x
    ty_4k = target[1] * scale_y
    pulse = 1.0 + 0.12 * math.sin(fc * 0.15)
    
    py5.no_fill()
    py5.stroke(170, 40, 255, 60)
    py5.stroke_weight(2)
    py5.ellipse(tx_4k, ty_4k, 64 * pulse, 64 * pulse)
    py5.stroke(170, 40, 255, 120)
    py5.ellipse(tx_4k, ty_4k, 36 * pulse, 36 * pulse)
    py5.fill(170, 40, 255, 230)
    py5.ellipse(tx_4k, ty_4k, 12, 12)

    # Draw Obstacles (Volumetric amber blocks)
    for obs in obstacles:
        py5.fill(255, 150, 20, 20)
        py5.stroke(255, 150, 20, 180)
        py5.stroke_weight(2)
        py5.rect(obs.x * scale_x, obs.y * scale_y, obs.w * scale_x, obs.h * scale_y)
        # Structural center axis line
        py5.line(obs.x * scale_x, (obs.y + obs.h/2) * scale_y, (obs.x + obs.w) * scale_x, (obs.y + obs.h/2) * scale_y)

    # 4. Draw Active Swarm Rockets
    for r in population.rockets:
        if r.hit_obstacle or r.reached_target:
            continue
            
        rx_4k = r.x * scale_x
        ry_4k = r.y * scale_y
        
        # Calculate heading angle
        angle = math.atan2(r.vy, r.vx)
        
        py5.push_matrix()
        py5.translate(rx_4k, ry_4k)
        py5.rotate(angle)
        
        # Glow cyan rocket triangles
        py5.fill(0, 230, 255, 200)
        py5.no_stroke()
        py5.begin_shape(py5.TRIANGLES)
        py5.vertex(14, 0)
        py5.vertex(-10, -7)
        py5.vertex(-10, 7)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

    # 5. Draw Cybernetic Laboratory HUD in 4K
    py5.stroke(0, 230, 255, 90)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.rect(40, 40, py5.width - 80, py5.height - 80)
    
    # Corner alignment targets
    for cx, cy in [(40, 40), (py5.width - 40, 40), (40, py5.height - 40), (py5.width - 40, py5.height - 40)]:
        py5.stroke(0, 230, 255, 180)
        py5.stroke_weight(3)
        py5.line(cx - 20, cy, cx + 20, cy)
        py5.line(cx, cy - 20, cx, cy + 20)

    # Telemetry data text block (left side)
    py5.fill(0, 230, 255, 220)
    py5.text_size(24)
    py5.text("SYSTEM: BIO-CYBERNETIC GENETIC PATHFINDING", 80, 100)
    
    py5.text_size(18)
    py5.fill(255, 200)
    py5.text(f"POPULATION SIZE   : {len(population.rockets)} AGENTS", 80, 145)
    py5.text(f"ACTIVE GENERATION : GEN {population.generation:03d}", 80, 175)
    py5.text(f"MUTATION PROB     : {MUTATION_RATE*100:.2f}% (STOCHASTIC)", 80, 205)
    py5.text(f"PREV SUCCESS RATE : {population.prev_success_rate:.1f}% SUCCESS", 80, 235)

    # DNA Gene Map Ribbon (visualising best chromosome of current gen)
    py5.text("BEST CHROMOSOME GENE SEQUENCE :", 80, 290)
    ribbon_x = 80
    ribbon_y = 310
    ribbon_w = 400
    ribbon_h = 24
    py5.no_stroke()
    best_dna = population.best_rocket.dna
    
    # Draw DNA vectors as vertical colored slots
    slot_w = ribbon_w / LIFE_SPAN
    for idx, (gx, gy) in enumerate(best_dna.genes):
        g_angle = math.atan2(gy, gx)
        # Hue mapped to steering angle
        ghue = int((g_angle + math.pi) / math.tau * 360)
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        # Highlight current active step in the ribbon
        alpha = 100 if idx != life_step else 25
        py5.fill(ghue, 85, 95, alpha)
        py5.rect(ribbon_x + idx * slot_w, ribbon_y, slot_w + 1, ribbon_h)
        
    py5.color_mode(py5.RGB, 255)
    py5.stroke(0, 230, 255, 120)
    py5.stroke_weight(1)
    py5.no_fill()
    py5.rect(ribbon_x, ribbon_y, ribbon_w, ribbon_h)

    # Fitness Distribution Bar Chart
    py5.fill(255, 200)
    py5.text_size(18)
    py5.text("POPULATION FITNESS PROFILE :", 80, 380)
    chart_y = 405
    # Calculate fitness distribution bins
    fits = np.array([r.fitness for r in population.rockets])
    max_fit = np.max(fits) if np.max(fits) > 0 else 1.0
    normalized_fits = (fits / max_fit) * 100.0
    hist, _ = np.histogram(normalized_fits, bins=10, range=(0, 100))
    
    # Draw histogram bars
    for idx, val in enumerate(hist):
        bar_h = int((val / len(population.rockets)) * 120.0)
        py5.fill(0, 230, 255, 50)
        py5.rect(80 + idx * 42, chart_y + (120 - bar_h), 28, bar_h)
        py5.fill(255, 150)
        py5.text_size(10)
        py5.text(f"{idx*10}%", 84 + idx * 42, chart_y + 140)

    # Progress bar (right side)
    bar_width = 300
    bar_x = py5.width - 80 - bar_width
    bar_y = 90
    py5.no_fill()
    py5.stroke(0, 230, 255, 100)
    py5.stroke_weight(2)
    py5.rect(bar_x, bar_y, bar_width, 16)
    
    py5.fill(0, 230, 255, 180)
    py5.no_stroke()
    py5.rect(bar_x + 2, bar_y + 2, (bar_width - 4) * (fc / TOTAL_FRAMES), 12)
    
    py5.fill(255, 220)
    py5.text_size(18)
    py5.text(f"FRAME RENDER : {fc} / {TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)", bar_x, bar_y - 15)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if blank screen
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Render progress logging
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
