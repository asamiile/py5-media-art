import py5
import numpy as np
from pathlib import Path

# Configuration
WIDTH, HEIGHT = 1920, 1080
FPS = 60
DURATION = 10  # seconds
TOTAL_FRAMES = DURATION * FPS

class PlasmaAgent:
    def __init__(self, x, y, mass):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.random.uniform(-1, 1, 2)
        self.acc = np.zeros(2)
        self.mass = mass
        self.max_speed = 7.0
        self.history = []
        self.history_limit = 15
        self.hue = py5.random(260, 320) # Violet to Magenta base
        self.flare_timer = 0

    def apply_force(self, force):
        self.acc += force / self.mass

    def update(self):
        self.vel += self.acc
        speed = np.linalg.norm(self.vel)
        if speed > self.max_speed:
            self.vel = (self.vel / speed) * self.max_speed
        self.pos += self.vel
        self.acc *= 0
        
        # History for Bezier loops
        self.history.append(self.pos.copy())
        if len(self.history) > self.history_limit:
            self.history.pop(0)
            
        if self.flare_timer > 0:
            self.flare_timer -= 1

class StellarEquilibrium:
    def __init__(self):
        self.center = np.array([WIDTH/2, HEIGHT/2])
        self.agents = []
        self.num_agents = 1200
        self.sun_mass = 8000.0
        self.G = 0.8
        self.t = 0
        
        for _ in range(self.num_agents):
            angle = py5.random(py5.TWO_PI)
            # More varied distances
            dist = py5.random(150, 500)
            x = WIDTH/2 + py5.cos(angle) * dist
            y = HEIGHT/2 + py5.sin(angle) * dist
            self.agents.append(PlasmaAgent(x, y, py5.random(2, 10)))

        # Starfield
        self.stars = np.random.uniform(0, 1, (1500, 3)) # More stars
        self.stars[:, 0] *= WIDTH
        self.stars[:, 1] *= HEIGHT

    def update(self):
        self.t += 0.015
        # Breathing cycle
        breathing = py5.sin(self.t * 0.4) * 120
        
        for i, agent in enumerate(self.agents):
            to_center = self.center - agent.pos
            dist = np.linalg.norm(to_center)
            dist = max(dist, 50)
            
            # Gravity
            force_mag = (self.G * self.sun_mass * agent.mass) / (dist ** 2)
            gravity = (to_center / dist) * force_mag
            
            # Magnetic tension (restoring force to dynamic shell)
            # Use noise to create "coronal holes" and structure
            n = py5.noise(agent.pos[0]*0.005, agent.pos[1]*0.005, self.t * 0.2)
            target_dist = 250 + breathing + n * 250
            
            # Occasional flare pulse
            if py5.random(1) < 0.0001 and agent.flare_timer <= 0:
                agent.flare_timer = 60
                agent.vel *= 3.0 # Blast outward
            
            diff = dist - target_dist
            tension_k = 0.08 if agent.flare_timer <= 0 else 0.01
            tension = (to_center / dist) * diff * tension_k
            
            # Swirl
            swirl_mag = 2.5 * (1.0 + py5.sin(self.t + dist*0.01))
            swirl = np.array([-to_center[1], to_center[0]]) / dist * swirl_mag
            
            agent.apply_force(gravity)
            agent.apply_force(tension)
            agent.apply_force(swirl)
            agent.update()

    def draw(self):
        # Starfield
        py5.no_stroke()
        for star in self.stars:
            twinkle = py5.noise(star[0], star[1], self.t)
            py5.fill(255, star[2] * 255 * twinkle)
            py5.circle(star[0], star[1], star[2] * 1.5)

        # Sun core - More organic with noise
        py5.push_matrix()
        py5.translate(WIDTH/2, HEIGHT/2)
        
        # Outer glow
        for r in range(180, 80, -5):
            alpha = py5.remap(r, 180, 80, 0, 80)
            py5.fill(45, 90, 100, alpha) 
            # Jitter the radius with noise
            ang = py5.frame_count * 0.01
            rad_noise = py5.noise(py5.cos(ang), py5.sin(ang), r * 0.1) * 20
            py5.circle(0, 0, (r + rad_noise) * 1.6)
            
        # Bright inner core
        for r in range(80, 0, -8):
            alpha = py5.remap(r, 80, 0, 100, 255)
            py5.fill(40, 70, 100, alpha)
            py5.circle(0, 0, r * 1.8)
        py5.pop_matrix()

        # Agents and Magnetic Loops
        for i, agent in enumerate(self.agents):
            dist = np.linalg.norm(agent.pos - self.center)
            
            # Velocity-based color (shift to white/gold when fast/flaring)
            speed = np.linalg.norm(agent.vel)
            sat = py5.remap(speed, 0, 10, 80, 20)
            val = py5.remap(speed, 0, 10, 80, 100)
            
            py5.stroke(agent.hue, sat, val, 180)
            py5.stroke_weight(2.0 if agent.flare_timer > 0 else 1.2)
            py5.point(agent.pos[0], agent.pos[1])
            
            # Prominences - more frequent and visible
            if i % 15 == 0 and len(agent.history) >= 4:
                alpha = 60 if agent.flare_timer > 0 else 30
                py5.stroke(40, 60, 100, alpha) # Golden prominence
                py5.stroke_weight(0.8)
                py5.no_fill()
                h = agent.history
                py5.bezier(h[0][0], h[0][1], h[-1][0], h[-1][1], h[1][0], h[1][1], h[-2][0], h[-2][1])

sketch = StellarEquilibrium()
frames_path = Path(__file__).parent / "frames"

def setup():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.frame_rate(FPS)
    frames_path.mkdir(parents=True, exist_ok=True)

def draw():
    # Persistence for glow
    py5.fill(240, 100, 10, 25) # Deep Indigo with high alpha fade
    py5.rect(0, 0, py5.width, py5.height)
    
    sketch.update()
    sketch.draw()
    
    # Save frames
    if py5.frame_count <= TOTAL_FRAMES:
        py5.save_frame(str(frames_path / f"frame_{py5.frame_count:04d}.png"))
        
        # Mid-point preview
        if py5.frame_count == TOTAL_FRAMES // 2:
            py5.save(str(Path(__file__).parent / "preview_p1.png"))
    else:
        # Export video
        input_pattern = str(frames_path / "frame_%04d.png")
        output_video = str(Path(__file__).parent / "output.mp4")
        
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", input_pattern,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output_video
        ]
        subprocess.run(cmd, check=True)
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
