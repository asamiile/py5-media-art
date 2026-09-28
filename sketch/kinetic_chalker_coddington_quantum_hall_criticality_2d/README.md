# kinetic_chalker_coddington_quantum_hall_criticality_2d

2D quantum condensed matter physics simulation depicting multifractal electronic wavefunctions, random magnetic disorder potential landscapes, chiral edge percolation channels, and saddle-point quantum tunneling in the integer quantum Hall plateau transition.

## Concept & Physics

At the integer quantum Hall plateau transition between quantized Hall conductivity plateaus ($\sigma_{xy} = \nu e^2/h$), electronic states at the center of the broadened Landau level become delocalized, undergoing a continuous metal-insulator quantum phase transition.

According to the Chalker-Coddington network model:
1. **Disorder Potential Landscape**: A 2D electron gas (2DEG) is subjected to a perpendicular quantizing magnetic field $B$ and a smooth random electrostatic impurity potential $V(x, y)$.
2. **Chiral Equipotential Channels**: Quasiparticles circulate along equipotential contours of $V(x, y)$ with $\mathbf{E} \times \mathbf{B}$ drift velocity, forming clockwise chiral loops around potential hills ($V > E_F$) and counter-clockwise loops around potential valleys ($V < E_F$).
3. **Critical Percolation & Multifractality**: When the Fermi energy $E_F$ aligns with the Landau level center ($E = 0$), the localized closed loops percolate across the entire sample, exhibiting self-similar multifractal scale invariance with critical exponent $\nu \approx 2.59$.
4. **Saddle-Point Quantum Tunneling (QPCs)**: At saddle points of the disorder potential where $|\nabla V| \approx 0$, chiral edge channels cross, allowing wavefunctions to quantum-tunnel and branch coherently.
5. **Lagrangian Cyclotron Electrons**: 4,000 electrons execute microscopic Larmor cyclotron gyration superimposed upon macroscopic chiral drift and saddle-point tunneling.

## Aesthetics & Color Palette

- **Potential Hills ($V > 0$)**: Luminescent Electric Coral & Solar Gold (`#ff4500` to `#ffaa00`)
- **Potential Valleys ($V < 0$)**: Deep Cryogenic Cobalt Azure & Midnight Obsidian (`#040a18` to `#0d224d`)
- **Critical Percolating Channels**: Phosphorescent Electric Mint & Glacial Cyan (`#00ffa2` to `#00d4ff`)
- **Saddle-Point Tunneling Nodes**: Incandescent Liquid Pearl White (`#ffffff`)
- **Chiral Cyclotron Electrons**: Opal Mint & Golden Sparks

## Specifications

- **Format**: Seamless looping animation (900 frames @ 60 FPS, 15 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized potential landscape & drift kinematics + Blinn-Phong dual-light specular normal mapping
