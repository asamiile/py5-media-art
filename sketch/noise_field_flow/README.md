# Noise Field Flow

A mesmerizing visualization of particles flowing along invisible currents defined by turbulent Perlin noise, demonstrating emergent fluid-like behavior from simple particle dynamics.

## Visual Concept

Thousands of particles suddenly appear and begin flowing in swirling, organic curves. Electric cyan and vibrant magenta particles create flowing ribbons and vortices, guided by invisible Perlin noise velocity fields. The particles weave and spiral, creating patterns that mimic natural fluid dynamics without explicit simulation.

## Technical Details

- **Format**: Animation (12s @ 60fps, 4K/3840×2160)
- **Algorithm**: Perlin noise-based velocity field particle advection
- **Particle Count**: 5000 particles
- **Technique**:
  - Perlin noise velocity field (3D noise sampling for temporal variation)
  - Particle position update based on noise-derived velocity
  - Velocity smoothing (0.8 decay coefficient for inertia)
  - Boundary wrapping for continuous flow
  - Noise-value-based coloring (blue/magenta/cyan gradient)
  - Variable particle size based on local noise magnitude
  - Additive blending for light emission effect

## Color Palette

- **Background**: Deep purple-black (#1a0a2e)
- **Dominant (60%)**: Electric blue (#00ccff) with violet (#8800ff)
- **Secondary (30%)**: Hot pink (#ff00ff) with cyan transitions
- **Accent (10%)**: Gold particle highlights (#ffdd00)
- **Mood**: Vibrant/Neon with fluid elegance

## Conceptual Theme

This work visualizes fluid dynamics through particle behavior guided by noise fields, avoiding explicit physics simulation while achieving organic flow patterns. The approach demonstrates how simple rules (follow noise gradient) can generate complex, fluid-like emergent behavior.

Distinct from previous works by focusing on pure particle advection and flow visualization, creating a bridge between computational and physical phenomena without simulating physics equations directly.
