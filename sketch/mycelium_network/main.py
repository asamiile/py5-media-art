from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE
PREVIEW_FRAME = 120

class MyceliumTip:
    def __init__(self, x, y, age=0, depth=0):
        self.x = x
        self.y = y
        self.age = age
        self.depth = depth
        self.vx = py5.random(-1.5, 1.5)
        self.vy = py5.random(-1.5, 1.5)
        self.alive = True

    def update(self, width, height):
        self.x += self.vx
        self.y += self.vy
        self.age += 1

        # Random walk drift
        self.vx += py5.random(-0.2, 0.2)
        self.vy += py5.random(-0.2, 0.2)

        # Limit speed
        speed = (self.vx**2 + self.vy**2)**0.5
        if speed > 2:
            self.vx *= 2/speed
            self.vy *= 2/speed

        # Die if too old or off-canvas
        if self.age > 400 or self.x < -100 or self.x > width+100 or self.y < -100 or self.y > height+100:
            self.alive = False

    def branch(self):
        # Branch probability increases with age (mycelium branches as it matures)
        branch_prob = 0.06 + 0.0002 * self.age
        if py5.random() < branch_prob:
            child = MyceliumTip(self.x, self.y, self.age, self.depth + 1)
            # Child has slightly different direction
            angle = py5.atan2(self.vy, self.vx) + py5.random(-0.6, 0.6)
            child.vx = 1.5 * py5.cos(angle)
            child.vy = 1.5 * py5.sin(angle)
            return child
        return None

def setup():
    py5.size(*SIZE)
    py5.background(25)

    global tips, width, height
    width, height = SIZE

    # Start with 12 seed points densely distributed
    tips = []
    for i in range(4):
        for j in range(3):
            x = width * (0.15 + i * 0.28)
            y = height * (0.2 + j * 0.35)
            tips.append(MyceliumTip(x, y))

    # Add a few random interior points for variety
    for _ in range(3):
        tips.append(MyceliumTip(py5.random(width), py5.random(height)))

def draw():
    global tips

    # Don't clear background - build up trails over time

    new_tips = []

    for tip in tips:
        if tip.alive:
            # Store previous position for line drawing
            prev_x = tip.x - tip.vx
            prev_y = tip.y - tip.vy

            # Update position
            tip.update(width, height)

            # Color based on age: cream (new) → brown (old)
            # Cream: 240, 235, 200
            # Brown: 110, 70, 30
            age_factor = min(1.0, tip.age / 150)
            r = int(240 * (1 - age_factor) + 110 * age_factor)
            g = int(235 * (1 - age_factor) + 70 * age_factor)
            b = int(200 * (1 - age_factor) + 30 * age_factor)

            # Opacity decreases with age
            alpha = int(255 * (1 - age_factor * 0.4))

            # Stroke weight based on depth (deeper = thinner)
            weight = 1.8 - 0.3 * tip.depth

            # Draw with glow effect for young threads
            if age_factor < 0.3:
                glow_alpha = int(100 * (1 - age_factor / 0.3))
                py5.stroke(240, 235, 200, glow_alpha)
                py5.stroke_weight(max(0.3, weight) * 2.5)
                py5.line(prev_x, prev_y, tip.x, tip.y)

            py5.stroke(r, g, b, alpha)
            py5.stroke_weight(max(0.3, weight))
            py5.line(prev_x, prev_y, tip.x, tip.y)

            # Try to branch
            child = tip.branch()
            if child:
                new_tips.append(child)

    # Add new tips and filter dead ones
    tips.extend(new_tips)
    tips = [t for t in tips if t.alive]

    # Exit and save at target frame
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()

py5.run_sketch()
