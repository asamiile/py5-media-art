# kinetic_gyrotactic_bioconvection_plumes_2d

2D incompressible Navier-Stokes simulation coupled with microbial negative buoyancy, active upward gyrotactic swimming advection, and Lagrangian shear-induced bioluminescent tracer kinematics.

## Concept
In natural aquatic habitats, upward-swimming photosynthetic microorganisms (such as *Chlamydomonas* or *Volvox*) orient against gravity towards light. When their local density accumulates, the upper fluid layer becomes unstable, triggering bioconvection: the organisms plunge downward under their collective excess mass in delicate, branching plumes that mushroom into counter-rotating vortex rings and dancing bioluminescent tendrils.

## Techniques
- **Incompressible 2D Navier-Stokes Solver**: Formulated in vorticity ($\omega$) and stream function ($\psi$), utilizing a spectral 2D Poisson solver ($\nabla^2 \psi = -\omega$) in Fourier space to guarantee exact divergence-free flow.
- **Bioconvective Buoyancy Torque Coupling**: Directly couples horizontal microbial density gradients ($\partial C / \partial x$) into fluid vorticity generation, initiating spontaneous Rayleigh-Taylor-like hydrodynamic roll-up instabilities.
- **Semi-Lagrangian Active Advection**: Computes non-oscillatory backtrace advection for microbial concentrations under the combined influence of fluid velocity and active upward gyrotactic swimming ($\mathbf{V}_{\text{swim}}$).
- **Shear-Induced Bioluminescent Micro-Swimmers**: Advects over 750 Lagrangian tracer particles through 4K coordinate space, dynamically exciting their emission intensity and shifting their spectral hue from fluorescent cyan to incandescent solar gold under high local fluid shear stress.

## Palette
- **Abyssal Midnight**: Pitch oceanic void, deep midnight navy
- **Algal Emerald & Jade (60%)**: Bioluminescent deep-sea emerald, malachite green
- **Electric Cyan Tendrils (30%)**: Fluorescent electric cyan, sea-glass aqua
- **Solar Amber Cores & Shear Sparks (10%)**: Incandescent solar gold, warm phototactic amber
