# kinetic_stable_fluids_turbulence_2d

A 4K kinetic visualization of Jos Stam's Stable Fluids algorithm, solving the 2D incompressible Navier-Stokes equations on a periodic grid to create organic bioluminescent smoke, eddies, and vortices.

## Conceptual Intent
This work explores fluid mechanics as a dynamic canvas. By solving the Navier-Stokes equations in real-time, the piece simulates the beautiful chaotic mixing of colorful bioluminescent dyes under rotating forces, illustrating the fluid tension between structure and dissipation.

## Technical Details
- **Navier-Stokes Solver**: Eulerian grid solver using Semi-Lagrangian advection and Jacobi iteration pressure projection.
- **Color Fields**: Separate color dye channels advected through velocity fields to simulate chemical mixing.
- **Toroidal Topology**: wrapping boundaries allow fluid vortices to travel endlessly across the canvas.
- **4K Upscaling**: Dynamic bilinear expansion from the simulation grid to 3840×2160 pixels.

## Parameters
- **Grid Size**: 240×135
- **Time step (dt)**: 0.8
- **Jacobi Iterations**: 20
