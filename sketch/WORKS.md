# Works Registry

Read this file before creating any new artwork.
Use it to avoid repeating themes, techniques, or algorithms from past works.

## optical_illusion_3d_moire_spheres

- **Date**: 2026-05-25
- **Theme**: Two intersecting spherical cages of high-frequency lines slowly rotating to create mind-bending 3D Moiré interference patterns.
- **Technique**: Two concentric, dense wireframe spheres (longitude/latitude lines). One rotates slightly faster and on a different axis than the other. When rendered with additive blending, the overlapping lines create massive, moving interference bands.
- **Description**: A minimal optical illusion where overlapping geometric lines create the perception of swirling, macroscopic waves that don't actually exist.

## isometric_magnetic_flow_lattice

- **Date**: 2026-05-25
- **Theme**: A massive geometric lattice channeling invisible magnetic streams in isometric projection.
- **Technique**: Isometric 3D particle simulation where particles are constrained to grid axes but swept along a magnetic vector field, leaving geometric, neon laser-like trails.
- **Description**: Thousands of glowing particles forge sharp, right-angled paths through space, building a dense, glowing cybernetic grid in a dark void.

## abstract_cellular_growth_nodes

- **Date**: 2026-05-25
- **Theme**: Organic alien cells linking together and pulsating in a microscopic dark ecosystem.
- **Technique**: 2D N-body physics simulation using springs with distance constraints to simulate cell division and membrane bonding, connected by semi-transparent pulsating webbing.
- **Description**: Bioluminescent cells swarm and link together with glowing cyan webbing in a dark teal environment.

## neon_memory_corruption_rings

- **Date**: 2026-05-25
- **Theme**: Corrupted memory addresses reading as shifting topological rings in a cybernetic dream.
- **Technique**: Parametric 3D rings that distort with high-frequency 1D Perlin noise and chromatic aberration. Rendered in P3D with additive blending and motion blur.
- **Description**: Spinning, glitching rings of neon light breaking apart in a dark void.

## generative_kaleidoscopic_glass_tunnel

- **Date**: 2026-05-24
- **Theme**: Falling infinitely through a shifting, glowing stained-glass tunnel where the geometry recursively folds into itself.
- **Technique**: Uses a rolling buffer of Z-coordinates to create the illusion of an infinitely moving 3D tunnel. The tunnel is constructed using 60 polygonal rings connected by `QUAD_STRIP` meshes. Instead of static shapes, the radius and twist of each ring are continually warped by complex, interfering sine wave functions, giving the tunnel an organic, breathing quality. Additive blending combined with dynamic opacity creates a radiant, translucent glass effect that fades naturally into the dark void.
- **Description**: An infinite, psychedelic flight through an undulating, crystalline glass tunnel.

## kinetic_orbital_resonator_3d

- **Date**: 2026-05-24
- **Theme**: A delicate, hypnotic 3D kinetic sculpture of interlocking golden rings that rotate on multiple axes, connected by shimmering energetic strings.
- **Technique**: Calculates independent 3D rotation matrices for 18 concentric rings in absolute space using NumPy. The rotation speeds are mathematically linked using harmonic ratios (1:2, 2:3, etc.). As the rings orbit on different axes, thousands of translucent "energetic strings" are drawn between corresponding points on adjacent rings with a dynamic oscillating twist. The strings periodically align into perfect geometric patterns before dissolving into chaotic webs, simulating physical resonance and intricate clockwork. Additive blending enhances the glow of the golden mechanical construct.
- **Description**: An elegant 3D mechanical sculpture of interlocking golden rings connected by harmonic, shimmering strings.

## generative_topographic_reaction_diffusion

- **Date**: 2026-05-24
- **Theme**: A high-tech digital contour map of an evolving, living alien landscape.
- **Technique**: Instead of slow iterative simulation, this sketch evaluates a massive, complex mathematical interference pattern in real-time using NumPy vectorization. Five intersecting sine-wave fields, modulated by spatial distortions and rotating phase shifts, produce an incredibly organic scalar field. The script mathematically extracts the isobars (contour lines) of this field, rendering them as thousands of 3D points. The resulting animation looks like a topological map of a breathing, dividing biological organism, viewed through an orbiting camera.
- **Description**: A glowing 3D topological map of a breathing, dividing biological organism.

## generative_topological_torus_knot

- **Date**: 2026-05-24
- **Theme**: A glowing energetic torus knot that constantly twists and folds itself through higher dimensions.
- **Technique**: A parameterized 3D torus knot ($p=3, q=7$) rendered using 20,000 instanced glowing points. An orthonormal basis is calculated across the entire complex mathematical curve to generate a dense, volumetric 3D tube. The points are displaced radially by a high-frequency traveling sine wave. Additive blending combined with a slow background fade leaves majestic, sweeping plasma trails as the camera orbits the knot.
- **Description**: A mesmerizing 3D animated torus knot made of glowing particles that writhes and pulses with mathematical noise.

## abstract_liquid_neon_threads

- **Date**: 2026-05-24
- **Theme**: Fiber optic cables weaving themselves into complex liquid knots and unraveling in a dark void.
- **Technique**: N-body particle simulation with 4 orbiting gravity wells. 15,000 particles are rendered as continuous lines with additive blending. Instead of completely clearing the background, a very faint black rectangle is drawn to create extremely long, sweeping trails. The gravity wells' masses oscillate with sine waves, causing the trails to form intricate, looping Lissajous-like knots that resemble glowing liquid threads.
- **Description**: Thousands of glowing particles form intricate, swirling liquid threads around invisible gravity wells.

## abstract_cybernetic_glitch_core

- **Date**: 2026-05-24
- **Theme**: Data corruption in an old quantum computer, mixing sharp geometric structures with fluid, melting glitch effects.
- **Technique**: A 3D wireframe mesh that periodically displaces its vertices using high-frequency 3D Perlin noise and chromatic aberration separation on the X/Y axes when a "glitch" threshold is hit. It avoids extreme additive blending build-up by clearing the background with a low-opacity black each frame to create a controlled blur without blowing out to white.
- **Description**: A dynamic 3D cybernetic mesh glitches and distorts with chromatic aberration, creating a dark, moody energetic field.

## geometric_fractal_recursive_tree_3d

- **Date**: 2026-05-23
- **Theme**: L-systems, fractal trees, botany, recursive growth, sacred geometry, nature.
- **Technique**: Uses a recursive function (`draw_branch`) to generate thousands of connected 3D lines. At each depth, the tree branches into 2 or 3 smaller branches, spiraling outward in 3D space. The angle of each branch is dynamically modulated by a 2D Perlin noise field simulating wind, causing the entire massive structure to gently sway. The length of the branches scales rhythmically with a sine wave to simulate breathing or organic growth. Rendered in `py5.P3D` as the camera slowly orbits the glowing, neon-colored tree. 15s 60fps MP4.
- **Description**: A digital Yggdrasil. A massive, glowing neon tree grows upward from the void, branching out endlessly into thousands of delicate, mathematical twigs. The camera slowly orbits the three-dimensional fractal structure while a gentle, invisible wind rustles the glowing branches. The colors organically shift from deep roots of purple to electric cyan leaves, creating a mesmerizing fusion of nature and computation.

## geometric_isometric_voxel_sorting

- **Date**: 2026-05-23
- **Theme**: Pixel sorting, algorithms, voxels, entropy to order, 3D data visualization, isometric projection.
- **Technique**: Starts with a $15 \times 15 \times 15$ grid (3,375 voxels) of completely randomized colors (Hue, Saturation, Brightness). Every frame, the script runs partial passes of a Bubble Sort algorithm along the X, Y, and Z axes. The X-axis sorts by Hue, the Y-axis sorts by Saturation, and the Z-axis sorts by Brightness. As the algorithm progresses over 15 seconds, the chaotic block of noise magically self-organizes into a perfect, smooth 3D RGB color gradient cube. The voxels also "breathe" (scale up and down) based on their hue, meaning as the cube sorts itself, the random glitchy scaling organizes into a smooth geometric wave. Rendered in `py5.P3D` with an isometric camera angle. 15s 60fps MP4.
- **Description**: Entropy reversing into perfect order. A massive, rotating cubic structure is made of thousands of tiny, randomly colored floating blocks. Over time, the blocks begin to shift and swap places autonomously. Slowly, a pattern emerges from the chaos. The random noise reorganizes itself until it forms a flawless, glowing 3D rainbow gradient cube, undulating smoothly as its internal colors harmonize.

## abstract_generative_strange_attractor_lorenz

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, the butterfly effect, fluid convection, math.
- **Technique**: Solves the Lorenz system of nonlinear ordinary differential equations ($\frac{dx}{dt} = \sigma(y - x)$, $\frac{dy}{dt} = x(\rho - z) - y$, $\frac{dz}{dt} = xy - \beta z$) for 15,000 independent particles simultaneously. The entire swarm is initialized in a microscopic cluster of a $0.01$ radius. Due to the chaotic nature of the strange attractor (the "Butterfly Effect"), infinitesimally small initial differences cause the particles' paths to rapidly diverge. The physics are computed using vectorized NumPy operations for high performance. The particles are drawn as a continuous, fading neon ribbon (`py5.line` with additive blending and motion blur) that reveals the iconic dual-lobe "butterfly" shape of the attractor over time. 15s 60fps MP4.
- **Description**: The Butterfly Effect made visible. 15,000 points of light begin as a single microscopic drop, but within seconds, the laws of chaos rip them apart. They spiral outward, tracing the invisible mathematical currents of the Lorenz Strange Attractor. The paths weave a massive, glowing, two-lobed structure that looks like cosmic gossamer wings. The camera slowly orbits the 3D structure, showing the intricate, non-intersecting layers of infinite complexity drawn in deep purples and electric pinks.

## geometric_fractal_kaleidoscope_mirrors

- **Date**: 2026-05-23
- **Theme**: Kaleidoscopes, reflection, fractals, sacred geometry, mirrors, symmetry, optical illusions.
- **Technique**: Uses matrix transformations (`py5.push_matrix()`, `py5.rotate()`) combined with matrix scaling (`py5.scale(1, -1)`) to perfectly mirror a single wedge of geometry 12 times in a circle. Inside the base wedge (slice), the script generates chaotic, overlapping Bezier curves and jagged polygons driven by time and Perlin noise. When this single slice is mirrored and repeated, the chaotic lines seamlessly connect across the boundaries of the slices, creating massive, perfectly symmetrical geometric mandalas. Additive blending (`py5.ADD`) and a slight motion blur trail make the shifting shapes glow like stained glass or a laser light show. 15s 60fps MP4.
- **Description**: A digital kaleidoscope turns endlessly, reflecting beams of neon light into a perfect 12-pointed star. As the internal "mirrors" shift, chaotic ribbons of cyan and magenta fold into intricate, symmetrical mandalas, expanding and collapsing like a breathing cosmic flower. The shapes flow seamlessly across the reflection boundaries, creating the hypnotic illusion of an infinitely repeating fractal universe.

## abstract_generative_boids_flocking_3d

- **Date**: 2026-05-23
- **Theme**: Artificial life, emergent behavior, flocking, Boids, swarm intelligence.
- **Technique**: Simulates 1,200 individual "boids" flying inside a massive 3D boundary box. To achieve real-time 60fps performance without using C++ or shaders, the heavy $O(N^2)$ distance matrix and N-body interaction logic (Separation, Alignment, Cohesion) are heavily optimized using NumPy broadcasting and vectorization. Each boid mathematically calculates the velocity and position of its neighbors to steer its flight path dynamically. The boids are rendered using `py5.begin_shape(py5.TRIANGLES)` as custom 3D pyramids that pitch and yaw perfectly along their velocity vectors using `atan2` rotations. Dynamic lighting (`py5.directional_light`) casts dramatic shadows as the swarm moves. 15s 60fps MP4.
- **Description**: A breathtaking digital murmuration. Over a thousand glowing, geometric birds swarm inside an invisible cubic boundary. They organically clump together into massive, swirling flocks, only to break apart and weave through each other to avoid collisions. The artificial creatures constantly shift their neon colors based on their spatial coordinates, creating a chaotic yet perfectly synchronized dance of swarm intelligence that feels deeply alive.

## abstract_generative_cellular_automata_1d

- **Date**: 2026-05-23
- **Theme**: Cellular automata, Rule 30, chaos theory, weaving, digital tapestry, isometric projection.
- **Technique**: Implements a 1D elementary cellular automaton using Rule 30, famous for generating complex, pseudo-random, chaotic patterns from a single starting pixel. Instead of rendering it as a static 2D image, the automaton is rendered as a scrolling $100 \times 100$ grid of 3D cubes (`py5.box`) using an isometric camera projection. Every 3 frames, a new row is calculated at the top and the entire history shifts downward, creating a cascading waterfall effect. The "active" (`1`) states are rendered as tall, emissive gold pillars, while the "inactive" (`0`) states are short, dark obsidian blocks. A secondary sine wave ripple distorts the Z-axis of the entire tapestry. 15s 60fps MP4.
- **Description**: A breathtaking digital tapestry weaves itself in real-time. Rendered in a deep, moody isometric 3D view, a chaotic but highly structured pattern cascades downward like a waterfall. The pattern is built from thousands of individual geometric blocks—glowing, metallic gold pillars representing "alive" cells, and dark obsidian blocks representing "dead" cells. The chaotic geometry of Rule 30 creates striking triangle patterns that slide gracefully across the screen as the entire woven structure slowly rotates in three-dimensional space.

## geometric_generative_phyllotaxis_spiral

- **Date**: 2026-05-23
- **Theme**: Phyllotaxis, golden ratio, sunflowers, botany, sacred geometry, Moiré patterns.
- **Technique**: Uses Vogel's mathematical model for phyllotaxis ($r = c \sqrt{n}$, $\theta = n \times 137.5^\circ$) to arrange 4,000 glowing geometric "seeds" into a perfect spiral. The script slightly animates the divergence angle $\theta$ around the exact Golden Angle using a sine wave. Even a deviation of $0.1^\circ$ completely breaks and reforms the visible spiral arms (parastichies), creating hypnotic, kaleidoscopic Moiré patterns. The 2D mathematical pattern is mapped onto a 3D dome, tilting and rotating smoothly in 3D space (`py5.P3D`) with additive blending. 15s 60fps MP4.
- **Description**: Thousands of glowing neon petals arrange themselves into a perfect, massive sunflower-like spiral. As the central mathematical angle imperceptibly shifts, the spiral arms undergo a breathtaking optical illusion—collapsing into straight spokes, twisting into countless tiny whirlpools, and snapping back into perfect golden-ratio spirals. The entire 3D botanical structure breathes and rotates, shifting colors from hot pink and orange in the center to deep ultraviolet at the edges.

## abstract_vector_field_magnetic_dipole

- **Date**: 2026-05-23
- **Theme**: Magnetism, physics, vector fields, iron filings, electromagnetism, flux lines.
- **Technique**: Employs a fully NumPy-vectorized physics engine to update 30,000 particles at 60fps. The vector field is mathematically defined by four magnetic "poles" (positive and negative charges) that orbit each other in Lissajous curves. The force acting on each particle is calculated using Coulomb's/magnetic inverse-square law ($F \propto 1/r^2$). To simulate the visual look of iron filings aligning to a magnetic field, particles are drawn as short, additive-blended line segments (`py5.line` from old position to new position) over a motion-blur background. The color of the particles shifts from deep blue to bright cyan/white depending on their kinetic velocity. 15s 60fps MP4.
- **Description**: Like iron filings scattered over invisible magnets, tens of thousands of glowing particles align themselves into intricate, looping magnetic flux lines. The invisible poles dance and spin around each other, causing the magnetic field to warp and tear. The particles are continuously swept up in these invisible currents, creating breathtaking loops and figure-eights of glowing plasma that accelerate violently when trapped between opposing charges.

## abstract_liquid_displacement_map

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, water, optical refraction, caustics, bioluminescence, ocean currents.
- **Technique**: A dense 2D grid ($120 \times 80$) is mapped to a scrolling 3D Perlin noise field. Instead of using the noise to determine color or height directly, the script calculates the numerical derivative (gradient) of the noise field at each point. The $X$ and $Y$ coordinates of each grid point are then physically displaced by this gradient vector multiplied by a massive scalar ($8000$). This mathematically simulates optical refraction, where light rays bend based on the slope of a water wave. Additive blending (`py5.ADD`) naturally creates bright "caustic" bands where the displaced points bunch together. The entire field flows downwards over time, simulating a deep ocean current. 15s 60fps MP4.
- **Description**: Looking down into the depths of a bioluminescent ocean. Shimmering, fluid lines of light—known as caustics—dance and warp across the dark blue void. The light rays are bent and refracted by unseen, rolling waves, causing the grid to tear, overlap, and bunch together into intensely bright, neon-cyan ridges. The fluid motion is mesmerizing, flowing continuously downward like a digital waterfall of pure light.

## geometric_sacred_flower_of_life

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, Flower of Life, mandalas, blooming, interconnectedness, enlightenment.
- **Technique**: Uses a mathematical hexagonal lattice generator (Axial coordinates $q$ and $r$) to precisely calculate the intersecting center points for 91 overlapping circles. Instead of drawing it flat, the script adds a Z-axis depth ripple driven by a sine wave (`py5.translate(x, y, py5.sin(phase) * 50)`). Additive blending (`py5.ADD`) is used to make the overlapping geometric intersections glow with intense neon light. The radius of the circles and the overall structure breathe and pulsate in an outward-radiating wave pattern, simulating the "blooming" of a cosmic flower. 15s 60fps MP4.
- **Description**: The ancient "Flower of Life" symbol comes alive as a glowing, three-dimensional digital mandala. Perfectly overlapping neon circles ripple and breathe outward from the center, creating hypnotic, shifting petal patterns where their geometries intersect. The overlapping rings glow white-hot at their junctions, shifting continuously through a brilliant spectrum of cyan, magenta, and gold as the entire cosmic lattice slowly rotates in the dark void.

## abstract_reaction_diffusion_slime

- **Date**: 2026-05-23
- **Theme**: Biology, cellular division, slime mold, Reaction-Diffusion, organic patterns, Turing patterns.
- **Technique**: Solves the Gray-Scott Reaction-Diffusion differential equations natively in Python. To achieve 60fps performance without shaders, the simulation runs at half-resolution ($960 \times 540$) using highly optimized 2D NumPy array slicing for the discrete Laplacian convolution operator. The simulation is advanced 8 steps per drawn frame. The resulting chemical concentration fields are then upscaled via `numpy.repeat` and mapped to a custom color gradient, which is blasted directly to the screen buffer via `py5.np_pixels`. 15s 60fps MP4.
- **Description**: A macroscopic view of an alien cellular organism dividing and multiplying in a petri dish. Starting from a few microscopic seeds, neon cyan and green chemical trails rapidly spread outward across a dark violet void. The organic patterns undergo continuous mitosis, splitting into maze-like ridges, coral-like branches, and leopard spots as the two simulated chemicals continuously react and diffuse into one another.

## geometric_3d_voxel_terrain_flight

- **Date**: 2026-05-23
- **Theme**: Voxel engines, flight simulation, procedural terrain, retro 3D, topographic mapping.
- **Technique**: Uses a 2D Perlin noise map to generate a continuously scrolling 3D terrain grid. Rather than rendering the terrain as a smooth mesh, it is rendered discretely using 1,800 individual 3D cubes (`py5.box`), creating a retro voxel aesthetic similar to Minecraft or early 3D renders. The `y`-axis of the Perlin noise input is continuously decremented, creating the illusion of endless forward flight. A dynamic `py5.camera()` controls the viewport, banking left, right, up, and down as it flies through the valleys. The cubes are colored topographically based on their height, with the highest peaks assigned `py5.emissive()` materials so they glow like volcanic lava or neon snow in the dark atmosphere. 15s 60fps MP4.
- **Description**: The camera hurtles forward through a digital canyon made entirely of floating geometric cubes. Below, a jagged, blocky terrain of deep purple valleys and towering magenta peaks scrolls by endlessly. The camera smoothly banks and bobs as if mounted to a flying drone. As the drone passes over the tallest mountain ranges, the tips of the voxel towers glow with a blinding, emissive heat, illuminating the atmospheric fog of the digital world.

## abstract_particle_spring_physics_mesh

- **Date**: 2026-05-23
- **Theme**: Soft-body physics, Hooke's Law, digital fabric, spring constraints, interactive topology, tearing force.
- **Technique**: A 60x40 2D grid of particles is simulated using basic Euler integration and Hooke's Law. Each particle is connected to its rest position via a mathematical spring ($F = -kx$). Three invisible circular colliders move in complex Lissajous patterns across the screen, colliding with the grid particles and forcefully pushing them away. When the colliders pass, the springs rapidly snap the particles back into place with elastic damping. The connections between particles are drawn as lines using additive blending (`py5.ADD`). The color, brightness, and opacity of each line segment are directly mapped to its "stretch factor"—lines glow white-hot when under extreme tension. 15s 60fps MP4.
- **Description**: A dense, dark wireframe mesh resembling digital fabric spans the entire screen. Suddenly, invisible spheres crash into the fabric from behind, stretching the grid violently. The areas of the mesh under extreme physical tension glow brightly in blinding cyan and magenta, visualizing the kinetic energy of the impact. As the invisible forces move away, the fabric snaps back, rippling with residual elastic waves until it settles back into its perfect, dormant grid.

## geometric_fractal_recursive_tree_3d

- **Date**: 2026-05-23
- **Theme**: Fractals, recursive trees, L-systems, algorithmic botany, nature, wind simulation.
- **Technique**: Uses a pure recursive function (`draw_branch`) to draw a highly complex 3D tree. The function draws a line (the branch trunk), translates to its tip, and then calls itself 3 times. Each child branch is rotated evenly around the Y-axis (creating a volumetric canopy) and tilted outwards. The recursion depth is 9, resulting in $3^9$ (nearly 20,000) individual branch segments. Global time `t` continuously modulates the branching angles and applies Perlin noise-based wind sway. The hue shifts dynamically based on recursion depth. 15s 60fps MP4.
- **Description**: A magical, glowing digital tree grows upward from the bottom of the screen into a dense, sprawling canopy. The tree is composed of thousands of glowing neon lines that shift from deep indigo at the thick trunk to vibrant cyan and green at the delicate outer branches. The entire tree is constantly in motion—not only rotating slowly in 3D space, but each branch gracefully swaying and curling inward and outward as if caught in an ethereal, shifting wind.

## abstract_topological_moebius_strip

- **Date**: 2026-05-23
- **Theme**: Topology, non-orientable surfaces, Möbius strip, sacred geometry, infinite loops, energy streams.
- **Technique**: Evaluates the parametric mathematical equations for a Möbius strip over a dense $u,v$ coordinate grid. Rather than rendering a solid surface, the script draws only discrete longitude lines (`LINE_STRIP`) along the $V$ axis, creating the appearance of a hollow, glowing wireframe track or energy ribbon. The twist factor of the Möbius strip is animated over time using a sine wave, causing the non-orientable geometry to mathematically warp and "break" its topology as it spins. High-frequency 3D Perlin noise and additive blending give the lines a crackling, energetic plasma texture. 15s 60fps MP4.
- **Description**: A massive, glowing ribbon of neon light twists endlessly through a dark void. The ribbon is a perfect Möbius strip—a paradoxical geometric shape with only one side and one edge. As it rotates, the mathematical parameters of the strip smoothly mutate, causing the track to widen, narrow, and aggressively twist upon itself. The glowing cyan, magenta, and gold lines crackle with digital energy, creating an infinite, hypnotic loop that defies spatial logic.

## generative_vector_field_perlin_flow

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, vector fields, Perlin noise, wind currents, Van Gogh's Starry Night, organic flow.
- **Technique**: Uses NumPy arrays to manage the positions and velocities of 30,000 individual particles. In every frame, a 3D Perlin noise function evaluates the precise angle of a "wind current" at each particle's exact (x, y) location. The third dimension of the noise function is bound to time, causing the entire invisible vector field to slowly mutate and boil. The background is not completely cleared between frames; instead, a highly transparent black rectangle is drawn over the canvas, causing the moving particles to leave long, fading trails (`py5.background` motion blur effect). The particles are colored based on their current angle of travel. 15s 60fps MP4.
- **Description**: Like a digital painting of a cosmic wind storm. 30,000 glowing neon dust particles flow across the screen, caught in an invisible, churning atmospheric current. They weave into intricate, interlocking spirals, whirlpools, and flowing rivers of light that resemble the swirling skies of Van Gogh's *Starry Night* or the intricate rings of polished wood grain. As the underlying wind field slowly shifts, the entire glowing tapestry continuously repaints itself in waves of shifting cyan, magenta, and gold.

## generative_liquid_metaballs_threshold

- **Date**: 2026-05-23
- **Theme**: Metaballs, surface tension, fluid dynamics, liquid metal, organic blobs.
- **Technique**: Demonstrates an optimized way to render 2D Metaballs without expensive per-pixel distance field calculations. First, 60 invisible points bouncing around the screen are rendered as soft, grayscale radial gradients using `py5.blend_mode(py5.ADD)`. This creates a smooth, continuous scalar density field. Then, `py5.load_np_pixels()` intercepts the raw frame buffer. NumPy array masking is applied to threshold the image instantly: pixels above a certain brightness become a solid neon cyan (the liquid core), while pixels sitting exactly on the brightness threshold become neon magenta (surface tension / outlines). The result is perfectly smooth, gloopy liquid blobs that merge and separate dynamically. 15s 60fps MP4.
- **Description**: Drops of glowing neon cyan liquid float across a pitch-black canvas. As the droplets collide, they do not overlap like solid objects; instead, their surface tension snaps them together, seamlessly merging into massive, undulating blobs of liquid light. Each globule is outlined by a razor-sharp, glowing magenta edge that continuously recalculates its shape as the fluid stretches and tears apart, creating a hypnotic lava-lamp effect of digital plasma.

## geometric_isometric_cyber_city

- **Date**: 2026-05-23
- **Theme**: Cyberpunk, isometric projection, brutalist architecture, procedural generation, living cities.
- **Technique**: A massive 35x35 grid of 3D boxes is generated using `py5.box()`. The camera is strictly set to an orthographic projection (`py5.ortho()`) and rotated to precise isometric angles ($\arcsin(1/\sqrt{3})$ and $45^\circ$). The height of each "building" is dynamically driven by an exponentiated 3D Perlin noise field moving over time, creating sharp, towering skyscrapers and deep valleys that ripple like a fluid wave. Multi-colored directional lighting casts dramatic shadows, while select buildings are rendered as pure, glowing emissive neon pillars. 15s 60fps MP4.
- **Description**: An endless, futuristic metropolis viewed from a classic video-game isometric perspective. The brutalist concrete skyscrapers stretch and shrink continuously, as if the entire city is a living, breathing organism reacting to a digital earthquake. Saturated neon cyan and magenta lights sweep across the angular architecture, while hyper-tall glowing monolithic towers pierce the skyline like beacons in the geometric night.

## geometric_fractal_polyhedron_subdivision

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, recursive subdivision, platonic solids, geodesic domes, fractal breathing.
- **Technique**: The script begins with a mathematically perfect Icosahedron (a 20-sided Platonic solid derived from the Golden Ratio). Before drawing, it performs 4 levels of recursive subdivision on the CPU, splitting each triangular face into 4 smaller triangles and projecting the new vertices back onto a unit sphere, creating a dense geodesic mesh (thousands of triangles). During the draw loop, the position of every single vertex is displaced outward or inward based on a 3D volumetric sine wave interference pattern. This displacement causes the rigid geometry to "breathe" and warp dynamically. The faces are rendered semi-transparent with glowing edges (`py5.TRIANGLES`). 15s 60fps MP4.
- **Description**: A gigantic, glowing geodesic crystal floats and rotates slowly in a void. What starts as a perfect sphere made of thousands of tiny triangular glass panels suddenly begins to warp and breathe. Three-dimensional ripples travel across its surface, pulling the sharp vertices outward into spiked fractal crowns and pushing them inward to form deep craters. The facets gleam in shifting colors of cyan, magenta, and gold as the simulated light hits the continuously rippling, breathing digital crystal.

## abstract_quantum_wavefunction_collapse

- **Date**: 2026-05-23
- **Theme**: Quantum mechanics, wave function, superposition, probability density, spherical harmonics, electron orbitals.
- **Technique**: Uses NumPy vectorization to simulate a 3D probability cloud of 60,000 particles. Instead of standard noise, the particle positions are displaced and filtered using equations derived from "Spherical Harmonics"—the mathematical standing waves that dictate the shapes of electron orbitals (s, p, d, f) in atoms. The sketch smoothly interpolates between two distinct orbital states (quantum superposition), causing the particle cloud to morph and separate into distinct geometric lobes and nodes (empty voids where probability is zero). Rendered using `py5.POINTS` with additive blending and dynamic phase coloring. 15s 60fps MP4.
- **Description**: A mesmerizing visualization of the quantum realm. 60,000 glowing subatomic particles float in a deep void, not as solid objects, but as a probability cloud. The cloud organically shifts, stretching and pinching into the distinct, bulbous shapes of atomic orbitals. As the wave function evolves in a state of superposition, the neon cyan and azure lobes of the electron cloud dissolve and recombine, perfectly illustrating the hidden standing waves that form the foundation of matter.

## abstract_cellular_automata_1d

- **Date**: 2026-05-23
- **Theme**: Cellular Automata, Rule 30, Stephen Wolfram, computational irreducibility, digital fabric, weaving.
- **Technique**: First, a 1D Cellular Automaton (Rule 30) is calculated for 150 generations across a grid of 120 cells using a classic bitwise evaluation loop. Instead of rendering this as a flat 2D pixel grid, the space-time history (where Y is time and X is the cell index) is mapped onto the surface of a 3D cylinder using polar coordinates (`py5.QUADS`). To make it kinetic, a time-based 3D Perlin noise field deforms the radius of the cylinder continuously. The result is a mathematically complex, non-repeating triangular fractal pattern that appears to be woven into a piece of digital fabric flapping in a simulated wind. 15s 60fps MP4.
- **Description**: A massive, woven tube of glowing fabric floats in the dark. The fabric is patterned with the iconic, chaotic triangles of Cellular Automaton Rule 30—the same mathematical pattern found on the shells of Conus textile snails. As the tube slowly rotates, an invisible wind causes the digital cloth to ripple and warp. The "living" cells (1s) glow in shifting neon hues, while the "dead" cells (0s) form a dark, semi-transparent mesh, blending rigid computer science with organic, flowing textiles.

## generative_phyllotaxis_sunflower

- **Date**: 2026-05-23
- **Theme**: Phyllotaxis, golden ratio, Fibonacci sequence, sunflower seeds, organic growth, sacred geometry.
- **Technique**: Positions 3,000 "seeds" using the classic mathematical model of plant growth: $r = c \sqrt{n}$ and $\theta = n \times 137.5^\circ$ (the Golden Angle). To make the simulation kinetic and mesmerizing, the exact angle is continuously modulated by a tiny sine wave offset. This extremely small perturbation breaks the perfect Fibonacci spirals, causing the intersecting visual arcs to warp, twist, and weave into entirely new geometric interference patterns before snapping back to the perfect sunflower formation. The entire structure is rendered as a subtly breathing 3D dome, with each seed rotating and glowing dynamically. 15s 60fps MP4.
- **Description**: A perfect, glowing sunflower made of 3,000 neon diamond petals spins slowly in a dark void. As the underlying mathematical angle shifts by fractions of a degree, the perfect spiral arms of the flower begin to twist and cross over one another. The visual structure ripples and breathes, dissolving into complex diamond grids and multi-armed vortexes before seamlessly reforming its hypnotic, natural Fibonacci perfection. The colors radiate from the center, creating a mesmerizing display of organic geometry.

## optical_illusion_moire_patterns

- **Date**: 2026-05-23
- **Theme**: Op-art, optical illusions, Moiré patterns, kinetic art, wave interference, visual perception.
- **Technique**: Renders three extremely dense layers of concentric circles and one layer of dense linear grating. By assigning contrasting semi-transparent colors (cyan, magenta, yellow, white) to each layer and slowly translating, rotating, and scaling them relative to one another, the sketch generates intense mathematical interference patterns (Moiré effects). The human eye perceives these overlapping high-frequency lines as moving, low-frequency macroscopic shapes (ghostly spirals, pulsing waves, and flickering stars). Rendered purely in 2D with `py5.circle` and `py5.line`. 15s 60fps MP4.
- **Description**: A mind-bending optical illusion. Dense geometric grids of cyan, magenta, and yellow overlap against a dark background. As the layers slowly drift and rotate out of alignment, impossible new shapes—pulsating stars, shimmering ripples, and swirling vortexes—suddenly appear and dissolve within the negative space. The interference patterns create a dizzying, hypnotic visual effect that seems to vibrate and move in ways that the actual drawn lines do not, challenging the limits of human perception.

## abstract_strange_attractor_particle_flow

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, Lorenz system, butterfly effect, fluid dynamics, particle swarm.
- **Technique**: Leverages NumPy array vectorization to compute the differential equations for the classic Lorenz attractor ($dx, dy, dz$) on 50,000 independent particles simultaneously at 60fps. The particles are initialized in a tiny cluster and are quickly ripped apart by the chaotic vector field, splitting into two distinct orbiting lobes (the "butterfly wings"). A subtle oscillating noise field is added to the equations, giving the mathematically rigid attractor a more organic, fluid-like wind distortion. The scene is rendered using `py5.POINTS` with additive blending and motion blur. Particle colors dynamically map from cyan to magenta based on their instantaneous velocity. 15s 60fps MP4.
- **Description**: 50,000 glowing particles are caught in an invisible, chaotic gravitational storm. Starting as a dense singularity, the swarm is violently stretched and torn into two swirling, interconnected rings resembling the wings of a butterfly. The glowing dust races along the complex mathematical curves of the Lorenz attractor, leaving brilliant trails of cyan and magenta light that continuously fold in on themselves. As the camera slowly rotates, the infinite, non-repeating complexity of chaos theory is revealed as a beautiful, breathing cosmic nebula.

## generative_neural_network_graph

- **Date**: 2026-05-23
- **Theme**: Artificial intelligence, neural networks, deep learning, data flow, synaptic connections, cybernetics.
- **Technique**: A massive 3D graph is constructed representing the layers of a deep neural network. The nodes (neurons) are arranged in 8 concentric circular layers forming a large cylinder. The edges (synapses) connect nodes between adjacent layers. To avoid visual clutter and maintain performance, connections are only drawn between "nearest neighbor" angles. A global "activation pulse" travels continuously down the layers from input to output, causing the nodes and edges to flare with intense brightness as the data passes through. Individual synaptic activity is modulated by 3D Perlin noise, ensuring the network feels organically "thinking" rather than rigidly mechanical. Rendered with additive blending. 15s 60fps MP4.
- **Description**: A gigantic, glowing cybernetic brain floats in a dark void. It is composed of thousands of nodes connected by a dense web of glowing synapses. As the camera slowly orbits the structure, bright pulses of data surge through the network, illuminating the layers one by one in a cascading wave of cyan and magenta light. The connections flicker and reroute dynamically, mimicking the complex, unfathomable computations of an artificial intelligence processing a massive stream of information.

## geometric_flower_of_venus

- **Date**: 2026-05-23
- **Theme**: Orbital mechanics, celestial geometry, resonance, spirograph, cosmic mandala.
- **Technique**: Simulates the orbital paths of three mathematical "planets" moving around a central star. By connecting the planets with semi-transparent, additive-blended lines (`py5.line`) at regular time intervals, their orbital resonance ratios naturally construct intricate, spirograph-like mandalas (just as tracing the distance between Earth and Venus over 8 years creates a perfect 5-petaled flower). Unlike rigid astronomy, the orbital radii and resonance ratios (`ratio1`, `ratio2`) slowly morph over time using sine waves. This causes the drawn geometry to seamlessly transition between different symmetrical flowers and complex, chaotic webs. 15s 60fps MP4.
- **Description**: In the dark void of space, three glowing points orbit at different speeds. As they move, brilliant laser-like lines connect them, leaving a glowing trail in their wake. Because their orbits are mathematically resonant, these straight lines intersect perfectly to weave a stunning, glowing mandala—the "Flower of Venus". As the orbital parameters slowly shift, the intricate geometric flower dissolves and rapidly reweaves itself into an entirely new, deeply mesmerizing 12-petaled cosmic pattern.

## hyperbolic_tessellation_poincare

- **Date**: 2026-05-23
- **Theme**: Hyperbolic geometry, Poincaré disk, non-Euclidean math, M.C. Escher, fractal tessellation, Möbius transformation.
- **Technique**: Demonstrates complex mathematical mapping in 2D space. A recursive hexagonal fractal is generated in the complex plane, strictly bounded within the "unit disk" ($|z| < 1$). Before rendering, every vertex of the fractal is mathematically transformed using a time-varying Möbius transformation: $f(z) = (z - a) / (1 - a^* z)$. The complex parameter $a$ orbits inside the disk over time. This creates an impossible optical illusion where the center of the fractal seems to flow out toward the edges, infinitely shrinking as it approaches the boundary circle, mimicking the exact hyperbolic spatial distortion seen in M.C. Escher's "Circle Limit" works. 15s 60fps MP4.
- **Description**: Inside a glowing white circle on a dark canvas, a mesmerizing mosaic of neon hexagons forms a dense fractal. As invisible forces warp space, the geometric pattern continuously flows outward like a fountain. Shapes that reach the edge of the circle do not disappear; instead, they stretch, flatten, and shrink to infinity, creating an infinite hyperbolic boundary. The colors cycle smoothly through neon gradients, emphasizing the dizzying, impossible depth of this non-Euclidean universe.

## abstract_fluid_marbling

- **Date**: 2026-05-23
- **Theme**: Fluid marbling, suminagashi, marble paper, organic flow, vector field advection.
- **Technique**: Instead of simulating a raster pixel grid, this sketch renders 120 horizontal vector lines, each containing 400 vertices. To simulate the swirling, organic eddies of ink dropped onto water, every vertex is displaced (`dx`, `dy`) by a combination of overlapping 3D Perlin noise fields. By carefully tuning the frequency and amplitude of the noise functions, the lines are pulled and folded into elegant, continuous swirls that perfectly mimic fluid advection without the extreme computational overhead of a true Navier-Stokes solver. Rendered in P2D with a smooth ocean-blue to deep-purple gradient. 15s 60fps MP4.
- **Description**: Dense, horizontal lines of cyan and purple ink are suspended in a dark void. Slowly, invisible currents begin to stir the fluid. The perfectly straight lines are drawn into complex, curling eddies, folding over themselves like marble patterns on expensive paper. The fluid motion is incredibly smooth and organic, continuously twisting into new, mesmerizing fractal swirls before gently drifting off-screen.

## geometric_origami_tessellation

- **Date**: 2026-05-23
- **Theme**: Origami, paper folding, Miura fold, geometric tessellation, mathematical surfaces.
- **Technique**: Uses a dense 2D grid (`py5.QUAD_STRIP`) to simulate a massive sheet of paper. A base "fold angle" ($\theta$) oscillates via a sine wave, causing the entire paper to contract on the X-axis while simultaneously expanding on the Z-axis in an alternating, checkerboard pattern. This creates the classic "accordion" structure of rigid origami. To make it visually organic, the fold angle is modulated locally by 3D Perlin noise, causing the rigid geometric folds to ripple, warp, and crumple slightly like real, stiff iridescent paper. 15s 60fps MP4.
- **Description**: A vast, flat plane of iridescent material slowly begins to fold itself. Guided by invisible mathematical laws, the surface collapses inward, forming a highly complex, repeating geometric pattern of sharp ridges and deep valleys (a Miura-ori tessellation). Strong directional lights catch the shifting angles of the folds, revealing a spectrum of glowing cyan and magenta hues. As the structure slowly spins, the paper breathes—unfolding back into a nearly flat plane before deeply crumpling again in a mesmerizing, organic rhythm.

## generative_cymatics_chladni

- **Date**: 2026-05-23
- **Theme**: Cymatics, Chladni figures, standing waves, physics simulation, sound visualization.
- **Technique**: Calculates the squared gradient of the classic Chladni equation (`a * sin(n*pi*x)*sin(m*pi*y) + b * sin(m*pi*x)*sin(n*pi*y)`). 30,000 simulated grains of sand are placed on a 2D plane. Every frame, they read the local gradient of the wave amplitude and accelerate "downhill" towards the zero-amplitude nodal lines where the plate isn't vibrating. NumPy array vectorization allows simulating 30,000 particles at 60 FPS in Python. As the resonant frequencies `n` and `m` morph smoothly over time, the complex geometric figures naturally dissolve and reform into new harmonic states. Brownian noise prevents particles from getting artificially stuck. 15s 60fps MP4.
- **Description**: In a dark, resonant void, 30,000 glowing particles of "digital sand" vibrate violently before suddenly settling into perfectly symmetrical, incredibly complex geometric patterns. As the hidden audio frequencies shift, the sand boils over, scattering into chaos, only to instantly lock into an entirely new, intricate mandala. The sand forms sharp grids, sweeping arcs, and nested loops, glowing with shifting neon hues as the virtual plate slowly rotates.

## kinetic_string_art_geometry

- **Date**: 2026-05-23
- **Theme**: Geometric string art, mathematical curves, parametric equations, laser light show.
- **Technique**: Uses parametric equations to animate 1,500 straight lines connecting points that orbit along multiple concentric 3D circles. The phase multipliers determining the orbital speeds of the endpoints (`m1`, `m2`) are dynamically modulated by sine and cosine waves over time. This causes the thousands of straight lines to mathematically construct beautiful, curved geometric envelopes (similar to a Lissajous curve or a Spirograph) that continually twist, fold, and turn inside out. Rendered in P3D with additive blending and a semi-transparent background to create a brilliant, sweeping motion blur. 15s 60fps MP4.
- **Description**: Thousands of extremely fine, rainbow-colored laser beams connect across a dark void. Because of their precise geometric arrangement, the perfectly straight lines collectively form the illusion of a smooth, sweeping, complex curved surface. As the endpoints orbit at different speeds, the surface dances, twisting into a torus, collapsing into a star, and expanding back into a complex spiraling funnel. The vibrant neon colors wash through the strings like a digital hologram.

## generative_kaleidoscope_mirrors

- **Date**: 2026-05-23
- **Theme**: Optical illusions, kaleidoscope, perfect symmetry, generative curves.
- **Technique**: Demonstrates the mathematical power of matrix transformations (`py5.push_matrix`, `py5.rotate`, `py5.scale`). A highly complex, chaotic, and asymmetrical base segment consisting of twisting, noise-driven 3D bezier curves is calculated and drawn inside a single wedge (1/12th of a circle). This base wedge is then copied, rotated, and mirrored (`scale(1, -1)`) 12 times in a loop. Because the base geometry relies on Perlin noise driven by time, the chaos morphs organically, but the matrix mirroring forces it into absolute, mesmerizing, radial symmetry. 15s 60fps MP4.
- **Description**: Symmetrical ribbons of glowing neon light twist, fold, and bloom like an alien flower inside a massive kaleidoscope. The shapes are chaotic, forming sharp angles and elegant loops, but they are perfectly mirrored across 12 axes. As the entire mandala slowly rotates, the internal geometry breathes and shifts, creating a flawless, deeply satisfying optical illusion of perfect fractal symmetry out of pure random noise.

## abstract_topological_mesh

- **Date**: 2026-05-23
- **Theme**: Topology, non-Euclidean geometry, mathematical surfaces, abstract mesh.
- **Technique**: Uses NumPy's `meshgrid` to highly optimize the calculation of a 10,000-vertex grid ($100 \times 100$). The $Z$-height of each vertex is governed by a dynamic mathematical equation that combines a hyperbolic paraboloid (saddle shape) with time-varying 3D sine and cosine ripples. The mesh is rendered using `py5.TRIANGLE_STRIP` for performance. A strong specular highlight (`py5.specular`, `py5.shininess`) and directional lighting are applied, giving the abstract math surface the appearance of glossy, wet liquid or polished plastic. The color of the mesh maps smoothly to its vertical displacement, shifting over time. 15s 60fps MP4.
- **Description**: A vast, glossy landscape of geometric ripples morphs fluidly in a dark void. The surface bends into a massive, saddle-like shape, while high-frequency ripples wash across it like waves in a thick alien liquid. The mesh shines with intense specular highlights under a bright artificial light. As the landscape slowly spins, its colors shift organically through a spectrum of oceanic cyans, deep blues, and vibrant neon pinks, perfectly matching the peaks and valleys of its mathematical topology.

## chromatic_glitch_cube_field

- **Date**: 2026-05-23
- **Theme**: Glitch art, chromatic aberration, retro-futurism, VHS distortion.
- **Technique**: Instead of slow pixel-by-pixel manipulation, this sketch achieves real-time chromatic aberration by rendering the entire 3D scene three times per frame—once for the Red channel, once for Green, and once for Blue. These passes are composited using `py5.BLEND_MODE(py5.ADD)`. Under normal conditions, the color channels are slightly offset on the X-axis, creating a rainbow edge-fringe. High-frequency 1D Perlin noise dictates a "glitch intensity" variable; when the noise spikes above a threshold, the color channels are violently and randomly displaced in 3D space, causing the white wireframes to shatter into vibrant RGB shadows. A semi-transparent black overlay provides retro CRT scanlines. 15s 60fps MP4.
- **Description**: A vast, dark void is filled with hundreds of tumbling, white wireframe cubes. Suddenly, the video signal appears to tear and glitch. The cubes violently split apart into pure red, green, and blue ghost-images before snapping back together. The camera slowly dollies forward through the field while the intense chromatic aberration and thick CRT scanlines give the piece a raw, analog-video aesthetic.

## sacred_geometry_flower_of_life

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, mysticism, overlapping circles, wave interference.
- **Technique**: The center coordinates for an extensive hexagonal grid are mathematically generated during `setup()`, defining the exact intersection points of a classic Flower of Life pattern spanning 6 concentric layers. During `draw()`, a circle is drawn at each node. Instead of static shapes, the radius, stroke weight, color, and Z-axis depth of every circle are continuously modulated by a radiating sine wave originating from the center. This causes the geometry to "breathe" as overlapping interference patterns cascade outward. Rendered in P3D with additive blending. 15s 60fps MP4.
- **Description**: An intricate lattice of glowing, intersecting neon rings forms the legendary Flower of Life pattern against a dark background. As the entire mandala slowly rotates, pulsating waves of energy ripple outward from its core. The rings expand and contract rhythmically, shifting through brilliant hues of cyan, magenta, and gold. Where the rings overlap, brilliant flares of white light form, giving the ancient symbol a deeply hypnotic, high-tech, and mystical presence.

## algorithmic_diorama_voxel_city

- **Date**: 2026-05-23
- **Theme**: Procedural generation, isometric diorama, voxel art, cyberpunk cityscape.
- **Technique**: A $30 \times 30$ grid of 3D boxes is generated during `setup()` using 2D Perlin noise combined with a radial distance envelope. This forces the tallest "skyscrapers" to cluster in the center of the grid, tapering off into smaller buildings near the edges to create a distinct floating island diorama. The height values are quantized to give a blocky, voxel aesthetic. During `draw()`, the camera is positioned and rotated to create a high-angle isometric-style perspective. The buildings dynamically pulse in height slightly over time, and random 3D Perlin noise is used to make individual buildings flash brightly, simulating glowing neon windows in a living, breathing cyberpunk city. 15s 60fps MP4.
- **Description**: A dense, futuristic mini-city sits on a thick, dark platform floating in empty space. The buildings are rendered as sleek geometric blocks that transition in color from deep oceanic blues at the edges to vibrant magenta and purple at the towering center. The entire diorama slowly rotates on a turntable, while individual skyscrapers blink and pulse with internal neon light, giving the impression of a living, microscopic metropolis.

## kinetic_wave_pendulum

- **Date**: 2026-05-23
- **Theme**: Physics simulation, kinetic art, harmonic motion, pendulum waves.
- **Technique**: Simulates an array of 45 independent, uncoupled pendulums suspended from a single central bar. The length of each pendulum is mathematically calculated using the simple pendulum equation ($T = 2\pi\sqrt{L/g}$) such that the $i$-th pendulum executes exactly $15 + i \times \text{step}$ oscillations over the 15-second duration of the video. When released from a common starting angle, the pendulums quickly fall out of phase, creating mesmerizing traveling waves, chaotic interlaced patterns, and beautiful double/triple helices before finally realigning completely at the 15-second mark. Rendered in P3D with dynamic HSB coloring and a slow cinematic camera pan. 15s 60fps MP4.
- **Description**: 45 glowing, rainbow-colored spheres hang from a massive support beam in a dark 3D void. Released simultaneously, they begin to swing back and forth. Because their string lengths vary slightly, they immediately fall out of sync, creating a hypnotic, snake-like traveling wave of color. As time progresses, the wave breaks down into two waves, then three, then total chaos, before magically snapping back into perfect synchronization exactly at the end of the video.

## quantum_orbital_electron_cloud

- **Date**: 2026-05-23
- **Theme**: Quantum mechanics, electron orbitals, probability density, particle physics.
- **Technique**: Uses NumPy to simulate 50,000 "electrons" in spherical coordinates ($r, \theta, \phi$). Instead of classical Newtonian gravity, the particles orbit chaotically and jitter. Their effective radii are modulated by a simplified spherical harmonic function (`abs(cos(2θ) * sin(3φ))`), which forces the random particle cloud to naturally group into distinct geometric "lobes" reminiscent of complex $d$ or $f$ atomic orbitals. The particles are drawn using `py5.POINTS` with additive blending, accumulating light where probability density is highest. The hue of each particle is tied to its distance from the nucleus. 15s 60fps MP4.
- **Description**: In the center of the void, a bright white nucleus pulses. Surrounding it is a vast, ethereal cloud of 50,000 glowing neon points. The points swarm chaotically, yet their collective motion forms beautiful, symmetrical flower-like lobes—the mathematical shapes of quantum electron orbitals. As the entire atomic structure slowly rotates, the density of the points creates blindingly bright, colorful regions of high probability, leaving dark voids where electrons are forbidden to exist.

## recursive_fractal_tree_3d

- **Date**: 2026-05-23
- **Theme**: Algorithmic botany, L-systems, fractal geometry, nature emulation.
- **Technique**: Uses a classic recursive function (`draw_branch`) in P3D to build a fractal tree with a maximum depth of 8. Unlike simple 2D L-systems, this tree branches out in 3 directions at every node, distributed radially around the local Y-axis. The entire structure is composed of thousands of overlapping lines. The branching angle is driven by a sine wave based on time and the current depth, causing the tree to smoothly expand and contract as if breathing or swaying in an unseen underwater current. The color transitions from a deep magenta trunk to bright cyan/green "leaves" at the outermost tips. 15s 60fps MP4.
- **Description**: A mesmerizing, neon-lit digital tree grows from the bottom of a dark void. It branches out in full 3D space, with thousands of delicate geometric twigs. The entire massive structure slowly rotates while gracefully expanding and contracting. The colors smoothly pulse along its depth, giving the mathematical fractal a deeply organic and hypnotic, lifelike quality.

## fluid_vector_field_interference

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, vector fields, magnetic interference, particle swarm.
- **Technique**: Utilizes highly optimized NumPy arrays to simultaneously calculate the physics of 25,000 independent particles in 3D space. The velocity of each particle is driven by a vector field composed of two separate, off-axis mathematical vortices (acting like tornadoes or magnetic poles) combined with a sinusoidal noise interference layer. As the particles are swept into these currents, their colors shift dynamically based on their speed. Additive blending (`py5.ADD`) and a semi-transparent background frame buffer create a thick, glowing motion blur that beautifully visualizes the invisible fluid flow lines. 15s 60fps MP4.
- **Description**: Thousands of glowing embers swirl violently in the dark, caught in invisible, overlapping tornados. The particles form distinct rings and tubes of light as they are pulled into the twin vortex centers, their colors shifting from cool blue to intense, blinding white-hot magenta as they accelerate. The entire chaotic system slowly tumbles in 3D space, revealing the complex, interwoven spiral patterns of the fluid interference.

## recursive_fractal_spirograph

- **Date**: 2026-05-23
- **Theme**: Spirograph, hypotrochoid math, recursive geometry, 3D ribbons.
- **Technique**: Simulates a series of 4 nested, rotating linkages (similar to a robotic arm or planetary gears). Each linkage rotates on multiple axes (X, Y, and Z) at different speeds, creating a highly complex, chaotic 3D orbit for the final "pen" tip. The tip's position is recorded in a fixed-length memory queue (1500 points). To render the trail, a `py5.TRIANGLE_STRIP` is extruded along the path by calculating the tangent vector and expanding outward to create a flat "ribbon" that tapers and fades at the tail. The entire shape rotates in P3D, producing a mesmerizing, self-intersecting knot of glowing HSB colors. 15s 60fps MP4.
- **Description**: A brilliantly glowing ribbon of rainbow light dances wildly in the center of a black abyss. Like an invisible, multi-jointed pendulum swinging in all three dimensions, it draws an intricate, chaotic, yet perfectly mathematical knot. The glowing trail slowly fades into darkness at its tail, creating a beautiful long-exposure photography effect, as the entire 3D construct smoothly rotates before the viewer.

## generative_terrain_topography

- **Date**: 2026-05-23
- **Theme**: Generative terrain, Perlin noise, topography, retro-futurism (Synthwave aesthetic).
- **Technique**: Evaluates 2D Perlin noise across a 120x90 grid to compute elevation data. Instead of generating a solid mesh with lighting, the terrain is drawn as a wireframe using `py5.TRIANGLE_STRIP` without `py5.fill`. The Y-axis of the noise sampling space is offset by time `t`, creating an infinite scrolling effect that simulates the camera flying forward at high speed over the landscape. The stroke color of each vertex is dynamically mapped to its Z-elevation, transitioning from deep cool blues in the valleys to bright, hot pinks and reds at the mountain peaks. 15s 60fps MP4.
- **Description**: The camera glides swiftly over a vast, undulating wireframe mountain range. The landscape is entirely composed of brightly glowing neon lines against a pitch-black void, reminiscent of 80s synthwave aesthetics and classic vector graphics. Deep valleys flow underneath the camera in cool cyan, while jagged peaks rise up in brilliant magenta and orange, shifting seamlessly as the terrain endlessly generates ahead of the viewer.

## geometric_metatron_cube_3d

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, Metatron's Cube, Vector Equilibrium, esoteric math.
- **Technique**: Constructs the 13 foundational spheres of Metatron's Cube in 3D using the vertices of a cuboctahedron (Vector Equilibrium) plus a central node. All 78 possible connecting lines between these 13 centers are drawn in P3D. The structure rotates smoothly on all three axes while the lines pulse with dynamic HSB neon colors. Lines connected to the center are rendered thicker and brighter, emphasizing the radial energy of the shape, while the vertices themselves are drawn as glowing 3D spheres. 15s 60fps MP4.
- **Description**: A mathematically perfect, glowing geometrical construct floats in the void. It consists of 13 brightly lit spheres connected by an intricate web of 78 intersecting neon lines. As the entire complex structure tumbles and rotates in 3D space, it occasionally aligns perfectly with the camera to reveal the classic 2D sacred geometry pattern of Metatron's Cube, before breaking apart again into complex 3D depth.

## cellular_automata_game_of_life_3d

- **Date**: 2026-05-23
- **Theme**: Cellular automata, emergence, 3D voxel graphics, Game of Life.
- **Technique**: Operates a 32x32x32 state grid using a 3D extension of the Game of Life rules (the "4555 rule": a cell survives if it has 4 or 5 neighbors, and is born if it has exactly 5 neighbors out of the possible 26 in a 3x3x3 Moore neighborhood). The neighbor counting is highly optimized using `scipy.signal.convolve`. To make the visualization compelling, the age of each surviving cell is tracked. When rendered using `py5.box`, older cells grow slightly larger and shift their HSB hue over time, making it easy to distinguish stable geometric structures from chaotic, newly-born noise. 15s 60fps MP4.
- **Description**: A cluster of randomly blinking neon blocks floats in the center of the screen. Suddenly, complex geometric patterns begin to emerge from the noise. Symmetrical gliders shoot off into the darkness, while oscillating central structures slowly shift through rainbow colors as they survive from generation to generation. The camera smoothly orbits the entire 3D voxel structure, revealing the intricate internal architecture of the emergent lifeforms.

## particle_attractor_lorenz_3d

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, vector fields, particle physics.
- **Technique**: Evaluates the Lorenz system equations ($\sigma=10, \rho=28, \beta=8/3$) simultaneously for 30,000 independent particles using highly optimized vectorized NumPy arrays. Each frame, the local vector field determines the velocity of every particle, driving them to orbit the two strange attractor "wings." The rendering uses P3D with `py5.POINTS` and additive blending, combined with a semi-transparent black rectangle over the screen to produce beautiful motion-blurred trails. The color of each particle is dynamically tied to its instantaneous speed and the global time. 15s 60fps MP4.
- **Description**: 30,000 brightly colored neon sparks swirl through a black void, caught in the invisible currents of a mathematical storm. They trace out the famous "butterfly wings" of the Lorenz strange attractor, looping endlessly from one side to the other. Thanks to additive blending, dense clusters of particles glow with intense, blinding light, while fast-moving outliers leave sweeping, wispy rainbow trails behind them as the entire shape slowly rotates.

## algorithmic_crystal_growth

- **Date**: 2026-05-23
- **Theme**: Algorithmic botany, DLA (Diffusion-Limited Aggregation), crystallography, bismuth.
- **Technique**: Uses a 3D NumPy grid (30x30x30) to track crystal nodes. The growth algorithm starts with a single central seed. Every frame, it randomly selects active nodes (biased towards newer nodes via a Beta distribution to encourage branching rather than a solid blob) and spawns neighbors in the 6 cardinal directions. Once a node is formed, it records its "generation" (age). The sketch renders each node using `py5.box` with size and neon HSB coloring determined by its generation. The result is a rapidly branching, fractal-like structure similar to bismuth crystals. Rendered in P3D with directional lighting. 15s 60fps MP4.
- **Description**: In the center of a dark void, a tiny glowing cube appears. Suddenly, it rapidly branches outward in straight lines, spawning thousands of cubic "crystals" that aggressively build a complex, jagged, alien structure in 3D space. As the giant crystalline lattice rotates, its nested layers shimmer in a hypnotic rainbow gradient, highly reminiscent of metallic bismuth crystals.

## quantum_interference_waves

- **Date**: 2026-05-23
- **Theme**: Quantum mechanics, wave interference, ripple tanks, data visualization.
- **Technique**: Evaluates the trigonometric superposition of three moving wave emitters acting upon a dense 150x150 grid of particles (22,500 total). The height (Z-axis) of each particle is calculated as the sum of sine waves propagating outward from each emitter. Constructive and destructive interference creates complex, evolving Moire-like patterns and standing waves. Rendered using `py5.POINTS` in P3D, with the camera tilted to view the resulting 3D landscape. Color mapping is directly tied to the wave amplitude. 15s 60fps MP4.
- **Description**: A vast grid of glowing dots hangs in space, undulating rhythmically like the surface of a liquid. Three invisible sources are moving around the grid, continuously dropping stones into the water. Where their ripples intersect, they create beautiful, constantly shifting geometric peaks and valleys. The colors transition dynamically through the neon spectrum based on how high or low the wave peaks are.

## neon_wireframe_torus_knot

- **Date**: 2026-05-23
- **Theme**: Topology, geometry, wireframe 3D rendering, glowing aesthetics.
- **Technique**: Evaluates the parametric equations for a (3,7) Torus Knot to generate a complex, interlocking continuous curve in 3D space. To render it with volume instead of just a thin line, we calculate the Frenet-Serret frame (tangent, normal, binormal vectors) at every point along the curve. We then extrude a 12-sided circle along these axes, using `py5.begin_shape(py5.TRIANGLE_STRIP)` to draw a hollow, wireframe 3D tube. The entire structure smoothly rotates on all three axes while rainbows of neon colors race rapidly along its length. 15s 60fps MP4.
- **Description**: A highly complex, mathematically perfect 3D knot floats in the center of a black void. Instead of a solid surface, the knot is drawn as an intricate wireframe mesh composed of thousands of glowing neon lines. As the knot rotates smoothly, bright pulses of pink, blue, and green light race around its infinite loops, creating a deeply satisfying, hypnotic visual loop.

## generative_architecture_cityscape

- **Date**: 2026-05-23
- **Theme**: Procedural architecture, 3D cityscapes, cyberpunk, neon lighting.
- **Technique**: Utilizes pure 3D rendering (`py5.box`, `py5.camera`) to build an infinite grid of city blocks. The height of each building is determined by 2D Perlin noise multiplied by a "downtown factor," ensuring taller skyscrapers cluster near the central avenue while shorter buildings spread into the suburbs. The camera constantly pushes forward down the central avenue, dynamically spawning and culling buildings to maintain performance. Dual directional lighting combined with glowing HSB strokes gives the city a distinct neon-drenched, retro-futuristic aesthetic. 15s 60fps MP4.
- **Description**: The camera glides steadily down a wide, empty avenue surrounded by hundreds of towering skyscrapers. The city stretches to the horizon in a dark void. Each building is cast in dark shadows but strongly outlined with brilliant, shifting neon light. As you fly forward, the skyline endlessly generates itself, rising and falling organically like a concrete mountain range.

## cloth_simulation_physics

- **Date**: 2026-05-23
- **Theme**: Physical simulation, Verlet integration, fabric dynamics, neon cyber-aesthetics.
- **Technique**: Uses NumPy to compute Verlet integration physics for a 50x50 grid of connected nodes (2,500 total particles). The grid enforces structural spring constraints to maintain its shape, with the top edge pinned in space. Gravity constantly pulls the nodes downward, while a 3D Perlin noise field applies a continuous, turbulent "wind" force, pushing the fabric backwards. The cloth is rendered in P3D using `py5.QUADS`, mapping the Z-depth (how far the wind pushes the fabric) and the X/Y coordinates directly to the HSB color wheel. 15s 60fps MP4.
- **Description**: A massive, brilliantly colored neon sheet hangs suspended in a dark void. As an invisible digital wind strikes it, the fabric ripples, folds, and violently billows backwards, throwing off a mesmerizing gradient of shifting rainbow colors that highlight every wrinkle and fold of the simulated cloth.

## recursive_tree_fractal_canopy

- **Date**: 2026-05-23
- **Theme**: Generative botany, fractals, recursion, natural motion.
- **Technique**: Utilizes pure recursive functions to draw fractal trees. At each step, a branch draws a line, translates to the tip, and recursively calls itself to draw 2 or 3 smaller branches at specific angles. To breathe life into the static mathematical structure, `py5.noise()` (Perlin noise) is sampled using the branch depth and time, modifying the rotation angles to simulate propagating waves of wind passing through the canopy. Rendered in P3D with additive blending and a semi-transparent motion blur background. 15s 60fps MP4.
- **Description**: Three massive, neon-glowing trees rise from the bottom of the canvas, immediately splitting into thousands of tiny, intricate branches. Glowing circular "leaves" sit at the tips of the fractal structure. As time passes, the colors smoothly shift through the rainbow, and the entire incredibly dense canopy sways and flexes organically as if blown by a gentle breeze.

## hypnotic_moire_interference

- **Date**: 2026-05-23
- **Theme**: Optical illusions, Moiré patterns, wave interference, Op Art.
- **Technique**: Uses pure 2D geometric vector drawing (`py5.begin_shape`, `py5.circle`). By overlapping extremely dense arrays of lines (radial bursts) and closely-spaced concentric circles, and rotating/translating them at slightly different speeds and offsets, massive macroscopic interference patterns naturally emerge. This visual artifact, known as a Moiré pattern, creates the illusion of curving waves and ghostly glowing bands moving across the screen, even though the underlying geometry consists only of rigid straight lines and perfect circles. Additive HSB blending provides a vivid neon aesthetic. 15s 60fps MP4.
- **Description**: Two dense bursts of colorful lines slowly rotate in opposite directions, while tight rings of concentric circles expand and contract. Because the lines are so densely packed, your eyes and the pixels physically interact to create giant, sweeping, ghostly waves of light that ripple horizontally and vertically across the canvas. It is a striking, hypnotic optical illusion.

## fractal_brownian_motion_terrain

- **Date**: 2026-05-23
- **Theme**: Procedural generation, retro 3D graphics, outrun/synthwave aesthetics, terrain mapping.
- **Technique**: Utilizing `py5.begin_shape(py5.TRIANGLE_STRIP)`, we generate a 60x60 3D mesh grid. The vertical (Z) position of each vertex is determined by 2D Perlin noise (`py5.noise()`). To create the sensation of forward flight, the Y-coordinate sampled from the noise space is constantly offset downwards over time. The edges of the grid smoothly fade to black using a distance falloff mask. Rendered in P3D with dynamic neon HSB coloring mapped to altitude. 15s 60fps MP4.
- **Description**: The camera hurtles endlessly over a sprawling, mountainous digital landscape. The neon wireframe mountains shift colors from deep blue in the valleys to bright purple and pink at their peaks. As you fly forward, new mountains smoothly roll into existence from the black horizon, perfectly evoking the aesthetic of 1980s vector graphics and modern Synthwave art.

## differential_growth_coral

- **Date**: 2026-05-23
- **Theme**: Algorithmic botany, differential growth, biological simulation.
- **Technique**: We start with a simple ring of 30 connected nodes. In every frame, the nodes attempt to maintain a comfortable distance from their neighbors (spring force) while actively repulsing any other node that gets too close. If the distance between two connected nodes exceeds a threshold, a new node is spawned between them. This continuous division and repulsion causes the line to organically fold, buckle, and crinkle into itself, creating incredibly dense, labyrinthine shapes. Vectorized physics logic allows it to grow to over 8,000 nodes smoothly. 15s 60fps MP4.
- **Description**: A smooth, glowing neon circle violently crinkles and folds inward. As it rapidly expands, it packs itself into a dense, brain-like labyrinth of glowing curves. The colors cycle continuously along the perimeter, sending waves of rainbow light pulsing through the tightly packed geometric coral structure.

## sacred_geometry_mandala

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, kaleidoscope symmetry, vector graphics, spiritual algorithms.
- **Technique**: Instead of manipulating pixels directly, this work uses crisp, mathematical vector graphics (`py5.begin_shape`, `py5.vertex`, `py5.circle`). It draws 12 concentric layers of geometry—alternating between polygons, stars, and rings of circles. Each layer rotates independently, with alternating directions and variable speeds. The radii of the shapes gently pulse using sine waves. Drawn with semi-transparent neon colors (HSB) and additive blending over a faintly fading background to create light trails. 15s 60fps MP4.
- **Description**: A mesmerizing array of neon shapes (stars, triangles, and circles) rapidly spin and pulse from the center of the canvas. Because each layer is rotating at slightly different speeds and directions, the entire structure behaves like an incredibly complex mechanical clock or a digital kaleidoscope, hypnotically expanding and contracting in perfect symmetry.

## vector_flow_field_particles

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, vector fields, particle trails, generative art.
- **Technique**: To maintain 60fps while simulating 500,000 particles, we bypass computationally heavy Perlin noise and instead generate a smooth pseudo-random flow field using a combination of multiple low-frequency sine and cosine waves. This creates continuous, chaotic eddies and currents. The particles update their positions based on this vector field every frame. The background is only faintly cleared (10/255 opacity) each frame, allowing the particles to leave extremely long, smooth light trails. Rendered via additive blending directly into the `py5.np_pixels` buffer. 15s 60fps MP4.
- **Description**: Millions of bright cyan, blue, and white strands flow across the dark canvas like glowing silk threads caught in an invisible river. They converge into massive, swirling vortexes and split along unseen ridges. As the invisible math underlying the currents slowly shifts over time, the beautiful, complex structures elegantly unspool and reform into new shapes.

## metaballs_liquid_metal

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, implicit surfaces, metallic reflections, retro demoscene.
- **Technique**: We simulate 30 bouncy physics particles and compute a 2D scalar field representing their inverse-square distance functions. Instead of rendering them as solid blobs, we pass the scalar field through phase-shifted periodic sine functions. This creates alternating bands of light and dark that perfectly mimic the environmental reflections of shiny liquid metal (like mercury or chrome). The outer boundary is clamped via a hard threshold mask. Computed completely via vectorized NumPy grid operations and upscaled to full resolution. 15s 60fps MP4.
- **Description**: 30 spheres of liquid mercury fly around a pitch-black canvas. When they get close, they seamlessly snap together and merge into larger, amorphous blobs. The intricate, wavy light bands inside the blobs constantly shift and distort, creating an extremely convincing metallic sheen that reflects an invisible, striped environment.

## neural_network_activation_landscape

- **Date**: 2026-05-23
- **Theme**: Artificial intelligence, latent space, continuous neural representations, generative art.
- **Technique**: We construct a 2-hidden-layer Multi-Layer Perceptron (MLP) purely in NumPy. A dense grid of 2D $(X, Y)$ coordinates acts as the input batch, and we perform a full forward pass (`Dense -> ReLU -> Dense -> ReLU -> Dense -> Sin`) for every pixel on the canvas simultaneously. Over time, the internal weight matrices of the network are smoothly rotated using a skew-symmetric matrix multiplier, simulating a slow, continuous walk through the network's high-dimensional latent space. The 3-channel output is directly mapped to the RGB pixel buffer. 15s 60fps MP4.
- **Description**: The screen is covered in smooth, surreal blobs and sharply creased bands of vibrant color. As the hidden "brain" slowly rewires its internal connections, the decision boundaries warp, flow, and fold into one another. It feels like peering into the fluid, geometric dreams of an artificial intelligence.

## lorenz_attractor_particle_flow

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, meteorology, fluid dynamics.
- **Technique**: 200,000 independent particles are initialized in a tight cluster near the origin and iteratively integrated through the classical Lorenz equations using a high-speed vectorized NumPy Euler solver. Instead of drawing static lines, the particles dynamically flow through the attractor's phase space, leaving decaying, semi-transparent light trails. The 3D coordinates are rotated with a virtual camera and projected directly into the `py5.np_pixels` buffer using additive blending. Colored based on their vertical (Z) position, creating a glowing gradient from Deep Purple to Hot Pink to Bright Orange. 15s 60fps MP4.
- **Description**: A tight knot of glowing plasma explodes outward, rapidly tracing the iconic butterfly wings of the Lorenz attractor. The particles flow like a torrential, glowing fluid, endlessly looping and crossing between the two chaotic basins. The camera slowly orbits the structure, revealing the infinitely thin, fractal layers that make up this beautiful mathematical anomaly.

## boids_flocking_swirl

- **Date**: 2026-05-23
- **Theme**: Artificial life, emergence, flocking, Craig Reynolds' boids.
- **Technique**: Simulates 10,000 autonomous "boids" using a randomized neighborhood approximation to calculate Separation, Alignment, and Cohesion forces in real time without dropping framerate. The boids are drawn directly to the `py5.np_pixels` buffer, creating smooth additive light trails that slowly fade over time. Colored based on their velocity, transitioning from deep ocean blue to bright bioluminescent cyan as they accelerate. 15s 60fps MP4.
- **Description**: Like a glowing school of deep-sea fish or a swarm of cybernetic fireflies, thousands of bright blue trails swirl around the screen. They continuously split apart, merge, and form massive swirling vortexes, demonstrating how complex, beautiful group dynamics can arise from simple individual rules.

## magnetic_pendulum_fractal

- **Date**: 2026-05-23
- **Theme**: Physics simulation, fractals, chaos theory, basins of attraction.
- **Technique**: Instead of simulating a single pendulum swinging between three magnets, we treat the entire canvas as a grid of 500,000 different starting positions $(X, Y)$ and simulate them all simultaneously using vectorized NumPy operations. Over the course of the 15-second animation, the positions of all pendulums are integrated using Euler's method. The color of each pixel corresponds to the proximity of its respective pendulum to the three magnets (Red, Green, Blue). As the pendulums fall into the gravitational and magnetic wells, the smooth color fields shatter into infinitely complex fractal boundaries. 15s 60fps MP4.
- **Description**: What begins as a smooth, blurry RGB gradient slowly warps and folds as the invisible pendulums start swinging. Gravity and magnetism violently pull the system apart, revealing a stunning, razor-sharp fractal crystal where tiny changes in starting position determine which magnet a pendulum ultimately lands on.

## strange_attractor_clifford_morph

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, dynamical systems.
- **Technique**: An ultra-fast vectorized Python simulation mapping 500,000 points through the Clifford attractor equations iteratively. Instead of static parameters, the variables $(a,b,c,d)$ are modulated by smooth sine waves over the 15-second duration, causing the fractal structure to seamlessly unfold, collapse, and transform. A dense 2D histogram (density map) is calculated each frame using `numpy.add.at` and mapped to a Cyberpunk-inspired Magenta, Blue, and Cyan additive palette directly in the pixel buffer. 15s 60fps MP4.
- **Description**: Millions of microscopic particles dance along invisible mathematical boundaries, tracing out impossibly intricate, folding shapes. As time progresses, the rules of the universe shift—causing the ghostly, neon-lit geometric web to warp and tear, constantly revealing new, mesmerizing symmetries hidden within the chaos.

## slime_mold_physarum

- **Date**: 2026-05-23
- **Theme**: Biological growth, multi-agent systems, emergent behavior, slime mold.
- **Technique**: A massive multi-agent particle simulation running entirely on a 2D grid. 150,000 independent sensory agents deposit chemical pheromones on the grid as they move. They also sense the local pheromone gradient using three forward sensors and steer towards the highest concentration. The global pheromone grid is continuously diffused and decayed using `scipy.ndimage.gaussian_filter`. Rendered via nearest-neighbor upscaling into a bio-luminescent Electric Green and Deep Violet palette directly in the `py5.np_pixels` buffer. 15s 60fps MP4.
- **Description**: What starts as an amorphous ring of individual particles quickly organizes into striking, pulsing transport networks. The agents follow each other's chemical trails, spontaneously forming dense super-highways of glowing electric green that branch, weave, and restructure themselves like the veins of a living organism.

## solar_corona_magnetic_loops

- **Date**: 2026-05-23
- **Theme**: Astrophysics, solar flares, magnetic flux loops, plasma dynamics.
- **Technique**: A 3D procedural physics simulation modeling 150,000 plasma tracers flowing along magnetic field lines generated by multiple dipole pairs (sunspots). The field is perturbed by a time-varying volumetric noise function to simulate turbulent convection. Rendered via a manual 3D projection mapped directly into the `py5.np_pixels` buffer for ultra-fast additive blending, using a temperature-based Crimson-Orange-Gold palette. 15s 60fps MP4.
- **Description**: The dark surface of a stellar void erupts with towering, interlocking arches of blinding gold and crimson plasma. As the camera slowly orbits the scene, the magnetic flux tubes twist and weave, guiding rivers of high-energy particles that beautifully illustrate the immense, invisible electromagnetic forces shaping the solar corona.

## double_pendulum_fractal_map

- **Date**: 2026-05-23
- **Theme**: Chaos theory, fractal boundaries, double pendulum, phase space.
- **Technique**: A 2D parameter space grid (where $X = \theta_1$ and $Y = \theta_2$) represents the initial starting angles of over 500,000 double pendulums. A highly vectorized NumPy physics engine integrates the equations of motion for all pendulums simultaneously using a sub-stepped Euler/Runge-Kutta approximation. The current angle $\theta_2$ of each pendulum is mapped to a continuous spectral color map, creating an intricately folding fractal that reveals the chaotic boundaries of the system over time. 15s 60fps MP4.
- **Description**: A smooth, beautifully colored gradient gradually warps, stretches, and folds in upon itself with infinite complexity. As the hidden pendulums swing, the phase space shatters into a breathtaking, swirling fractal pattern, perfectly visualizing how microscopic changes in initial conditions lead to wildly divergent and chaotic futures.

## reaction_diffusion_turing_patterns

- **Date**: 2026-05-23
- **Theme**: Turing patterns, reaction-diffusion, biological self-organization, Gray-Scott model.
- **Technique**: 2D Reaction-Diffusion PDE solved via finite difference method on a downscaled grid using `scipy.ndimage.convolve` for vectorized Laplacian operations. Chemical concentrations are iteratively updated across 8 sub-steps per frame. Feed and kill rates dynamically shift over time to transition the system from isolated spots to dense labyrinths and chaotic stripes. The resulting chemical field is upscaled and rendered directly to `py5.np_pixels` using a Deep Purple, Cyan, and Neon Orange color map. 15s 60fps MP4.
- **Description**: A mesmerizing, organic progression of life-like patterns. Starting from a dark purple void, vibrant cyan and neon orange chemical reactions spontaneously emerge, slowly growing into isolated cellular spots that gradually fuse, morph, and stretch into complex, shifting labyrinths resembling coral or animal skin.

## lissajous_knot_orbital_decay

- **Date**: 2026-05-23
- **Theme**: Orbital mechanics, resonance, Lissajous figures, 3D geometry.
- **Technique**: Vectorized 3D parametric equations generating 120,000 orbital tracers. The frequencies $f_x, f_y, f_z$ are linearly interpolated from irrational starting ratios ($\pi, e, \phi$) down to a 1:1:1 resonance over time. Rendered directly into the `py5.np_pixels` buffer for massive performance additive blending with a fading background, using a Cyan-to-Magenta structural palette. 15s 60fps MP4.
- **Description**: An incredibly intricate, tangled ball of glowing neon threads spins in the dark void. As time passes, the chaotic orbits begin to align, gradually simplifying the knot's geometry until the entire system collapses into a single, majestic, perfectly synchronized ring of light.

## non_euclidean_poincare_disk

- **Date**: 2026-05-23
- **Theme**: Non-Euclidean geometry, hyperbolic space, Poincaré disk model, infinite recursion.
- **Technique**: Procedural pixel-shader simulation. Maps the pixel canvas to the complex plane, restricts it to the unit disk, and applies time-varying Möbius transformations to simulate translation/zooming in hyperbolic space. The transformed hyperbolic distance drives a trigonometric tessellation pattern, colored with a shimmering Cyan-Emerald-Violet palette. 15s 60fps MP4.
- **Description**: A glowing circular window into a non-Euclidean universe. As the view translates endlessly forward, intricate, shimmering geometric forms flow out from the impossibly deep boundary, expanding gracefully as they approach the center before folding away, visualizing the mind-bending infinite space contained within a finite disk.

## magnetic_reconnection_plasma

- **Date**: 2026-05-23
- **Theme**: Magnetic reconnection, solar flares, plasma physics.
- **Technique**: Vectorized 2D simulation of a Sweet-Parker / Petschek magnetic reconnection event. 150,000 plasma tracer particles are advected by a time-varying magnetic field that snaps and reconfigures at $t=0.5$, releasing high-velocity jets. Directly manipulates the `py5.np_pixels` buffer for extreme performance additive blending, mapping particle velocity to a Gold-to-Magenta color gradient. 15s 60fps MP4.
- **Description**: Opposing magnetic fields slowly compress a glowing sheet of golden plasma. Suddenly, the field lines snap and reconnect, instantly accelerating the plasma into violent, blinding magenta jets that shoot outward in opposite directions, visualizing the catastrophic energy release of a solar flare.

## boid_murmuration_fluid

- **Date**: 2026-05-23
- **Theme**: Fluid flocking dynamics resembling organic murmuration.
- **Technique**: Vectorized boids simulation featuring 120 flock leaders and 30,000 follower agents. Leaders interact via separation, alignment, cohesion, and central attraction. Agents are strongly attracted to their respective leaders and align with their velocity, adding local noise. Rendered using additive blending on a dark indigo background. 15s 60fps MP4.
- **Description**: Thousands of tiny sparks sweep across a dark indigo sky, suddenly folding and swooping together into massive, undulating ribbon-like shapes that feel both organic and perfectly synchronized.

## adaptive_nerve_bloom

- **Date**: 2026-05-23
- **Theme**: Emergent intelligence and neural connections.
- **Technique**: Network graph simulation with 180 nodes and dynamic distance-based synapses. Signal propagation is visualized through pulsing edge brightness and node activation radii. Rendered with a Cyan, Magenta, and Gold palette over a dark canvas. 15s 60fps MP4.
- **Description**: The dark canvas blooms with a constellation of cyan, magenta, and gold neural nodes. Connections between neurons pulse with energy as signals propagate through the network, creating an ever-shifting web of computational activity. The animation captures the essence of intelligence emerging and organizing itself in real time.

## strange_attractor_aizawa

- **Date**: 2026-05-23
- **Theme**: The mathematical beauty of the Aizawa strange attractor and chaotic orbits.
- **Technique**: 2.5D point cloud with 80,000 tracers using the Aizawa attractor equations. Additive blending with a shifting HSB palette of deep cyan, emerald, and gold. 15s 60fps MP4.
- **Description**: Tens of thousands of glowing particles flow from the center to map out the hypnotic, spherical shape of the Aizawa strange attractor. As they orbit, their trajectories illustrate the delicate balance between determinism and chaos, shifting in hue to create a vibrant, glowing mathematical sculpture in the void.

## hopf_fibration_flow

- **Date**: 2026-05-23
- **Theme**: The mathematical beauty of the Hopf fibration, showing linked circles flowing seamlessly through each other in 3D space.
- **Technique**: 3D point cloud of 50,000 particles parameterized by angles on S2 and a fiber angle. The points flow along the fiber angle and are stereographically projected into R3. Additive blending with spectral colors mapped to the base angle. 15s 60fps MP4.
- **Description**: Thousands of glowing particles weave together into an intricate set of interlinked tori. As the system flows, the particles trace the continuous, non-intersecting rings of the Hopf fibration, projecting higher-dimensional geometry into a mesmerizing dance of light.

## bifurcation_attractor_swarm

- **Date**: 2026-05-23
- **Theme**: Chaotic attractors undergoing bifurcation, mapped by a glowing swarm of particles.
- **Technique**: 2.5D rendering of the Lorenz attractor equations mixed with custom sine-wave perturbations. 50,000 tracers. Additive blending with a hot pink, violet, and deep blue palette. 15s 60fps MP4.
- **Description**: Thousands of glowing points stream through a dark void, painting the structure of a mathematical strange attractor. Over time, the parameters driving the system shift, causing the orbital paths to deform and bifurcate into increasingly complex patterns of motion.

## fractal_brownian_terrain

- **Date**: 2026-05-23
- **Theme**: A sweeping 3D landscape generated by moving Fractional Brownian Motion (fBm) noise, projecting a neon-lit wireframe terrain that shifts and evolves as we fly over it in a dark void.
- **Technique**: 2.5D rendering using py5's P3D mode, moving noise grid using `py5.noise()`, mapping noise to height. Additive blending with vibrant neon color transitions based on height. 15s 60fps MP4.
- **Description**: An endless flight over a shimmering mathematical landscape. As the terrain flows beneath, the neon wireframe contours shift dynamically, illustrating the complex, fractal nature of continuous 2D noise translated into 3D heightmaps.

## chromatic_vector_field_glitch

- **Date**: 2026-05-23
- **Theme**: A swirling, dynamic vector field driven by Perlin noise, traversed by thousands of glowing particles, which experiences intense noise spikes that datamosh the buffer.
- **Technique**: Procedural simulation of 10,000 particles moving through an OpenSimplex noise-based vector field. Particles are rendered with time-evolving HSB hues and additive blending. Random noise bursts inject intense localized chaos into the particle trajectories, while NumPy is used to trigger horizontal block datamoshing across the final rendered frame. 15s 60fps MP4.
- **Description**: The flow of structured data through an unstable network. Ten thousand data points follow smooth, continuous fluid paths governed by a hidden mathematical manifold, only to be intermittently slammed by catastrophic digital interference that rips the structure apart and forces hard resets of the trajectories.

## holographic_lattice_collapse

- **Date**: 2026-05-23
- **Theme**: A 3D isometric or pseudo-3D hexagonal lattice that shimmers holographically in neon colors, and then collapses due to randomized scaling and displacement glitches over time.
- **Technique**: Procedural P3D grid of polygons, additive blending, sine wave based height maps mapped to color, and random glitch displacements applied to vertices and global pixels based on noise. Datamosh tearing via NumPy array manipulation. 15s 60fps MP4.
- **Description**: A visualization of an idealized, shimmering geometric manifold suffering from catastrophic data collapse. The piece juxtaposes the rigid, mathematical beauty of an undulating 3D lattice with the aggressive, unpredictable nature of digital corruption.

## quantum_interference_glitch

- **Date**: 2026-05-23
- **Theme**: The delicate, shimmering interference patterns of quantum waves that violently shear and split into bright RGB noise when observed.
- **Technique**: Procedural interference patterns mapped to saturated neon colors (Cyan, Magenta, Yellow), with sudden chaotic horizontal and vertical tearing using NumPy pixel manipulation. 15s 60fps MP4.
- **Description**: A visualization of a structured quantum system experiencing sudden decoherence. The piece begins with harmonious, overlapping interference rings from multiple wave sources, but as the timeline progresses, the "observation effect" intensifies, tearing the simulation apart through violent spatial shifts and RGB channel inversions.

## neon_cellular_datamosh

- **Date**: 2026-05-23
- **Theme**: The relentless, infectious spread of corrupted data through a structured system, represented by neon cellular automata bleeding into chaotic horizontal datamosh lines.
- **Technique**: Procedurally generated cellular rectangles drawn with high saturation RGB colors (Cyan, Magenta, Yellow, Green) on a dark background. NumPy is used for real-time pixel manipulation, introducing horizontal screen tearing and RGB channel swapping to simulate datamoshing and signal corruption. 15s 60fps MP4.
- **Description**: A visualization of a structured digital system being overwhelmed by vibrant, chaotic data corruption. Clean geometric shapes are continuously ripped apart and color-shifted, leaving neon trails that bleed across the canvas in unpredictable patterns.

## cybernetic_flora_corruption

- **Date**: 2026-05-22
- **Theme**: Organic growth trying to establish order, but constantly being disrupted by vibrant digital corruption.
- **Technique**: Procedurally generated cybernetic floral structures (Maurer-inspired roses) rotating and blooming over time, rendered with RGB channel splitting. A secondary NumPy pixel-manipulation pass introduces horizontal datamoshing and block tears across the canvas. 15s 60fps MP4.
- **Description**: A delicate, geometric flower blooms slowly in the obsidian void. As it opens, its structural integrity stutters and shears, bleeding intense neon cyan, magenta, and yellow data across the frame, leaving vibrant datamosh trails in its wake.

## lbm_karman_vortex_street

- **Date**: 2026-05-22
- **Theme**: The mesmerizing, repeating pattern of swirling vortices created by a fluid as it is forced around an obstacle.
- **Technique**: Vectorized 2D Lattice Boltzmann Method (D2Q9) simulation. Dynamic vorticity is mapped to a diverging thermal/teal colormap. 15s 4K/60fps MP4.
- **Description**: A smooth, deep blue river flows silently until it hits a solid pillar. Rhythmic, alternating crimson and cyan whirlpools peel off from the edges of the pillar, drifting downstream in a complex dance of interacting eddies.

## ginzburg_landau_spiral_defects

- **Date**: 2026-05-22
- **Theme**: The mesmerizing, spontaneous emergence of rotating spiral waves and topological defects in a complex oscillatory medium.
- **Technique**: Vectorized 2D simulation of the Complex Ginzburg-Landau Equation (CGLE) solved via FDTD. The complex phase maps to a vibrant synthwave spectrum. 15s 4K/60fps MP4.
- **Description**: A bubbling, chaotic sea of iridescent noise quickly synchronizes. Distinct pacemakers emerge, emitting rhythmic, expanding rainbow rings that curl into spinning, interlocking multi-armed spirals.

## hopf_fibration_projection

- **Date**: 2026-05-22
- **Theme**: The mathematical elegance of the Hopf Fibration, projecting the 4D hypersphere onto 3D space as a seamless arrangement of interlocking, luminous circular fibers.
- **Technique**: Parametric 4D generation of Hopf circles projected via Stereographic projection from S3 to R3, and then to 2D. Rendered as luminous, silken threads using an additive blend mode. 15s 4K/60fps MP4.
- **Description**: A massive, shimmering torus made of hundreds of interlocking glowing rings slowly rotates in the void. As it turns inside out in 4D space, waves of iridescent colors flow smoothly along the fibers.

## crystal_dislocation_glide

- **Date**: 2026-05-22
- **Theme**: The sudden, violent slipping of microscopic lattice defects through an atomic crystal under immense pressure, visualizing the invisible physics of plastic deformation.
- **Technique**: Vectorized 2D Sine-Gordon (Frenkel-Kontorova) phase-field model. Computes atomic displacement under macroscopic shear stress with local yielding and dislocation avalanches. 15s 4K/60fps MP4.
- **Description**: A perfectly ordered, shimmering ice-blue atomic grid slowly deforms. Suddenly, brilliant amber fault lines rip diagonally through the structure, accompanied by a cascade of localized structural rearrangements that echo like a microscopic earthquake.

## hyper_chromatic_glitch_fold

- **Date**: 2026-05-22
- **Theme**: A high-density data matrix folding and tearing itself apart, bleeding brilliant spectral colors as its structural integrity collapses under recursive glitches.
- **Technique**: Vectorized recursive grid subdivision with pseudo-random chromatic displacement, localized horizontal tearing (row-shifting), and high-frequency noise injection. Multi-pass RGB channel splitting. 15s 4K/60fps MP4.
- **Description**: A perfect, dense geometric grid suddenly shivers, splitting into blinding neon magenta and cyan channels. Horizontal tears slice across the frame, ripping the structure apart while golden noise bleeds into the fractures.

## salt_finger_convection_sim

- **Date**: 2026-05-22
- **Theme**: Double-diffusive convection where warm, salty water lies over cold, fresh water, creating intricate falling salt fingers and rising thermal plumes due to differing diffusion rates.
- **Technique**: Vectorized 2D Boussinesq Navier-Stokes with two coupled advection-diffusion scalar fields (Temperature and Salinity). 15s 4K/60fps MP4.
- **Description**: Deep oceanic indigo background is cut through by electric cyan falling salt fingers and warm gold rising thermal plumes.

## taylor_couette_vortices

- **Date**: 2026-05-18
- **Theme**: The hydrodynamic transition of a fluid confined between concentric rotating cylinders, shifting from beautifully stacked, orderly toroidal vortices to undulating waves and chaotic turbulence.
- **Technique**: Vectorized 3D Navier-Stokes advection on a cylindrical coordinate grid representing Taylor-Couette flow, advecting 120,000 tracer particles. The simulation dynamically transitions from laminar Taylor vortex flow to wavy vortex flow by modulating the Taylor shear number over time. Projected manually into 3D space with slow cylindrical orbital rotation and depth fading. 15s 4K/60fps MP4.
- **Description**: A stunning, hollow cylinder of glowing sapphire tracers rotates majestically in pitch-black space, organizing into a vertical stack of six glowing toroidal vortices. Tracers spiral dynamically inside each torus around a soft, molten copper core. As the outer shear increases, the stacked tori sway and wave in an undulating rhythm before dissolving into a turbulent sienna and blue spray, then cleanly reforming.

## fput_recurrence_lattice

- **Date**: 2026-05-18
- **Theme**: The paradox of a non-linear lattice of coupled oscillators that, instead of thermalizing and distributing energy evenly, periodically returns to its initial low-frequency state in a majestic act of coherence.
- **Technique**: Vectorized 1D FPUT chain simulation with alpha non-linear coupling, Velocity Verlet integration, manual 3D perspective projection, and 150,000 glowing particles in additive blending. Color-mapped by local thermal energy density and real-time Fourier modal spectrum rings. 15s 4K/60fps MP4.
- **Description**: An elegant, shimmering double helix in electric cyan shatters dynamically into high-frequency amethyst and rose-pink thermalized ripples, before condensing back into a pristine, coherent wave with a blinding gold-white core, surrounded by concentric background rings of light.

## schlieren_thermal_plumes

- **Date**: 2026-05-18
- **Theme**: Visualizing the invisible convection currents of heat rising off a glowing wire, using the Schlieren optical effect.
- **Technique**: 2D particle simulation (150,000 tracers) advected by a multi-harmonic curl noise field representing convective turbulence. Rendered with additive blending and faint silver strokes to simulate the gathering of refracted light. 15s 4K/60fps MP4.
- **Description**: Deep, high-contrast monochrome with sharp, shimmering wisps of faint electric blue and silver light that curl and fold into each other like smoke, but with optical purity.

## ferrofluid_rosensweig_instability

- **Date**: 2026-05-18
- **Theme**: The spontaneous emergence of hexagonal spikes on the surface of a magnetic fluid when subjected to a vertical magnetic field.
- **Technique**: 2.5D height field simulation using a continuous relaxation model balancing magnetic pressure against gravity and surface tension, rendered with high-contrast specular highlights. 15s 4K/60fps MP4.
- **Description**: A dark, glossy metallic fluid that suddenly erupts into sharp, crystalline spikes, reflecting deep violet and gold light.

## abrikosov_vortex_depinning

- **Date**: 2026-05-17
- **Theme**: Type-II superconductivity, Abrikosov flux lattice, pinning potential wells, elastic depinning, AC transport current, plastic flow channels.
- **Technique**: Vectorized 2D Langevin equations of motion for 400 repulsive vortices interacting via a screened Yukawa-like potential, trapped in an attraction landscape of 80 fixed Gaussian potential wells under an oscillating AC transport drive. Velocity-mapped color styling and persistent fading trails. 15s 4K/60fps MP4.
- **Description**: A stunning simulation of Abrikosov vortex depinning. A perfect hexagonal lattice of electric cyan quantum vortices is trapped by 80 fixed violet pinning centers. As an alternating horizontal driving force is applied, channels of vortices shear into glowing magenta and gold, carving sinuous, rushing vortex rivers that slide through pinning channels and trace permanent, silken highways of light.

## photoelastic_granular_jamming

- **Date**: 2026-05-17
- **Theme**: Granular physics, photoelastic stress birefringence, contact force chains, jamming transitions.
- **Technique**: 2D soft-sphere Discrete Element Method (DEM) using spring-dashpot contact dynamics solved in a multi-step vectorized NumPy physics engine, integrated with a multi-layered polariscope photoelastic rendering model. Concentric stress-induced colorful circular fringes centered at the contact points and 1,000+ contact-force neon lines. 15s 4K/60fps MP4.
- **Description**: A stunning simulation of photoelastic granular jamming. 650 translucent dark glass beads are compressed by a modern glassy cyan piston, building a dense network of glowing amber and gold contact force chains. As they are compressed, the beads glow from within with nested deep purple, neon pink, and solar gold stress fringes, dynamically rearranging and locking under pressure.

## viscous_fingering_hele_shaw

- **Date**: 2026-05-17
- **Theme**: Saffman-Taylor instability, viscous fingering, fluid confinement, fractal branching, competitive growth
- **Technique**: Grid-based discrete Laplace equation solver via Jacobi relaxation, Dielectric Breakdown Model (DBM) boundary growth with pre-cached Gaussian-smoothed spatial noise, and high-density advected flow tracer simulation. Multi-velocity point styling (drawing 80,000 tracer particles grouped into three speed classes with custom opacity and weight). 15s 4K/60fps MP4.
- **Description**: A stunning simulation of Saffman-Taylor instability in a confined Hele-Shaw cell. Mesmerizing, organic fractal-branching fingers of electric cyan and neon teal grow outward from a central seed into a deep royal indigo fog. The active growth tips are highlighted with an incandescent, warm gold glow, while 80,000 silken tracer particles curve gracefully along the fluid flow lines, mapping the invisible pressure gradients.

## kuramoto_phase_synchronization

- **Date**: 2026-05-17
- **Theme**: Kuramoto model, spontaneous synchronization, firefly rhythms, emergent order.
- **Technique**: 2D grid-based Kuramoto model simulation on a 640x360 grid. Each pixel acts as a coupled oscillator with a natural frequency derived from continuous 2D noise. Oscillators couple with their 4 nearest neighbors, pulling each other's phase. The phase $\theta$ is mapped to a sharp brightness curve ($\sin^4(\theta)$) to simulate flashes of light. Rendered with a Deep Indigo / Cyan / Golden Glow palette using `py5.np_pixels`. 15s 4K/60fps MP4.
- **Description**: A mesmerizing macro-view of emergent order; hundreds of thousands of individual, chaotic sparks of light begin to influence one another, slowly synchronizing into majestic sweeping waves of golden-cyan flashes against a deep indigo void, reminiscent of bioluminescent fireflies coordinating their rhythms in a dark forest.

## mobius_geodesic_flow

- **Date**: 2026-05-17
- **Theme**: Non-orientable topology, continuous flow, mathematical beauty.
- **Technique**: 3D simulation of 150,000 particles constrained to a parametric Möbius strip. Particles follow a continuous flow field parameterized by $(u, v)$ and wrap seamlessly around the non-orientable boundary. Manual 3D-to-2D perspective projection. Rendered with multi-pass additive point rendering using `py5.points` with a Cyan/Violet/Magenta HSB palette against a dark void. 15s 4K/60fps MP4.
- **Description**: A majestic mathematical sculpture of light; a continuous, glowing ribbon twists and loops through a dark void, its surface composed of thousands of silken threads that flow endlessly along its non-orientable topology in a shimmering dance of cyan and violet energy.

## polymer_chain_langevin_dynamics

- **Date**: 2026-05-17
- **Theme**: Microscopic polymer chains floating in a heat bath, folding and unfolding randomly under thermal noise and a swirling fluid field.
- **Technique**: 2D Langevin dynamics simulation of 150 polymer chains (1,000 particles each). Particles are connected by Hookean springs, subject to random Gaussian thermal kicks, and advected by a macroscopic harmonic swirl field using vectorized NumPy physics with sub-stepping. Rendered with multi-pass additive point rendering using `py5.points` with a "Cyan to Magenta" HSB palette against a motion-blurred dark background. 15s 4K/60fps MP4.
- **Description**: A mesmerizing microscopic view; 150 glowing, fluorescent neon threads twist, tangle, and breathe in a dark fluid, driven by invisible thermal noise and slow swirling currents, resembling DNA or polymers in a microfluidic channel.

## chladni_plate_resonance

- **Date**: 2026-05-17
- **Theme**: A brass plate vibrating at multiple shifting resonant frequencies, causing golden sand particles to dance and gather along the intricate, shifting nodal lines.
- **Technique**: 2D particle simulation (150,000 particles) using the Chladni resonance equation with time-varying modes ($n, m$). Particles are advected along the negative gradient of $|Z|^2$ toward the nodal lines. Rendered with multi-pass additive point rendering using `py5.points()` with an Amber/Gold palette against a dark slate background. 15s 4K/60fps MP4.
- **Description**: A vast, dark plate where hundreds of thousands of golden, glowing sand grains vibrate and dance, organizing into complex, shifting geometric lattices that perfectly visualize the acoustic resonance of the void.

## boid_murmuration_fluid

- **Date**: 2026-05-17
- **Theme**: The breathtaking, emergent intelligence of a massive murmuration flowing and turning like liquid through a turbulent wind at dusk.
- **Technique**: Vectorized hierarchical spatial flocking simulation (Boids) for 30,000 agents, coupled with a multi-octave noise wind field and center of mass attraction. Agents align with local flock leaders and leave fading silken paths rendered directly into the py5 pixel buffer with additive blending. 15s 4K/60fps MP4.
- **Description**: Thousands of tiny sparks sweep across a dark indigo sky, suddenly folding and swooping together into massive, undulating ribbon-like shapes that feel both organic and perfectly synchronized.

## electrodeposition_dendrite_growth

- **Date**: 2026-05-17
- **Theme**: The slow, beautiful electro-chemical growth of silver crystals branching out in a dark fluid under an electric field.
- **Technique**: Vectorized pseudo-Diffusion-Limited Aggregation using a 150,000 particle system with continuous radial drift and random walk. Metallic age-based coloration mapped directly to the py5 P2D 3D ARGB pixel buffer with additive blending for electrolyte glow. 15s 4K/60fps MP4.
- **Description**: A single glowing seed in the center begins to rapidly branch out with intricate, frost-like fractal tendrils of shimmering silver and warm copper against a deep obsidian void, enveloped by an electric blue aura of migrating ions.

## pilot_wave_hydrodynamics

- **Date**: 2026-05-17
- **Theme**: Path memory and wave-particle duality in classical physics. A microscopic droplet bouncing on a vertically vibrating fluid bath generates local standing Faraday wave ripples that serve as its own guiding field. The droplet is deflected by the gradients of its own past waves, creating a self-guided chaotic walk fueled by wave memory.
- **Technique**: Vectorized 2D wave-field superposition (Bessel-like Faraday wave ripples) and agent-based pilot-wave coupling, hybrid rendering (low-resolution grid-based specular shading combined with high-resolution vector overlays), and custom ARGB color packing in NumPy. 15s 4K/60fps MP4.
- **Description**: A spectacular fluid simulation of a vertically vibrating oil bath. Concentric neon turquoise and electric cyan ripples propagate and interfere on a metallic, iridescent fluid surface, while 8 brilliant white-pearl droplets bounce in and out of phase, steered by the invisible slopes of their own past waves and tracing glowing amber-gold path trajectories across the obsidian pool.

## active_nematic_turbulence

- **Date**: 2026-05-17
- **Theme**: The restless, self-sustained dance of active living matter, where microscopic energy sources continuously drive chaotic flows, tearing order apart into wandering topological defects that seek each other in the dark.
- **Technique**: Vectorized active nematodynamics simulation using Q-tensor components ($Q_1 = \cos 2\theta$ and $Q_2 = \sin 2\theta$) and discrete winding numbers, incompressible screened Stokes flow solved via 2D FFT, and 120,000 tracers with HSL-tailored color bins. 15s 4K/60fps MP4.
- **Description**: A stunning, vibrant simulation of active nematodynamics in a deep midnight Prussian blue fluid. Swirling ribbons of electric teal and ocean-blue filaments are swept along by self-sustained Stokes flows, while glowing gold comet-like +1/2 defects and hot pink star-like -1/2 defects are continuously generated, advected, and annihilated, trailing majestic paths of deep amethyst light.

## glitch_strata_v3

- **Date**: 2026-05-17
- **Theme**: Luxury decay, digital archaeology, and high-fidelity corruption.
- **Technique**: Vectorized 2D pixel-buffer corruption using NumPy. Implements dynamic wiggling strata boundaries, horizontal wave tearing, blocky slide shifts, dynamic vertical data spikes, vectorized chromatic aberration (RGB channel splitting), and moving retro analogue scanlines. 10s 4K/60fps MP4.
- **Description**: An elegant, shimmering digital tapestry of obsidian, deep gold, cyber magenta, and royal amethyst decays dynamically over time. Striking horizontal tearing waves and vertical tracking errors slice across the canvas, while high-performance RGB channel splitting adds vibrant chromatic aberration, visualizing a majestic archaeological survey of corrupted luxury memory.

## bioluminescent_shear_tide

- **Date**: 2026-05-17
- **Theme**: The fleeting, brilliant glow of microscopic organisms in a midnight tide pool, triggered by the mechanical stress of shifting currents and breaking waves.
- **Technique**: 2D fluid-shear advection with a multi-harmonic velocity field. A bioluminescent buffer excites based on local shear stress, modulating the alpha and color of 120,000 tracers. 12s 4K/60fps MP4.
- **Description**: A stunning fluid simulation of a tide pool at midnight. Shimmering ribbons of electric emerald and cyan light are swept along by invisible currents, glowing with intense brilliance as shear forces excite the simulated microorganisms, leaving delicate, fading trails of foam-white and deep teal in the dark water.

## quantum_zeno_decoherence

- **Date**: 2026-05-16
- **Theme**: The freezing effect of constant observation vs. the violent eruption of decoherence.
- **Technique**: Stochastic state-switching simulation with periodic grid projections, vectorized particle fragmentation, and direct pixel-buffer horizontal shredding. 15s 4K/60fps MP4.
- **Description**: A shimmering amethyst quantum sphere is caged by sharp white-gold observation grids; when the gaze wavers, the sphere shatters into spectral fragments and digital glitch artifacts, visualizing the tension between quantum stability and chaotic decoherence.

## axion_domain_walls
- **Theme**: Domain walls in an axion insulator.
- **Technique**: 3D time-varying scalar field simulation, gradient-descent particle trapping on isosurfaces, and 3D additive rendering. 10s 4K/60fps MP4.
- **Description**: Ethereal sheets of chrome and oxide light ripple and intersect in a dark void, as particles clump and flow along the topological domain walls.

## topological_edge_currents

- **Date**: 2026-05-16
- **Theme**: Protected edge states in a topological insulator.
- **Technique**: Lattice-based boundary flow simulation, vectorized particle advection, and multi-pass additive rendering. 10s 4K/60fps MP4.
- **Description**: Glowing emerald currents weave through a dark cobalt lattice, flowing perfectly around internal voids and jagged boundaries without dissipation.

## superfluid_kelvin_waves

- **Date**: 2026-05-16
- **Theme**: Kelvin waves on quantized vortices in a superfluid.
- **Technique**: 3D vortex filament model with helical wave perturbations, vectorized tracer advection, and multi-pass additive rendering. 10s 4K/60fps MP4.
- **Description**: Glowing helical filaments in ultra violet and silver, vibrating with quantum Kelvin waves as they rotate and interact.

## bec_interference_fringes

- **Date**: 2026-05-16
- **Theme**: Bose-Einstein Condensate (BEC) interference and vortex formation.
- **Technique**: Vectorized interference field simulation with expanding wave packets, density-mapped particle dynamics, and multi-pass additive rendering. 10s 4K/60fps MP4.
- **Description**: Expanding concentric fringes of quantum density that collide to create intricate moiré lattices in neon aqua and pulse red.

## fermi_surface_topology

- **Date**: 2026-05-16
- **Theme**: Fermi Surface momentum-space geometry.
- **Technique**: Vectorized 3D scalar field for Fermi surface approximation with particle advection constrained to the energy manifold and tight-binding mapping. 10s 4K/60fps MP4.
- **Description**: A shimmering, complex manifold of momentum states in electric cobalt and solar gold, illustrating the topological structure of electron energy in a crystal lattice.

## quantum_spin_liquid_entanglement

- **Date**: 2026-05-16
- **Theme**: Quantum Spin Liquids (QSLs) and Resonating Valence Bonds (RVB).
- **Technique**: Vectorized triangular lattice spin system with stochastic dimer-swapping (RVB) dynamics and tracer-based entanglement trails. 10s 4K/60fps MP4.
- **Description**: A fluid, shimmering web of entangled spin-dimers in deep amethyst and electric lime, illustrating the resonating nature of quantum spin liquids.

## cholesteric_blue_phase_resonance

- **Date**: 2026-05-16
- **Theme**: Cholesteric liquid crystal "Blue Phases" (BPI/BPII).
- **Technique**: Vectorized 3D director field approximation with cubic symmetry, particle advection, and iridescent selective reflection mapping. 10s 4K/60fps MP4.
- **Description**: A shimmering 3D lattice of double-twist light cylinders in electric cyan and royal violet, revealing the complex topological structure of highly chiral liquid crystals.

## eutectic_alloy_solidification

- **Date**: 2026-05-13
- **Theme**: A cooling alloy remembering pressure and impurity as pale eutectic lamellae freeze through a dark molten film.
- **Technique**: Vectorized phase-front solidification animation on a 960x540 grid, using anisotropic cooling fronts, oscillatory eutectic lamella masks, dendritic tip highlights, grain-boundary fields, solute-rejection memory, and direct py5 pixel-buffer rendering. 10s 4K/60fps MP4 generated as `output.mp4`.
- **Description**: Silver and pewter freezing fronts advance through an iron-blue melt, splitting into alternating lamellae while copper-rich impurity veins stay behind as a persistent memory of the solidification path.

## electrowetting_lens_array

- **Date**: 2026-05-13
- **Theme**: Tiny droplets on conductive glass flattening under voltage pulses and bending light like adjustable micro-lenses.
- **Technique**: Vectorized electrowetting lens-field animation on a 960x540 grid, using pulsed elliptical droplet masks, rim highlights, caustic interference bands, electrode traces, voltage-memory glow, and direct py5 pixel-buffer rendering. 10s 4K/60fps MP4 generated as `output.mp4`.
- **Description**: A dark graphite slide holds an array of aquamarine droplets that breathe flatter and taller as voltage sweeps across them; silver rims and amber electrode memories reveal the hidden electrical control behind the shifting optical caustics.

## belousov_zhabotinsky_spirals

- **Date**: 2026-05-13
- **Theme**: Oscillating chemical reactions forming self-sustaining spiral waves in a dark laboratory medium.
- **Technique**: Vectorized Barkley-model Belousov-Zhabotinsky excitable medium simulation on a 768x432 grid, using activator/inhibitor dynamics, periodic Laplacian diffusion, counter-rotating spiral pacemakers, LANCZOS upscaling, and warm reaction-front palette mapping. 20s 4K/60fps MP4.
- **Description**: Crimson and amber chemical wavefronts curl into rotating spiral cores over near-black reagent, spreading ivory-hot excitation bands that make the surface feel like a living reaction vessel.

## magnetotactic_compass_swarm

- **Date**: 2026-05-13
- **Theme**: Magnetotactic bacteria quietly reorienting as an invisible magnetic field turns through a microscope slide.
- **Technique**: Vectorized 2D bacterial swarm simulation with rotating-field alignment, local oxygen-driven wobble, rod-shaped density deposition, magnetite core darkening, field-line memory, and persistent trails rendered directly through the py5 pixel buffer. 10s 4K/60fps MP4.
- **Description**: Thousands of teal microbial rods drift over an olive-black slide, then slowly swing into a shared direction as faint pearl field lines pass through them; amber tips and dark magnetite cores make the swarm feel alive, precise, and quietly compelled.

## brine_frost_channel_memory

- **Date**: 2026-05-13
- **Theme**: Sea ice forming under quiet pressure, with trapped brine veins opening and remembering old fracture paths.
- **Technique**: Vectorized 2D phase-field frost growth with animated anisotropic channel fields, edge/freezing nuclei, dendritic crystal texture, brine darkening, and persistent salt-memory highlights rendered directly through the py5 pixel buffer. 10s 4K/60fps MP4.
- **Description**: A cold mineral surface freezes inward in porcelain-blue sheets while dark brine veins creep through it; amber salt traces flicker along old cracks, giving the ice a memory of pressure and retreat.

## soliton_resonance_void

- **Date**: 2026-05-13
- **Theme**: Nonlinear Schrödinger Equation (NLSE), solitons, breather modes, wave interference.
- **Technique**: 2D NLSE simulation on a 256x256 grid using the Split-Step Fourier Method. Visualizes the evolution and collision of multiple localized wave packets (solitons) in a focusing nonlinear medium. 15s 4K/60fps MP4.
- **Description**: A dark, tranquil pool of violet energy where bright, localized pulses of rose and gold light emerge, collide, and pass through each other with intense, flickering resonance, demonstrating the unique stability and interaction of solitons.

## acoustic_levitation_drift

- **Date**: 2026-05-13
- **Theme**: Acoustic levitation, Gorkov potential, standing wave resonance, particle trapping.
- **Technique**: 3D Gorkov potential simulation. Particles are trapped in the nodes of a 3D standing wave field. The phase of the standing wave is slowly modulated, causing the trapped "beads" of light to drift and reorganize. 15s 4K/60fps MP4.
- **Description**: A dark void where thousands of silver and cyan specks are suspended in an invisible, vibrating grid. The grid slowly shifts and warps, carrying the specks in a rhythmic, coordinated dance that reveals the hidden geometry of sound.

## wigner_crystal_melting

- **Date**: 2026-05-13
- **Theme**: Quantum phase transition, Wigner crystallization, melting, Coulomb repulsion, collective dynamics.
- **Technique**: 2D particle simulation with $1/r$ repulsive forces and a harmonic trap. Brownian dynamics with time-varying temperature. Vectorized NumPy physics. 20s 4K/60fps MP4.
- **Description**: A rigid, shimmering hexagonal lattice of blue-white stars that slowly vibrates, develops defects, and eventually melts into a chaotic, swirling sea of violet and cyan light as the quantum temperature rises.

## spinodal_decomposition_nebula

- **Date**: 2026-05-13
- **Theme**: The spontaneous separation of two primordial fluids as the universe cools, creating a vast, intricate web of matter and void.
- **Technique**: Cahn-Hilliard equation simulation on a 256x256 grid, scaled to 4K using LANCZOS. Visualizes phase separation (spinodal decomposition) with a spectral mapping from obsidian to solar white. 15s 4K/60fps MP4.
- **Description**: A shimmering, uniform mist of purple and cyan slowly curdles and separates into a majestic, glowing sponge-like network of light threads, leaving vast dark voids in between.

## quantum_chaos_billiard

- **Date**: 2026-05-12
- **Theme**: Quantum mechanics, chaos theory, stadium billiard, wavefunctions, quantum scarring, wave-particle duality.
- **Technique**: 2D wave equation simulation in a stadium geometry. High-density volumetric point rendering to visualize probability density. 15s 4K/60fps MP4 (1080p source).
- **Description**: Visualizes the emergence of quantum scars in a chaotic stadium billiard, where the wavefunction concentrates along classical periodic orbits.

## topological_spin_ice

- **Date**: 2026-05-12
- **Theme**: Condensed matter, spin ice, magnetic monopoles, frustrated magnets, emergent phenomena.
- **Technique**: Discrete lattice simulation with stochastic monopole dynamics. Vectorized coordinate mapping for high-performance lattice rendering. 15s 4K/60fps MP4 (1080p source).
- **Description**: Visualizes the emergence and motion of magnetic monopoles in a frustrated spin ice lattice.

## topological_defect_string

- **Date**: 2026-05-12
- **Theme**: Cosmology, early universe, symmetry breaking, cosmic strings, topological defects, phase transition.
- **Technique**: 2D complex scalar field simulation (Ginzburg-Landau type) with Mexican hat symmetry breaking. High-density point rendering of defect cores. 10s 4K/60fps MP4 (1080p source).
- **Description**: Visualizes the emergence of cosmic strings from a primordial gold field as the universe undergoes a symmetry-breaking phase transition.

## dark_matter_halo_cusp

- **Date**: 2026-05-12
- **Theme**: Astrophysics, dark matter, N-body simulation, NFW profile, gravitational collapse.
- **Technique**: 3D N-body simulation (140,000 particles) with NFW potential modeling. Multi-pass additive rendering. 20s 4K/60fps MP4 (1080p source).
- **Description**: A diffuse cloud of Spectral Indigo particles collapses into a dense, bright central cusp, visualizing the formation of a dark matter halo.

## gravitational_wave_chirp

- **Date**: 2026-05-12
- **Theme**: General relativity, binary black hole merger, gravitational waves, space-time ripples.
- **Technique**: 3D particle simulation (80,000 particles) distorted by a metric perturbation field. Chirp frequency/amplitude scaling and ringdown logic. Multi-pass additive rendering. 15s 4K/60fps MP4 (1080p source).
- **Description**: Two binary black holes spiral and merge, triggering a titanic chirp of space-time ripples that radiate as concentric waves of Deep Violet and Electric Gold.

## neutrino_flavor_oscillation

- **Date**: 2026-05-12
- **Theme**: Particle physics, neutrinos, flavor oscillation, PMNS matrix, quantum interference.
- **Technique**: 3D particle advection (120,000 particles) along a helical beam. Color oscillations between three HSB bands. Multi-pass additive rendering. 15s 4K/60fps MP4 (1080p source).
- **Description**: A beam of ghostly light oscillates between three distinct flavors—Cyan, Magenta, and Gold—representing the Electron, Muon, and Tau neutrino states in transit.

## rydberg_blockade_array

- **Date**: 2026-05-12
- **Theme**: Quantum computing, Rydberg atoms, dipole blockade, collective excitations.
- **Technique**: 3D grid simulation. Greedy blockade logic based on a wave potential. Multi-pass additive rendering with glowing shells (sphere geometry). 12s 4K/60fps MP4 (1080p source).
- **Description**: A precise 3D grid of neutral atoms, where laser excitations trigger blinding Neon Orange glows and translucent blockade shells that prevent neighboring atoms from being excited.

## supersolid_lattice_vibration

- **Date**: 2026-05-12
- **Theme**: Quantum matter, supersolids, spontaneous translational symmetry breaking, phonon-roton modes.
- **Technique**: 3D lattice simulation (100,000 particles). Lattice vibrations modeled as coupled oscillators or wave propagation. Multi-pass additive rendering with HSB spectral shifts. 15s 4K/60fps MP4 (1080p source).
- **Description**: A crystal-like 3D lattice of crystalline droplets shimmers in a cold vacuum, pulsing and vibrating with roton-like excitations in a coordinated wave-like dance.

## dirac_fluid_turbulence

- **Date**: 2026-05-12
- **Theme**: Dirac fluids, electron hydrodynamics, graphene physics, relativistic turbulence.
- **Technique**: 2D particle advection on a velocity field (80,000 particles). Velocity field generated by a von Kármán vortex street model. Multi-pass additive rendering. 14s 4K/60fps MP4 (1080p source).
- **Description**: A shimmering flow of plasma-like light surges through a channel, breaking into a majestic von Kármán vortex street of glowing eddies as it encounters a circular obstacle.

## anderson_localization_mesh

- **Date**: 2026-05-12
- **Theme**: Quantum physics, Anderson localization, disordered systems, metal-insulator transition.
- **Technique**: 3D grid simulation (150,000 particles). Grid nodes are randomly perturbed. A "localization" function (exponential falloff) determines particle density. Manual 3D-to-2D projection. 15s 4K/60fps MP4 (1080p source).
- **Description**: A vast, distorted 3D grid of silver threads floats in the dark, housing a blindingly bright, spherical concentration of electric blue and amethyst particles that represent a localized quantum wavefunction.

## weyl_semimetal_fermi_arcs

- **Date**: 2026-05-12
- **Theme**: Topological matter, Weyl semimetals, Fermi arcs, chiral Weyl nodes, momentum-space topology.
- **Technique**: 3D particle simulation (120,000 tracers). Two centers of attraction/repulsion representing Weyl nodes. Particles follow "Fermi arc" trajectories—semicircular or elliptic paths on a surface in momentum space. Multi-pass additive rendering with P3D projection. 20s 4K/60fps MP4 (1080p source).
- **Description**: Two blindingly bright Weyl nodes float in an obsidian momentum-space void, connected by a shimmering, pulsing shell of iridescent Fermi arcs in cyan and magenta.

## benard_marangoni_convection

- **Date**: 2026-05-11
- **Theme**: Fluid dynamics, surface tension, Bénard-Marangoni convection, self-organization.
- **Technique**: 2D particle simulation of surface-driven flow. Tracers follow a velocity field derived from surface tension gradients. Features multi-pass additive rendering with a "Deep Violet / Indigo / Silver" palette. 20s 4K/60fps MP4.
- **Description**: A shimmering surface organizes into silver-rimmed hexagonal cells, visualizing the spontaneous order of surface-tension driven convection.

## kerr_effect_filamentation

- **Date**: 2026-05-11
- **Theme**: Non-linear optics, Kerr effect, self-focusing, laser filamentation, spatial solitons.
- **Technique**: 2D particle simulation of laser filamentation. Tracers are advected by the gradient of an intensity field governed by non-linear self-focusing dynamics. Features multi-pass additive rendering with a "Deep Emerald / Neon Lime / Prism White" palette. 20s 4K/60fps MP4.
- **Description**: A central beam of emerald light breaks into brilliant filaments, creating a high-energy crystalline structure through non-linear self-focusing.

## rayleigh_benard_convection_cells

- **Date**: 2026-05-11
- **Theme**: Fluid dynamics, thermodynamics, thermal convection, Rayleigh-Bénard instability, self-organization.
- **Technique**: 2D particle advection simulation. Tracers are guided by a dynamic velocity field derived from a hexagonal convection roll model. Features multi-pass additive rendering with a "Molten Copper / Solar Amber / Obsidian" palette. 20s 4K/60fps MP4.
- **Description**: A dark, viscous surface boils with organized cells of molten copper and golden light, revealing the elegant self-organization of a heated fluid.

## gravitational_wave_chirp_merger

- **Date**: 2026-05-11
- **Theme**: General Relativity, gravitational waves, binary black hole merger, spacetime distortion, the "chirp" signal.
- **Technique**: 3D particle grid simulation representing the fabric of spacetime. Two orbiting gravitational centers (masses) warp the surrounding geometry, creating rotating spiral ripples. Employs a non-linear "chirp" progression and manual 3D-to-2D projection. 15s 4K/60fps MP4.
- **Description**: Two blindingly bright singularities dance in a tightening spiral, sending violent, rhythmic ripples of indigo and cyan through the fabric of spacetime before a final cataclysmic merger.

## asymptotic_giant_branch_pulsation

- **Date**: 2026-05-11
- **Theme**: Stellar evolution, AGB stars, thermal pulses, planetary nebula precursor, stardust.
- **Technique**: 3D shell ejection simulation. A central core undergoes periodic pulses every 180 frames, triggering the expansion of nested, concentric shells of 15,000 tracers each (up to 150,000 total). 20s 4K/60fps MP4.
- **Description**: Concentric, shimmering shells of stardust expand slowly from a pulsing stellar core, creating a delicate, layered cocoon of rose and orange light.

## magnetohydrodynamic_z_pinch_instability

- **Date**: 2026-05-11
- **Theme**: Fusion energy, plasma physics, Z-pinch confinement, sausage and kink instabilities, magnetohydrodynamics (MHD).
- **Technique**: 3D magnetic field simulation of a central current column. Implements harmonic deformations corresponding to sausage (radial) and kink (helical) instability modes. 100,000 tracers. 10s 4K/60fps MP4.
- **Description**: A vertical column of intense light starts in a stable cylindrical configuration but quickly succumbs to the violent forces of electromagnetism, deforming into chaotic kinks and sausages.

## supernova_nucleosynthesis_nebula

- **Date**: 2026-05-11
- **Theme**: Stellar evolution, supernova explosions, heavy element creation, nuclear physics, beautiful night sky.
- **Technique**: 3D blast wave simulation using an expanding shell of 80,000 particles with stochastic cooling and turbulence. Rendered with manual 3D-to-2D projection, multi-pass additive blending, and a "Deep Gold / Neon Violet / Star-White" palette. 15s 4K/60fps MP4.
- **Description**: A violent yet majestic expansion; a central core collapses and rebounds, sending a shimmering, variegated nebula of precious metals and stardust into the cosmic dark.

## cosmic_ray_cascade_resonance

- **Date**: 2026-05-11
- **Theme**: High-energy astrophysics, cosmic ray air showers, particle physics, beautiful night sky.
- **Technique**: 3D particle cascade simulation (Heitler model). A primary high-energy particle triggers a stochastic branching process, spawning secondaries (pions, muons, electrons) in a narrow relativistic cone. Features 50,000 spectral particles at the shower peak. Rendered with manual 3D-to-2D projection, multi-pass additive blending, and a "Blinding White / Electric Cyan / Deep Amethyst" palette. 10s 4K/60fps MP4.
- **Description**: A majestic eruption of light; a single streak from the top of the frame shatters into a vast, shimmering cone of spectral particles that illuminate the obsidian void like a fleeting ghost.

## nematic_liquid_crystal_disclinations

- **Date**: 2026-05-11
- **Theme**: Liquid crystals, topological defects, disclination lines, soft matter physics, beautiful night sky.
- **Technique**: 3D tensor field simulation (simplified director field) where orientation is influenced by moving defect centers (vortices). Features 40,000 tracers advected along the director field. Rendered with manual 3D-to-2D projection, multi-pass additive blending, and a "Spectral Blue / Pearl / Ionized Amethyst" palette. 15s 4K/60fps MP4.
- **Description**: Silken filaments of pearl and blue light weave through the obsidian void, revealing the tangled topological defects of a liquid crystal phase as it relaxes toward equilibrium.

## dielectric_breakdown_resonance

- **Date**: 2026-05-11
- **Theme**: Plasma physics, Lichtenberg figures, dielectric breakdown, high-voltage discharge, beautiful night sky.
- **Technique**: 3D stochastic branch-growth simulation (DLA-variant) where "streamers" propagate along the gradient of a dynamic field. Features 30,000 spectral particles advected by the local discharge current and turbulence. Rendered with manual 3D-to-2D projection, multi-pass additive blending, and a "Blinding White / Electric Cyan / Deep Amethyst" palette. 8s 4K/60fps MP4.
- **Description**: A majestic, high-energy visualization of cosmic lightning; razor-sharp branches of electric cyan and white energy strike out into the obsidian void, shattering into a shimmering haze of amethyst particles as the dielectric strength of the vacuum fails.

## soap_film_thickness_flow

- **Date**: 2026-05-10
- **Theme**: draining soap film where nanoscale thickness changes become moving interference colors and pale bubble rims
- **Technique**: Procedural thin-film thickness field driven by vertical drainage, shear waves, circular bubble boundaries, and dry black-film memory. Spectral cosine interference maps thickness to saturated green, blue, violet, and magenta bands, with bright pearl rim highlights and slow rupture shadows rendered directly through the py5 pixel buffer. 10s 4K/60fps MP4, generated as `output.mp4` and mirrored to `soap_film_thickness_flow.mp4`.
- **Description**: Large bright arcs cut through a flowing field of iridescent color bands, suggesting a fragile soap membrane draining, thinning, and remembering near-rupture zones.

## chromatophore_signal_skin

- **Date**: 2026-05-10
- **Theme**: cephalopod-like skin where chromatophore cells expand and contract under traveling neural signals
- **Technique**: Procedural staggered cell lattice with vectorized radial pigment masks, ring highlights, iridescent inner bands, and a fading signal-memory buffer. Multi-wave neural activation modulates chromatophore expansion across the skin while pale signal paths drift through warm umber and coral tissue. 10s 4K/60fps MP4, generated as `output.mp4` and mirrored to `chromatophore_signal_skin.mp4`.
- **Description**: A living field of coral pigment cells pulses over dark skin while pale nerve-wave ribbons pass through it, making the surface feel like a responsive cephalopod display.

## triboelectric_pollen_cloud

- **Date**: 2026-05-10
- **Theme**: charged pollen grains suspended in a dim air column, pulled by invisible static-electric fields
- **Technique**: Procedural electrostatic-potential animation with moving positive and negative charge centers. Vectorized field-line synthesis maps potential phase and field magnitude into blue-violet corona arcs, while ring-shaped pollen shells and a fading charge-memory buffer create warm golden grains and residual ion trails. 10s 4K/60fps MP4, generated as `output.mp4` and mirrored to `triboelectric_pollen_cloud.mp4`.
- **Description**: Golden pollen rings drift through a smoky blue-violet chamber as static field lines curl and snap around them, leaving faint electric traces like charged dust suspended in quiet air.

## metachronal_cilia_field

- **Date**: 2026-05-10
- **Theme**: microscopic cilia moving in coordinated metachronal waves across a dim biological membrane
- **Technique**: Procedural 2D phase-field animation of cilia beat timing and recovery. Vectorized comb-ridge synthesis creates thousands of short filament strokes without per-stroke drawing; local shear accumulates into a fading flow-memory buffer, with cyan/pearl metachronal bands and subtle coral afterimages rendered directly through the py5 pixel buffer. 10s 4K/60fps MP4, generated as `output.mp4` and mirrored to `metachronal_cilia_field.mp4`.
- **Description**: Diagonal bands of tiny luminous cilia sweep across a dark teal membrane, producing coordinated pearl-and-cyan waves with faint coral traces that read like an organism moving fluid through microscopic rhythm.

## capillary_bridge_rupture

- **Date**: 2026-05-10
- **Theme**: microscopic droplets forming unstable liquid bridges, stretching under surface tension, and rupturing into faint residue
- **Technique**: 2D metaball droplet field with animated centers and radii. Near-neighbor segment-distance fields synthesize capillary bridges; a time-varying waist term thins the bridge necks until rupture, accumulating amber residue in a fading buffer. Direct NumPy-to-py5 pixel rendering with FFmpeg output as `output.mp4` and `capillary_bridge_rupture.mp4`. 10s 4K/60fps MP4.
- **Description**: Translucent green-blue droplets cling to a dark brushed substrate while thin liquid bridges stretch between them; small amber flashes mark rupture points and leave ghostly residue rings in the fluid network.

## ferroelastic_domain_drift

- **Date**: 2026-05-10
- **Theme**: polarized ferroelastic domains slowly drifting, locking, and leaving luminous boundary memories
- **Technique**: Continuous 2D phase-field relaxation with pinning noise, slow external bias, and domain-wall memory extracted from field gradients. A rotating analyzer term maps domain orientation into restrained teal and violet polarization colors, while moving boundaries accumulate amber highlights. Direct NumPy-to-py5 pixel rendering. 10s 4K/60fps MP4.
- **Description**: Large teal and violet material domains slide under a dark polarizing field; their borders glow with thin amber light, creating a quiet microscopic view of crystal variants shifting and locking into place.

## seismic_lithograph

- **Date**: 2026-05-10
- **Theme**: low seismic pulses traveling through an etched stone slab, revealing hidden layers and quiet fault heat
- **Technique**: 2D finite-difference wave field on a layer-dependent stiffness map. Stratified shale bands are synthesized as a lithographic base texture; diagonal fault masks add nonlinear slip and localized heat memory. Signed wave height, accumulated strain, and fault heat are mapped to slate, ash, sulfur, and rust tones through direct py5 pixel-buffer rendering. 10s 4K/60fps MP4.
- **Description**: A dark mineral surface where slow pressure waves cross layered stone, briefly exposing pale stress contours and rust-colored fault scars before the slab returns to a quiet, smoky lithographic texture.

## archival_vein_memory

- **Date**: 2026-05-10
- **Theme**: archival paper remembering water damage, oxidized ink veins, quiet material decay
- **Technique**: 2D anisotropic particle advection through a paper-fiber vector field. 65,000 particles deposit into low-resolution ink and oxide density buffers, which diffuse with restrained decay and are upscaled into the py5 pixel buffer. Fold-line crease masks bias the flow and tint oxidized regions with muted verdigris and copper edge highlights. 10s 4K/60fps MP4.
- **Description**: A warm parchment field where green-black stains slowly crawl along invisible fibers and old fold lines, forming soft archival veins with faint copper-rimmed edges and a quiet sense of paper remembering moisture.

## prismatic_recursive_glass

- **Date**: 2026-05-10
- **Theme**: Optical physics, high-tech urbanism, chromatic dispersion on a massive recursive glass structure.
- **Technique**: 3D recursive structure (fractal depth 4) rendered with a translucent shader-like effect in Py5. Using P3D, massive transparent monolithic slabs rotate and unfold dynamically. Chromatic aberration is faked by drawing the structure three times (R, G, B) with slight rotational offsets and additive blending.
- **Description**: A towering, intricate fractal crystal floats in the void. As it unfolds, its edges split the light into brilliant holographic rainbows, creating an awe-inspiring sense of scale and digital purity against a star-dusted night.

## color_flux_string_breaking

- **Date**: 2026-05-10
- **Theme**: Quantum Chromodynamics (QCD), string breaking, quark confinement, beautiful night sky.
- **Technique**: 3D particle simulation of strong force confinement. 30,000 quarks (particles) connected by "color flux tubes". As they drift apart due to high-energy scattering, the tension increases until it "snaps", spawning new quark-antiquark pairs. Rendered with additive blending, using RGB (Red, Green, Blue) and their anti-colors as the literal "color charge".
- **Description**: A dense, chaotic web of intense RGB threads that constantly stretch and snap with blinding white flashes, weaving an ever-expanding, intricate quantum tapestry that illustrates the inescapable confinement of quarks.

## chiral_turing_morphogenesis

- **Date**: 2026-05-13
- **Theme**: Organic morphogenesis driven by chiral chemical reactions, creating twisting, breathing labyrinths of light.
- **Technique**: Vectorized 2D Gray-Scott Reaction-Diffusion model on a 512x512 grid with a chiral advection term (asymmetric laplacian) and LANCZOS scaling to 4K. Rendered with a Midnight Indigo / Emerald / Amethyst palette. 15s 4K/60fps MP4.
- **Description**: A dark, viscous surface erupts with glowing, spiraling green and violet labyrinths that twist and consume each other like a living digital organism.

## monsoon_resonance

- **Date**: 2026-05-10
- **Theme**: still pond at midnight, summer monsoon raindrops, wave interference, meditative naturalism
- **Technique**: 2D scalar wave equation propagated by 5-point FDTD on a 480×270 grid (`u_next = (2u − u_prev + c²·∇²u) · damping`); raindrops injected as Mexican-hat (Laplacian-of-Gaussian) impulses to seed multiple concentric bands; soft border absorber prevents boxy reflections; signed-height shading (positive → cyan/pearl, negative → indigo shadow) plus subtle slope rim. Vectorized NumPy and direct ARGB pixel writes via `py5.np_pixels`. 18s 4K/60fps MP4.
- **Description**: A still dark pond surface where occasional silver droplets fall and bloom into expanding rings of moonlight; the rings interfere into a hypnotic shimmer of cyan and pearl bands against deep indigo, with a soft moonlight gradient and a single distant amber lamp at the far shore.

## lsystem_tree_v2
## axion_string_conversion

- **Date**: 2026-05-10
- **Theme**: Cosmic strings, axion-photon conversion, Primakoff effect, high-energy physics, beautiful night sky
- **Technique**: 3D polyline simulation of vibrating cosmic strings; emission of 160,000 spectral particles advected by magnetic drift. Features smooth curve rendering and multi-pass additive point rendering. Palette: "Stark White / Electric Cyan / Deep Amethyst / Ionized Magenta" HSB mapping. 15s 4K/60fps MP4.
- **Description**: A high-energy visualization of cosmic string dynamics; razor-sharp luminous threads pulse and snap in the obsidian void, emitting spectral clouds of cyan, violet, and magenta photons.

## superfluid_helicity_resonance

- **Date**: 2026-05-10
- **Theme**: Superfluidity, vortex helicity, Kelvin waves, quantum turbulence, beautiful night sky
- **Technique**: 3D particle simulation (240,000 tracers) advected by helical harmonic perturbations (Kelvin waves) along three interacting vortex rings. Features manual 3D-to-2D projection with multi-pass additive point rendering for a soft "ghostly" glow. Palette: "Electric Ice / Ghostly Amethyst / Deep Cobalt" HSB mapping. 20s 4K/60fps MP4.
- **Description**: A majestic visualization of quantum fluid dynamics; silken filaments of electric ice and ghostly amethyst light weave and twist in a helical resonance, tracing the hidden paths of superfluid vortex rings as they dance against the star-dusted obsidian void.

## mhd_kelvin_helmholtz_waves

- **Date**: 2026-05-10
- **Theme**: plasma dynamics, magnetohydrodynamics, fluid billows, beautiful night sky
- **Technique**: Vectorized 2D/3D particle advection (NumPy). Implements a magnetized shear layer simulation with a magnetic tension proxy resisting vertical displacement ($v_y \leftarrow v_y - \beta y$). Features a 60,000-particle system with persistence-based motion blur and additive blending in P2D. Palette: "Deep Amethyst / Luminous Teal / Molten Gold" with initial position-based color mapping. High-fidelity 4K rendering.
- **Description**: A majestic visualization of the Kelvin-Helmholtz instability in a magnetized cosmic fluid. Luminous filaments of teal and gold roll and billow into intricate spirals against a deep amethyst void, captured as they trace the invisible magnetic lines that attempt to bind them.


- **Date**: 2026-05-10
- **Theme**: bioluminescent nature, L-system fidelity, fractal growth, beautiful night sky
- **Technique**: Stochastic L-system with multi-segment curved branch subdivision. Implements bioluminescent leaf clustering at terminals using additive blending (`py5.ADD`) and a depth-based thickness taper ($sw \propto (1-t)^{2.5}$). Features a vectorized night sky gradient with integrated starfield and dynamic firefly accents. Palette: "Charcoal / Aged Wood / Luminous Teal / Molten Gold".
- **Description**: A majestic vision of cosmic biological emergence; a complex, organic tree with curved, silken branches rises against a star-dusted obsidian sky. Bioluminescent teal leaves pulse with a rhythmic internal light, while tiny fireflies of molten gold dance in the surrounding void, bridging the gap between natural phenomena and celestial wonder.


## voronoi_cells_v2

- **Date**: 2026-05-10
- **Theme**: abstract quantum cells, ethereal boundaries, fluid geometry, beautiful night sky
- **Technique**: Vectorized 2D pixel-buffer manipulation (NumPy). Implements a noise-warped Voronoi tessellation where pixel coordinates are perturbed by multi-harmonic sine/cosine fields before distance calculation. Features a soft-glow boundary rendering using an exponential falloff based on the second-order distance (d2-d1). Palette: "Deep Amethyst / Luminous Teal / Molten Gold" with stochastic cell-wise color modulation. High-resolution P2D rendering.
- **Description**: A majestic and ethereal visualization of cellular structure in a quantum field. Shimmering, fluid boundaries in luminous teal weave through a deep amethyst void, occasionally erupting into brilliant sparks of molten gold where the energy of the vacuum is concentrated.


## glitch_strata_v2

- **Date**: 2026-05-10
- **Theme**: luxury decay, obsidian & gold, digital archaeology, high-fidelity corruption, beautiful night sky
- **Technique**: Vectorized 2D pixel-buffer manipulation (NumPy). Implements recursive stratification with three distinct corruption styles: (1) noisy gradients with horizontal tear displacement, (2) digital block corruption with stochastic color injection, and (3) high-frequency jitter-shredding. Palette: "Obsidian / Deep Gold / Pale Amber / Steel" with refined noise-to-signal ratios and scanline synthesis. High-resolution P2D rendering.
- **Description**: A majestic, high-fidelity refinement of the `glitch_strata` concept; a vertical cross-section of luxury data-memory is rendered as an elegant, shimmering tapestry of obsidian, deep gold, and pale amber. Intricate horizontal displacement mapping and block corruption patterns create a sense of structured digital archaeology, revealing the hidden beauty of corrupted information against a silent, star-dusted night.


## rayleigh_taylor_plumes

- **Date**: 2026-05-10
- **Theme**: Fluid dynamics, Rayleigh-Taylor instability, buoyancy-driven mixing, beautiful night sky
- **Technique**: 3D particle simulation (100,000 particles) advected by a vectorized buoyant force field and 16 dynamic plume centers. Implements the growth of "mushrooms" and "spikes" through a dual-fluid interface. Features manual 3D-to-2D projection for performance and stability. Palette: "Incandescent Orange / Electric Azure / Deep Amethyst" with additive blending. 60fps high-bitrate 4K MP4.
- **Description**: A majestic visualization of two cosmic fluids mixing under gravity. Heavy, glowing plumes of molten orange sink into a deep blue sea, while silken azure filaments rise in response, creating a complex, shimmering interface of light and shadow reminiscent of a nocturnal atmospheric event.

## pulsar_magnetosphere_flux

- **Date**: 2026-05-10
- **Theme**: Pulsar magnetosphere, rotating dipole, magnetic field lines, relativistic wind, beautiful night sky
- **Technique**: 3D physics-based simulation of 60,000 particle tracers advected by a rotating magnetic dipole field. Implements the "twist" of magnetic field lines near the light cylinder and the transition to a radial relativistic pulsar wind. Features manual 3D-to-2D projection for performance and stability. Palette: "Cyan / Electric Blue / Royal Purple" HSB mapping with additive blending. 60fps high-bitrate 4K MP4.
- **Description**: A majestic visualization of a pulsar's invisible power; silken filaments of electric cyan and royal purple light are twisted into complex, shimmering braids by the star's rapid rotation. As they reach the light cylinder, the magnetic ropes snap and surge outward into the deep obsidian night, creating a vast, glowing shroud of relativistic energy.

## moire_lattice_resonance

- **Date**: 2026-05-10
- **Theme**: twisted bilayer graphene, Moiré patterns, electron resonance, quantum physics, beautiful night sky
- **Technique**: 2D particle simulation of 180,000 electron tracers in a dynamic Moiré potential field. Visualizes the interference of two rotating hexagonal lattices. Features multi-pass additive rendering with "Emerald / Cyan / Deep Purple" palette and dynamic twist-angle modulation. 60fps high-bitrate 4K MP4.
- **Description**: A stunning visualization of quantum resonance; nearly 200,000 silken particles are guided by the shimmering interference patterns of two twisted atomic lattices, forming complex, rhythmic arcs of cyan and violet light that pulse and breathe against a deep obsidian void.


## monolayer_buckling_topography

- **Date**: 2026-05-09
- **Theme**: Molecular monolayers, compression, buckling, material science, iridescence
- **Technique**: 3D grid deformation simulation (10,000 quads) using multi-octave noise-driven buckling potentials. Visualizes the structural failure and folding of a thin film under lateral compression. Features iridescent Fresnel shading and specular highlights in P3D. 60fps high-bitrate MP4.
- **Description**: A silken, iridescent silver sheet that "crunches" and wrinkles into a complex, mountainous topography of shimmering light and shadow as it undergoes molecular buckling.

## ginzburg_landau_vortices

- **Date**: 2026-05-09
- **Theme**: Ginzburg-Landau theory, topological defects, vortex-antivortex turbulence, superconductivity
- **Technique**: Time-Dependent Ginzburg-Landau (TDGL) simulation on a 128x128 complex scalar field. Visualizes the phase transition and topological defect dynamics using 40,000 advected particles. Features multi-pass additive rendering with a "Superconducting Gold / Electric Blue" palette. 60fps high-bitrate MP4.
- **Description**: A stunning visualization of a superconducting phase transition; complex filaments of molten gold and electric blue energy swirl and dance as topological vortices collide and annihilate in a shimmering obsidian void.

## quantum_hall_edge_states

- **Date**: 2026-05-09
- **Theme**: Quantum Hall Effect, topological protection, chiral edge states
- **Technique**: 2D particle simulation of 150,000 charge carriers under a strong perpendicular magnetic field. Visualizes the contrast between insulating bulk (cyclotron loops) and conducting edges (unidirectional skipping orbits). Features multi-pass additive rendering with "Cobalt / Electric Lime" palette. 60fps high-bitrate MP4.
- **Description**: A precise and technically stunning visualization of topological protection in a 2D electron gas. Within the deep indigo bulk, particles are trapped in localized cyclotron loops, while along the boundaries, they form a swift, unidirectional current of shimmering electric lime light.

## primordial_polarization_swirl

- **Date**: 2026-05-09
- **Theme**: B-mode polarization, primordial gravitational waves, CMB, beautiful night sky
- **Technique**: 3D simulation of 120,000 particles on a spherical shell advected by a multi-scale "curl" vector field representing tensor perturbations. Features multi-pass additive rendering with HSB spectral mapping and cosmic expansion scaling. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of the early universe's first light; silken swirls of celestial azure and soft gold energy are twisted into intricate B-mode patterns by primordial gravitational waves, shimmering across a deep amethyst void.

## casimir_vacuum_pressure

- **Date**: 2026-05-09
- **Theme**: Casimir effect, quantum vacuum pressure, beautiful night sky
- **Technique**: 3D particle physics simulation of 160,000 virtual particles with life-cycle decay and boundary-based suppression. Oscillating parallel plates with glow effects. Multi-pass additive rendering. "Silver / Electric Cyan / Deep Amethyst" palette. 60fps high-fidelity MP4.
- **Description**: A serene yet powerful visualization of quantum vacuum pressure; shimmering virtual particles emerge and vanish in a cosmic void, noticeably suppressed in the narrow gap between two silver plates, illustrating the silent force of the void itself.

## mhd_accretion_turbulence

- **Date**: 2026-05-09
- **Theme**: MHD turbulence, accretion disks, plasma physics, beautiful night sky
- **Technique**: 3D simulation of 180,000 particles in a Keplerian disk with magnetic tension proxies and MRI-inspired turbulence. Multi-pass additive rendering with kinetic energy color mapping. "Incandescent Orange / Plasma Blue / Obsidian Black" palette. 60fps high-bitrate MP4.
- **Description**: A violent, beautiful visualization of plasma turbulence in a black hole's accretion disk; swirling ropes of orange and blue fire are twisted by invisible magnetic fields, creating a rhythmic, incandescent dance of matter at the edge of the void.

## skyrmion_vortex_lattice

- **Date**: 2026-05-09
- **Theme**: Skyrmions, magnetic topology, spin textures, beautiful night sky
- **Technique**: 3D simulation of 150,000 "spin tracer" particles advected by a lattice of 9 Skyrmion cores. Implements a multi-pole vortex field with topological twisting and core oscillations. Multi-pass additive rendering with an "Emerald Glow / Burnished Gold / Deep Ultraviolet" palette. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of a magnetic Skyrmion lattice; swirling vortices of emerald and gold light wrap around stable topological cores, weaving an intricate web of silken spin textures against the deep violet star-dusted night.

## chromatic_planck_fluctuations

- **Date**: 2026-05-09
- **Theme**: Quantum foam, Planck length, virtual particles, vacuum energy, beautiful night sky
- **Technique**: 3D simulation of 160,000 "virtual particles" with finite lifetimes (birth/annihilation loop). Particles follow a dynamic 3D noise-based field (interpolated 32^3 volume) representing space-time jitter. Multi-pass additive rendering with lifetime-based alpha modulation and an "Ultraviolet / Electric Cyan / Solar Gold" palette. 60fps high-bitrate MP4.
- **Description**: A mesmerizing visualization of the quantum vacuum at the Planck scale; a boiling, iridescent sea of light where spectral sparks of ultraviolet and electric cyan flicker into existence and vanish, revealing the hidden, jittering geometry of space-time against the star-dusted obsidian void.

## cosmic_filament_condensation

- **Date**: 2026-05-09
- **Theme**: Large-scale structure, baryon acoustic oscillations, cosmic web, dark matter halos, beautiful night sky
- **Technique**: 3D simulation of 150,000 particles representing baryonic matter and dark matter tracers. Implements a multi-scale gravitational clustering algorithm towards 12 dynamic "dark matter hubs" using a modified $1/r^{1.2}$ potential. Features global harmonic oscillations (BAO) and multi-pass additive rendering with a "Crystalline White / Deep Cobalt / Ionized Magenta" palette. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of the formation of the Cosmic Web; silken filaments of ionized magenta and deep cobalt light stretch across the void, condensing into brilliant crystalline white clusters driven by the rhythmic pulse of primordial sound waves against the star-dusted night.

## stochastic_resonance_lattice

- **Date**: 2026-05-09
- **Theme**: Stochastic resonance, coupled oscillators, signal-in-noise, lattice dynamics, beautiful night sky
- **Technique**: 3D simulation of 150,000 particles following Langevin dynamics in a double-well potential landscape ($V(x) = -x^2/2 + x^4/4$). Implements nonlinear synchronization driven by Gaussian white noise and a weak periodic forcing signal. Multi-pass additive point rendering with state-dependent coloring ("Electric Cyan / Deep Amethyst / Neon White"). 60fps high-bitrate MP4.
- **Description**: A majestic vision of order emerging from chaos; a shimmering cloud of electric cyan and deep amethyst light pulses with a hidden cosmic rhythm. As the collective oscillators synchronize through the mechanism of stochastic resonance, the noisy void crystallizes into a pulsing geometric lattice of neon white energy against the star-dusted indigo night.

## accretion_disk_instability

- **Date**: 2026-05-09
- **Theme**: Black hole accretion, disk turbulence, Magneto-Rotational Instability (MRI), polar jets, beautiful night sky
- **Technique**: 3D simulation of 180,000 particles following Keplerian rotation dynamics ($v \propto 1/\sqrt{r}$). Implements turbulent noise-driven advection within the disk and high-velocity polar jets with plasma-like jitter. Multi-pass additive point rendering with an "Incandescent Orange / Crimson Red / Ultraviolet Indigo" HSB palette and a subtle high-density starfield. 60fps high-bitrate MP4.
- **Description**: A majestic vision of a star's final descent; silken filaments of incandescent orange and crimson light spiral into the dark heart of a black hole, creating a complex, shimmering disk that pulses with thermal instability. Violent jets of ultraviolet indigo plasma erupt from the poles, tracing the invisible magnetic conduits that channel energy away from the gravitational abyss against the star-dusted obsidian night.

## gravitational_caustic_refraction

- **Date**: 2026-05-09
- **Theme**: Gravitational lensing, light caustics, General Relativity, beautiful night sky
- **Technique**: 3D ray-tracing of 150,000 light rays deflected by four moving gravitational centers (lenses). Deflection is calculated using a vectorized non-linear force field, resulting in complex caustic folds and sharp light convergences. Multi-pass additive point rendering with a "Nebula Gold / Electric Azure / Diamond White" HSB palette and a subtle high-density starfield. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of space-time warping; silken ribbons of shimmering gold and electric azure light dance and fold into intricate caustic patterns as they are bent by invisible gravitational giants against the star-dusted obsidian night.

## vortex_phase_interference

- **Date**: 2026-05-09
- **Theme**: Quantum vortices, phase interference, superfluids, beautiful night sky
- **Technique**: 3D simulation of two interacting vortex rings with 150,000 particle tracers. Particles follow a simplified Biot-Savart velocity field and rotate around ring cores. When rings approach, their phase-velocity fields interfere, creating complex bridging structures. Multi-pass additive rendering with a "Electric Cyan / Royal Violet" HSB palette and a high-density background starfield. 20fps high-bitrate MP4.
- **Description**: A mesmerizing visualization of interacting quantum vortex rings in a superfluid medium; silken filaments of electric cyan and royal violet energy dance and weave through the void, creating intricate bridging structures as they collide in the star-dusted obsidian night.

## dark_energy_expansion_drift

- **Date**: 2026-05-09
- **Theme**: Dark energy, quintessence, accelerated expansion, cosmological constant, beautiful night sky
- **Technique**: 3D simulation of a "quintessence" field using a vectorized 3D scalar field. 120,000 particles representing dark energy quanta are advected by a repulsion field that increases with distance from the center (exponential expansion). Particles undergo virtual decay and leave silken threads. Multi-pass additive rendering with a "Cosmic Lavender/Deep Emerald/Silver" palette and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of the accelerating expansion of the universe; silken threads of cosmic lavender and deep emerald light stretch and thin as they drift into the obsidian night, representing the hidden energy driving the cosmos apart.

## topological_braid_flux

- **Date**: 2026-05-08
- **Theme**: Topology, knot theory, braid groups, cosmic threads, beautiful night sky
- **Technique**: 3D simulation of 16 "braid threads" evolved through a combined helical vortex flow and Perlin noise field. Each thread is a complex polyline whose crossing patterns are driven by phase-shifted oscillators and global rotation. Features multi-pass additive line rendering with a "Royal Purple/Electric Cyan/Crimson" palette and an integrated high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic dance of cosmic threads; silken braids of royal purple, cyan, and crimson light weave and tangle in a high-dimensional flow, representing the rhythmic connectivity of the vacuum against the star-dusted obsidian night.

## clifford_vortex_filaments

- **Date**: 2026-05-08
- **Theme**: Chaos theory, non-linear dynamics, attractor manifolds, turbulent flow, beautiful night sky
- **Technique**: 3D chaotic attractor based on a modified De Jong map. 200,000 particles are iteratively evolved through a system of coupled non-linear equations, where parameters ($a, b, c, d$) are slowly modulated via low-frequency oscillators. Features multi-pass additive point rendering with a "Molten Amber/Neon Violet/Electric Blue" palette and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic, silken knot of shimmering amber and violet light pulses and shifts in the void, revealing complex filamentary structures that weave through a chaotic mathematical manifold against the star-dusted obsidian night.

## spectral_tesseract_unfolding

- **Date**: 2026-05-08
- **Theme**: Higher dimensions, tesseract rotation, projection, mathematical beauty, beautiful night sky
- **Technique**: 4D rotation and 3D perspective projection of a hypercube. 200,000 particles sampled from the 4D face-cells of a tesseract are rotated simultaneously in $xy$ and $zw$ planes. The 4D coordinates are projected into 3D space using a perspective transform $1/(d-w)$. Features multi-pass additive point rendering with an iridescent spectral palette (HSB shift from Indigo to Violet to Gold) and an integrated starfield. 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering geometric structure of iridescent indigo and violet light turns and warps in the void, its higher-dimensional edges trailing golden sparks as it unfolds in ways that defy 3D logic against the star-dusted obsidian night.

## bioluminescent_mycelial_network

- **Date**: 2026-05-08
- **Theme**: Organic growth, mycelial networks, self-organization, cosmic biological emergence, beautiful night sky
- **Technique**: 3D agent-based simulation inspired by Physarum polycephalum (slime mold). 200,000 agents navigate a 128x128x128 pheromone density field, depositing trails and steering towards high-concentration gradients. The field is continuously evolved via diffusion (Gaussian blur) and decay using vectorized NumPy and Scipy. Features multi-pass additive point rendering with a "Cyan/Amethyst/White" bioluminescent palette and a high-density background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic vision of cosmic biological emergence; silken threads of electric cyan and royal amethyst light branch and weave through the void, self-organizing into a complex, shimmering mycelial web that pulses with an internal biological rhythm against the star-dusted obsidian night.

## higgs_field_symmetry

- **Date**: 2026-05-08
- **Theme**: Higgs mechanism, spontaneous symmetry breaking, phase transitions, scalar fields, beautiful night sky
- **Technique**: 3D simulation of a scalar field $\phi$ undergoing a symmetry-breaking phase transition. 200,000 particles representing local field excitations are evolved via Langevin-like dynamics driven by the gradient of the Higgs potential $V(\phi) = \alpha |\phi|^2 + \beta |\phi|^4$. The $\alpha$ parameter is smoothly transition from positive (symmetric) to negative (broken), causing the field to "roll" into the Mexican Hat vacuum manifold. Features multi-pass additive point rendering with a "White/Violet/Cyan/Gold" spectral palette and an integrated background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, high-fidelity vision of the birth of mass; a chaotic cloud of shimmering white-violet light undergoes a cosmic phase transition, collapsing into a structured, shimmering condensate of electric cyan and gold light that pulses with the hidden weight of the universe against the star-dusted obsidian void.

## chromospheric_spicule_flare

- **Date**: 2026-05-08
- **Theme**: Stellar chromosphere, plasma spicules, magnetic reconnection, solar flares, beautiful night sky
- **Technique**: 3D simulation of a stellar surface featuring hundreds of plasma "spicules" (short-lived vertical jets). 120,000 particles are emitted from a hemispherical base and advected by a dynamic magnetic field composed of 8 rotating dipoles. Periodic "magnetic reconnection" events trigger intense white-gold flares and rapid particle acceleration. Features multi-pass additive rendering with an "Incandescent Amber/Violet" HSB palette and a high-density background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, high-energy vision of a star's atmosphere; thousands of silken plasma jets erupt from an incandescent amber surface, twisting into complex magnetic loops that snap and flare with ultraviolet light against the star-dusted obsidian void.

## topological_quantum_braid

- **Date**: 2026-05-08
- **Theme**: Quantum fluids, knotted vortices, braid topology, superfluidity, beautiful night sky
- **Technique**: 3D simulation of a topological quantum fluid featuring a knotted vortex filament (Trefoil knot). 150,000 particles are advected via the Biot-Savart velocity field generated by the knotted core using vectorized NumPy with chunked point broadcasting. The knot undergoes a slow topological braid transformation. Features multi-pass additive rendering with a "Neon Emerald/Cyan/Indigo" HSB palette and a high-density background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering vision of a quantum fluid; silken filaments of electric emerald and cyan energy swirl and knot into a complex trefoil braid that pulses with hidden resonance against the star-dusted obsidian void.

## riemann_surface_unfolding

- **Date**: 2026-05-08
- **Theme**: Riemann surfaces, complex analysis, mathematical topology, high-dimensional manifolds, beautiful night sky
- **Technique**: 3D simulation of a complex manifold for $w^2 = z^3 - z$. The surface is rendered via 180,000 particles advected along the phase-gradient vector field of the complex potential. Implements multi-sheet topology where particles transition between sheets based on branch point proximity. Features multi-pass additive rendering with an iridescent "Spectral" HSB palette and a high-density background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A mesmerizing vision of mathematical beauty; a complex geometric surface unfolds and breathes in the void, its iridescent sheets swirling with silken threads of light that trace the hidden paths of complex functions against the star-dusted obsidian night.

## neutron_star_starquake

- **Date**: 2026-05-08
- **Theme**: Neutron stars, starquakes, crustal fracture, magnetospheric flaring, beautiful night sky
- **Technique**: 3D simulation of a neutron star surface using a noise-deformed sphere. Implements "Starquake" events where the crust fractures along stress-driven boundaries, rendered as high-intensity additive lines with volumetric glow. Ejected plasma (150,000 particles) is advected along helical magnetic field lines using vectorized NumPy. Features multi-pass additive rendering with an "Electric Cobalt/Gold" HSB palette and a high-density background starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, somber vision of a neutron star's violent surface; the dark obsidian crust shudders and splits, revealing blinding white-gold energy through jagged cracks that erupt into shimmering indigo plasma filaments against the star-dusted deep indigo void.

## vacuum_polarization_resonance

- **Date**: 2026-05-08
- **Theme**: Vacuum polarization, virtual particle pairs, dipole resonance, quantum electrodynamics, beautiful night sky
- **Technique**: 3D high-density particle simulation (200,000 particles) using vectorized NumPy. Particles are emitted as "virtual pairs" from a central region and advected by a dynamic 3D dipole electric field, creating polarized filaments. Visibility (alpha) is modulated by local field strength and particle lifetime. Features multi-pass additive rendering with a Cyan/Amethyst/Indigo palette and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering vision of the quantum vacuum; silken threads of electric cyan and royal amethyst energy polarize and align around an invisible dipole, creating an intricate tapestry of virtual light against the star-dusted obsidian void.

## axion_field_flux

- **Date**: 2026-05-07
- **Theme**: Dark matter, axion fields, Primakoff effect, scalar field oscillation, beautiful night sky
- **Technique**: 3D high-density particle simulation (240,000 particles) using vectorized NumPy. Particles are sampled from a multi-harmonic 3D scalar field $\phi(x, t)$. Implements "Primakoff conversion" where particle visibility (alpha) is modulated by local field phase and distance from a central magnetic flux string. Features multi-pass additive rendering with a Gold/Indigo/Cyan palette and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering vision of the hidden cosmos; a pulsing cloud of electric indigo and cyan light self-organizes into ghostly filaments around a blinding white-gold flux string, representing the conversion of dark matter axions into photons against the star-dusted obsidian void.

## neutrino_flavor_oscillation

- **Date**: 2026-05-07
- **Theme**: Neutrinos, flavor oscillation, weak interaction, ghostly flux, beautiful night sky
- **Technique**: 3D high-velocity particle simulation (220,000 particles) using vectorized NumPy. Particles follow needle-sharp trajectories representing ultra-high energy fluxes. Each particle's "flavor state" is modeled as a harmonic oscillator that modulates its HSB color (Cyan/Amethyst/Gold) and opacity to create a "ghostly" shifting effect. Features multi-pass additive rendering and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic vision of subatomic ghosts; a dense, shimmering stream of spectral light erupts from a stellar core, its particles flickering and shifting between electric cyan, royal amethyst, and gold as they surge through the star-dusted obsidian void.

## quantum_tunneling_resonance

- **Date**: 2026-05-07
- **Theme**: Quantum tunneling, wave packet interference, potential barrier, beautiful night sky
- **Technique**: 3D particle simulation (160,000 particles) modeling wave packet dynamics. Particles follow paths guided by incident, reflected (interference), and tunneled ($T \approx 0.05$) wavefunction components at a potential barrier. Features multi-pass additive rendering with HSB spectral mapping (Violet/Cyan/Gold) and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic vision of quantum mechanics; iridescent waves of electric violet and cyan crash against an invisible wall, rippling backward in complex fringes while a needle-sharp beam of white-gold light "leaks" through the barrier and vanishes into the deep obsidian night.

## superfluid_kelvin_waves

- **Date**: 2026-05-07
- **Theme**: Superfluidity, Kelvin waves, vortex line oscillation, quantum turbulence, beautiful night sky
- **Technique**: 3D particle simulation (120,000 particles) sampled along 12 closed-loop vortex filaments. Filaments are modulated by multiple helical harmonic oscillators (Kelvin waves) using vectorized NumPy. Features multi-pass additive rendering with HSB spectral mapping (Teal/Violet/White) and a high-density starfield (10,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic vision of quantum fluids; silken loops of electric teal and royal violet light oscillate with high-frequency helical ripples, appearing like cosmic threads vibrating in a silent star-dusted void.

## relativistic_caustic_drift

- **Date**: 2026-05-07
- **Theme**: Gravitational caustics, relativistic drift, light warping, beautiful night sky
- **Technique**: 3D particle simulation (180,000 particles) using a vectorized deflection model with 4 dynamic gravitational hubs. Features multi-pass additive rendering with influence-weighted spectral mapping (Cyan/Silver/Gold) and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A mesmerizing vision of light warping in the deep cosmos; liquid-like ribbons of electric cyan and silver energy drift and warp across the void, erupting into intense white-gold caustic networks wherever invisible mass centers concentrate the light against the star-dusted night.

## lattice_strain_diffraction

- **Date**: 2026-05-07
- **Theme**: Crystal lattices, mechanical strain, diffraction patterns, beautiful night sky
- **Technique**: 3D grid of 8,000 nodes (20x20x20) deformed by dynamic Gaussian strain centers and harmonic vibration. Features strain-weighted spectral rendering using HSB color mapping (Cyan/Magenta/Gold) and additive blending. 60fps high-bitrate MP4.
- **Description**: A majestic vision of a pulsing crystal lattice; a vast geometric grid of light warps and breaths in the void, erupting into shimmering rainbows of spectral energy wherever the structure is strained against the deep, star-dusted night.

## singularity_braiding

- **Date**: 2026-05-07
- **Theme**: Quantum field topology, cosmic strings, topological defects, beautiful night sky
- **Technique**: 3D particle simulation (150,000 particles) advected along the gradient of a dynamic complex potential field. Multi-pass additive rendering with HSB spectral mapping (Cyan/Amethyst/Gold) and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic vision of cosmic topological defects; silken threads of electric cyan and royal amethyst light braid and twist around invisible singularities, creating an intricate tapestry of quantum energy against the deep obsidian night.

## star_cluster_core

- **Date**: 2026-05-07
- **Theme**: Globular cluster, stellar dynamics, core collapse, n-body simulation, beautiful night sky
- **Technique**: 3D high-density stellar simulation featuring 3,000 dynamic "luminous" stars (using a vectorized central-potential gravity model) and 100,000 background "cloud" stars. Features multi-pass additive rendering with an "Ancient Stellar Core" HSB palette (Gold/Amber/White/Cyan). The central core is rendered with higher intensity and scale to simulate dynamical core collapse, set against a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering ball of thousands of stars that pulses with a golden intensity; at its heart, a dense sea of light swirls in a chaotic yet ordered orbital web against the deep obsidian night, representing the late-stage evolution of a dense globular cluster.

## cosmic_string_network

- **Date**: 2026-05-07
- **Theme**: Topological defects, cosmic strings, loops, primordial universe, beautiful night sky
- **Technique**: 3D simulation of a cosmic string network featuring 12 infinite strings and 40 closed loops. 120,000 particles are sampled along the paths using vectorized linear interpolation and animated with harmonic noise. Features intensity peaks at "cusps" where strings reach high energy, rendered with blinding white highlights. Multi-pass additive rendering uses an "Ultraviolet Singularity" palette (Cyan/Amethyst/Indigo) and a high-density starfield (10,000 stars). 60fps high-bitrate MP4.
- **Description**: A vast, shimmering web of razor-sharp light threads that twist and snap in the primordial void; silken loops of electric cyan and white energy drift and dissolve against a deep, star-dusted night sky, representing the energy relics of the early universe.

## magnetic_filament_weave

- **Date**: 2026-05-07
- **Theme**: Galactic magnetic fields, interstellar filaments, cosmic magnetism, beautiful night sky
- **Technique**: 3D magnetic field simulation using a combined toroidal spiral field and 5 localized rotating dipoles (NumPy). 150,000 particles are advected along the field lines, leaving persistent silken trails that create a dense, braided texture. Features multi-pass additive rendering with a "Cosmic Neon" HSB palette (Cyan/Magenta/Gold) and a high-density starfield (12,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic visualization of the galaxy's magnetic architecture; thousands of silken, glowing filaments trace the invisible field lines that braid and twist through the interstellar void, acting as a cosmic loom for stardust against a silent, star-dusted night.

## lensing_caustic_network

- **Date**: 2026-05-07
- **Theme**: Gravitational lensing, caustic networks, high magnification, dark matter clusters, beautiful night sky
- **Technique**: 2D gravitational lens simulation using a vectorized multi-hub mass model (NumPy). Visualizes the "caustics"—lines of theoretically infinite magnification—created by a cluster of 6 invisible dark matter halos. 180,000 particles are sampled based on the local magnification field of an animated background source. Features multi-pass additive rendering with a "Glacial Aurora" HSB palette (Cobalt/Cyan/Silver) and a high-density starfield (10,000 stars). 60fps high-bitrate MP4.
- **Description**: A mesmerizing, ever-shifting web of brilliant light ripples and morphs across the cosmos; like sunlight on the bottom of a pool, these gravitational caustics reveal the invisible architecture of dark matter, casting a cold and beautiful glow against the star-dusted obsidian void.

## pulsar_wind_nebula

- **Date**: 2026-05-07
- **Theme**: Pulsar wind, termination shock, synchrotron radiation, Crab Nebula filaments, beautiful night sky
- **Technique**: 3D particle simulation (120,000 particles) using vectorized NumPy for performance. Particles are emitted from a central pulsing core as a relativistic wind. At the termination shock ($r \approx 280$), they enter a turbulent regime driven by multi-octave pseudo-noise and helical magnetic fields. Features multi-pass additive rendering with synchrotron-inspired color mapping (Cyan -> Violet -> Gold) and a high-density starfield (8,000 stars). 60fps high-bitrate MP4.
- **Description**: A blindingly bright, pulsing heart of a nebula; silken filaments of electric light swirl and knot into a complex, glowing web of energy against the deep obsidian night, representing the violent and beautiful environment around a rapidly rotating pulsar.

## quantum_vortex_lattice

- **Date**: 2026-05-07
- **Theme**: Quantum vortices, superfluidity, vortex lattice, topological defects, beautiful night sky
- **Technique**: 3D simulation of a rotating superfluid with 19 quantized vortices in a hexagonal lattice. Implements helical Kelvin waves and a "melting" phase transition into turbulence. 30,000 particles are advected along the vortex cores. Features a transition from ordered Cyan/Indigo to chaotic shimmering Gold. 60fps high-bitrate MP4.
- **Description**: A macroscopic window into the quantum world; a perfect, shimmering lattice of vertical silk-like threads rotates in a deep blue void, before erupting into a chaotic and beautiful dance of tangled loops and swirling golden dust.

## nucleosynthesis_fusion_core

- **Date**: 2026-05-07
- **Theme**: Stellar nucleosynthesis, nuclear fusion, plasma convection, gamma-ray bursts, beautiful night sky
- **Technique**: 3D high-velocity particle simulation (150,000 points) using vectorized `py5.points()`. Implements a softened central gravity and a toroidal convection field. Particles undergo "elemental transformation" (H -> He -> C -> O) based on local temperature/density proxies. Triggers "gamma-ray" streaks upon fusion events. Multi-pass additive rendering for the central plasma glow. 60fps high-bitrate MP4.
- **Description**: A churning, incandescent heart of a giant star; a dense sea of electric blue nuclei collide and ignite in spectacular bursts of gold and violet light, slowly transforming the core into a rich, multi-layered tapestry of heavier elements.

## hyperspectral_lens_cluster

- **Date**: 2026-05-07
- **Theme**: Gravitational lensing, galaxy cluster, dark matter, Einstein rings, chromatic aberration, beautiful night sky
- **Technique**: 2D projection of a complex gravitational lens field. Background "galaxies" (60,000 particles) are distorted by a cluster of 6 massive objects using a vectorized deflection model. Implements "hyperspectral smearing" where different color channels are deflected by varying amounts to simulate relativistic chromatic aberration. Uses additive blending for vibrant, shimmering arcs and rings. 60fps high-bitrate MP4.
- **Description**: A mesmerizing window into the deep universe; distant, colorful galaxies are stretched and warped into elegant, shimmering arcs and glowing Einstein rings by an invisible, massive cluster in the foreground, creating a spectral tapestry of light against the silent obsidian void.

## kilonova_merger_ripple

- **Date**: 2026-05-07
- **Theme**: Neutron star merger, kilonova, nucleosynthesis, gravitational waves, beautiful night sky
- **Technique**: 3D simulation of a binary neutron star system spiraling into a collision. Features a real-time background starfield ripple effect simulating space-time distortion. Post-collision, it triggers an asymmetric ejection of 300,000 particles (toroidal + polar jets) with a spectral shift from blue-white to rose gold and platinum. 60fps high-bitrate MP4.
- **Description**: A violent and beautiful celestial event; two tiny, blinding dots dance in a tightening spiral, warping the very stars behind them, before vanishing into a spectacular explosion of shimmering gold and platinum dust that fills the void.

## cosmic_inflation_pulse

- **Date**: 2026-05-07
- **Theme**: Big Bang, cosmic inflation, exponential expansion, cooling of the universe, large-scale structure seeding, beautiful night sky
- **Technique**: 3D particle simulation (250,000 particles) using an exponential expansion model. Particles are emitted from a central singularity and rapidly pushed outward. Implements "quantum seeding" where multi-harmonic interference in the early phase grows into silken filaments and clusters. Features a time-dependent temperature mapping from blinding white to electric cyan and royal amethyst. 60fps high-bitrate MP4.
- **Description**: A breathtaking visualization of the birth of the cosmos; a blindingly bright point of light erupts into a vast, shimmering web of spectral energy that cools and self-organizes into intricate filaments against the deep, expanding indigo void.

## hawking_radiation_singularity

- **Date**: 2026-05-07
- **Theme**: Black hole evaporation, virtual particle pairs, Hawking radiation, event horizon entropy, beautiful night sky
- **Technique**: 3D simulation of a black hole's evaporation via virtual particle pair production at the event horizon ($r=2M$). Escaping particles (White-Gold) follow twisted "yarn-like" trajectories, while falling particles (Electric Indigo) are consumed by the central shadow. Features a multi-pass additive rendering with a pulsing "stretched horizon" glow and a high-density background starfield (10,000 stars). 60fps high-bitrate MP4.
- **Description**: A majestic and somber vision of a black hole slowly bleeding light into the void; a perfect circle of darkness is surrounded by a boiling, iridescent shell of quantum energy, with silken threads of light escaping like cosmic steam into a deep, star-dusted night.

## spectral_jet_precession

- **Date**: 2026-05-06
- **Theme**: Relativistic jet, pulsar precession, helical flow, beautiful night sky
- **Technique**: 3D simulation of a precessing bipolar relativistic jet using a recycling particle system (200,000 particles). Features time-modulated axial rotation that carves majestic helical "corkscrew" paths in the intergalactic medium. Multi-pass additive rendering with a spectral Teal/Violet palette, a high-intensity flickering core, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic vision of a pulsar beacon; two silken beams of light twist through the intergalactic void in a beautiful, geometric corkscrew pattern, pulsing with spectral energy against the deep obsidian night.

## protoplanetary_clump_void

- **Date**: 2026-05-06
- **Theme**: Protoplanetary disk, gravitational instability, planet birth, beautiful night sky
- **Technique**: 3D simulation of a young stellar system's accretion disk using 180,000 particles. Features Keplerian orbital dynamics and local gravitational clumping around hidden attractor points (proto-planets). Multi-pass additive rendering with a Solar Gold and Rusty Orange palette, high-intensity planetesimal cores, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic vision of a cosmic cradle; a vast, golden swirling disk of dust is sculpted by invisible forces as bright, shimmering knots of light form in the resonance gaps, representing the birth of a new solar system against the deep obsidian night.

## hyper_dimensional_tesseract_lattice

- **Date**: 2026-05-06
- **Theme**: 4D geometry, tesseract lattice, high-tech urbanism, beautiful night sky
- **Technique**: 3D projection of a rotating 4D tesseract lattice (a $3 \times 3 \times 3$ grid of hypercubes). Features continuous 4D rotations in multiple planes ($XW$, $YW$, $ZW$), causing the projected 3D geometry to morph and "unfold" surrealistically. Multi-pass additive rendering with a Cyan/Magenta palette, $W$-coordinate-based alpha modulation for hyperspace depth, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A mesmerizing, high-tech vision of higher-dimensional architecture; a vast, glowing grid of light morphs and unfolds into itself, representing the hidden data-structures that underpin a digital, iridescent cosmos against the deep obsidian night.

## quantum_entanglement_cascade

- **Date**: 2026-05-06
- **Theme**: Entanglement, non-locality, information cascade, beautiful night sky
- **Technique**: 3D simulation of a "Quantum Decision Tree" using a stochastic fractal branching algorithm. Features a dynamic information cascade system where energy pulses (represented as high-intensity white particles) traverse the silken teal branches, splitting and merging at each node. Multi-pass additive rendering with a Teal/Violet palette, shimmering node highlights, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic, high-tech "tree of light" that pulses with the energy of quantum information; its delicate, silken branches stretch into the infinite intergalactic void, representing the non-local connections that bind the cosmos together against the deep obsidian night.

## quantum_foam_architecture

- **Date**: 2026-05-06
- **Theme**: Planck scale geometry, quantum foam, architectural abstraction, beautiful night sky
- **Technique**: 3D simulation of a boiling quantum vacuum using time-modulated volumetric noise. Features 40,000 "quanta" points that emerge and dissolve based on noise density thresholds. Active nodes are connected via a shimmering spectral proximity mesh and accompanied by recursive geometric box-structures. Multi-pass additive rendering with a Cyan/Violet palette and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A mesmerizing, high-tech visualization of the fundamental structure of space-time; a boiling, geometric sea of light emerges and dissolves at the edge of perception, representing the microscopic jitter of reality against the deep obsidian night.

## digital_accretion_singularity

- **Date**: 2026-05-06
- **Theme**: Data singularity, black hole accretion, high-tech urbanism, beautiful night sky
- **Technique**: 3D accretion disk visualization using polar quadtree subdivision to generate a spiraling digital metropolis. Blocks accelerate and heat up (shifting from Cyan to Magenta) as they fall towards a central event horizon. Features relativistic coordinate warping, additive wireframe rendering, a volumetric singularity glow, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic vision of a data-singularity; a vast, glowing grid of information and architectural geometry is shredded and consumed by an invisible abyss, pulsing with spectral energy against the deep obsidian night.

## nebular_filament_lattice

- **Date**: 2026-05-06
- **Theme**: Interstellar filaments, magnetic alignment, silken textures, beautiful night sky
- **Technique**: 3D simulation of a complex intergalactic filament network using 200,000 particles. Particles follow a braided magnetic vector field generated via vectorized rotation matrices and helical drift. Features multi-pass additive rendering with a spectral Teal and Amethyst palette, a central volumetric energy pulse, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A majestic, shimmering web of luminous filaments that stretch across the cosmic void; thousands of silken threads in electric teal and soft amethyst pulse with energy, appearing like cosmic silk woven by invisible magnetic forces against the silent obsidian night.

## supernova_light_echo

- **Date**: 2026-05-06
- **Theme**: Supernova, light echoes, interstellar dust, beautiful night sky
- **Technique**: 3D simulation of a light echo phenomenon in a dense interstellar dust cloud (150,000 particles). Features a multi-octave Simplex noise-driven nebulosity that is progressively "unveiled" by an expanding spherical shell of light. Multi-pass additive rendering includes a bright white supernova core, shimmering electric blue dust filaments, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A central celestial explosion triggers a majestic wave of light that travels through the cosmic void, momentarily illuminating the intricate, silken structures of hidden gas clouds in spectral blue and silver against the silent obsidian night.

## lensed_fractal_urbanism

- **Date**: 2026-05-06
- **Theme**: High-tech urbanism, gravitational lensing, recursive geometry, beautiful night sky
- **Technique**: 3D recursive quadtree subdivision generating a multi-level digital metropolis. Each urban block is subjected to a central gravitational lensing warp, transforming rectilinear data-architecture into shimmering arcs and hyperbolic canyons. Features multi-pass additive rendering with a spectral palette (Cyan/Magenta), volumetric singularity glow, and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A vast, glowing metropolis spanning a cosmic horizon, its digital architecture warped and stretched into shimmering arcs by an invisible gravitational force against a deep, star-dusted indigo night.

## orbital_data_mesh

- **Date**: 2026-05-06
- **Theme**: Orbital infrastructure, global connectivity, high-tech urbanism, beautiful night sky
- **Technique**: 3D orbital simulation of 3,000 satellites across three distinct shells. Proximity-based laser links form a dynamic "data mesh" using additive line rendering. Features a dark, atmospheric planetary core with multi-layer volumetric glow and a high-density background starfield. Randomized "data bursts" flare through the network to simulate active information transfer. 60fps high-bitrate MP4.
- **Description**: A majestic, high-tech vision of a planet cocooned in a shimmering web of global connectivity; thousands of satellites and laser links in cyber cyan and stark white pulse with information against the silent, star-dusted void of a deep indigo night.

## sagittarius_a_orbits

- **Date**: 2026-05-06
- **Theme**: Galactic center, orbital dynamics, relativistic speeds, beautiful night sky
- **Technique**: 3D orbital simulation of 1,000 "S-stars" using Keplerian dynamics around a central singularity. Stars follow highly elliptical orbits, stretching into silken spectral trails as they reach relativistic speeds near periapsis. Features a multi-pass additive rendering for the star cluster and a dense background galactic starfield. 60fps high-bitrate MP4.
- **Description**: A high-energy visualization of the heart of our galaxy; 1,000 stars dance in a chaotic yet majestic orbital web around the invisible supermassive black hole Sagittarius A*, their paths tracing glowing filaments of white and gold light against a deep indigo void.

## ring_resonance_void

- **Date**: 2026-05-10
- **Theme**: Planetary rings, orbital resonance, shepherd moons, beautiful night sky
- **Technique**: 3D orbital simulation (180,000 particles) using vectorized NumPy for Keplerian dynamics. Features a perturbation model where invisible shepherd moons create density "wakes" and resonance gaps in a thin silken disk. Multi-pass rendering includes a background starfield, additive spectral ring particles (Pale Gold/Ice Blue), and a planetary shadow simulation. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of a planetary ring system seen from an oblique angle; nearly 200,000 silken particles swirl in complex orbital resonance, revealing delicate wave patterns and sharp gaps carved by the gravity of invisible moons against a silent, star-dusted night sky.

## lensed_nebular_void

- **Date**: 2026-05-06
- **Theme**: Gravitational lensing, interstellar gas, black holes, beautiful night sky
- **Technique**: 3D-like gravitational lensing simulation on a dense particle field (150,000 particles). Features a procedural nebula generated via multi-octave Simplex noise with an HSB spectral palette (Teal/Amethyst/Amber). Vectorized NumPy coordinate warping simulates the light-bending effects of a central singularity, creating a dynamic Einstein ring and shadow. 60fps high-bitrate MP4.
- **Description**: A majestic visualization of a supermassive black hole drifting across a colorful planetary nebula; the invisible mass of the singularity bends the light of distant gas and stars into a shimmering, iridescent halo of energy against the silent obsidian void.

## chromatic_wormhole

- **Date**: 2026-05-06
- **Theme**: General relativity, wormholes, spacetime tunnels, beautiful night sky
- **Technique**: 3D particle simulation (120,000 particles) using a hyperboloid mapping logic. Particles follow helical-hyperbolic trajectories through a spacetime throat. Features a distance-based color shift (Cyan to Amethyst) representing gravitational energy gradients. Multi-pass additive rendering for the tunnel core and a high-density background starfield. 60fps high-bitrate MP4.
- **Description**: A breathtaking traversal through an Einstein-Rosen Bridge; a luminous tunnel of electric cyan and royal amethyst light stretches across the void, with high-energy particles surging through the throat amidst a silent, star-dusted night sky.

## stellar_megastructure

- **Date**: 2026-05-06
- **Theme**: Megastructures, stellar engineering, recursive architecture, beautiful night sky
- **Technique**: 3D spherical quadtree subdivision mapped to (theta, phi) coordinates. Leaf nodes are rendered as obsidian boxes (`py5.box()`) with height modulation. Features a multi-pass central star core with additive bloom and a NumPy-vectorized starfield. Neon "data conduits" are rendered as additive lines on the slab surfaces. 60fps high-bitrate MP4.
- **Description**: A visualization of a Type II civilization's Dyson Shell in progress; a massive, dark, recursive geometric shell partially encloses a pulsing star, revealing the blinding white-gold energy of the core through its gaps against a silent, star-dusted night.

## dla_metropolis

- **Date**: 2026-05-06
- **Theme**: Organic urbanism, diffusion-limited aggregation (DLA), brutalist megastructures, beautiful night sky
- **Technique**: 3D Diffusion-Limited Aggregation (DLA) simulation (3,200 monoliths) using a NumPy-optimized spatial hashing grid for fast particle collision. Monoliths are rendered with skyscraper proportions and multi-pass aesthetics: (1) Solid obsidian core (BLEND), (2) Neon edge highlights (ADD), and (3) Subtle volumetric glow (ADD). HSB palette (Cyan/Indigo/Magenta) with a twinkling starfield backdrop. 60fps high-bitrate MP4.
- **Description**: A vast, fractal-like megacity grown through organic aggregation in the deep void; thousands of obsidian skyscrapers with glowing neon edges form a dense, bristling monolith that pulses with digital life against a silent, star-dusted night.

## tidal_disruption

- **Date**: 2026-05-06
- **Theme**: Cosmic catastrophe, spaghettification, event horizon, beautiful night sky
- **Technique**: 3D particle simulation (180,000 particles) using a relativistic gravitational potential. A central "singularity" exerts non-linear tidal forces that stretch a spherical particle emitter into a long, twisting filament. Particles are colored by speed-based HSB (simulating Doppler shift and heating), with a multi-pass additive core glow for the photon ring. 60fps high-bitrate MP4.
- **Description**: A star's violent and beautiful death; caught in the immense gravity of a supermassive black hole, it is shredded into a glowing "noodle" of plasma that spirals toward the event horizon in a deep, star-dusted void.

## synaptic_nebula

- **Date**: 2026-05-06
- **Theme**: Cosmic biology, information flow, synaptic currents, beautiful night sky
- **Technique**: Physics-driven particle simulation (80,000 particles) using NumPy. Particles gravitate toward 30 "synaptic nodes" while being perturbed by noise-driven drift. Vectorized rendering using `py5.points()` for performance. Synaptic nodes feature pulsing multi-pass glow coronas (spheres) with distance-based scaling. HSB palette (Cyan/Blue/Violet/Rose). 60fps high-bitrate MP4.
- **Description**: A vast, bioluminescent neural network in the deep void; 80,000 data-particles flow through nebular filaments, connecting 30 pulsing synaptic nodes that flare with the light of a cosmic intelligence.

## algorithmic_geode

- **Date**: 2026-05-06
- **Theme**: Digital mineralization, urban recursion, inner light, modern city feel, beautiful night sky
- **Technique**: 3D architectural sketch using P3D. Exterior consists of 12 jagged graphite shards (box primitives) with bright edge highlights and volumetric glow "leaks". Interior faces feature a recursive Quadtree city grid (depth 6) with animated HSB neon strokes. Multi-pass rendering for additive core bloom using concentric spheres and depth-test disabling. 60fps high-bitrate MP4.
- **Description**: A massive, jagged obsidian geode floats in the void; its dark, geometric shell is split open to reveal a pulsing, neon-lit metropolis of infinite recursive complexity, casting a cold, digital glow into the surrounding starfield.

## entropic_dyson_swarm

- **Date**: 2026-05-06
- **Theme**: Megastructures, Dyson swarm, solar energy, orbital entropy, beautiful night sky
- **Technique**: 3D orbital simulation (120,000 particles) using NumPy-vectorized Keplerian dynamics. Features "entropic drift" using Simplex-like noise perturbations to simulate gravitational instability. Multi-pass rendering for a pulsing solar core (60 units) and its corona glow. Particles are colored by orbital speed (Cyan to Gold) with additive blending. 60fps high-bitrate MP4 encoding.
- **Description**: A vast, shimmering megastructure in a deep indigo void; 120,000 collector mirrors swirl around a blindingly bright white-gold star, their paths tracing a chaotic yet organized dance of light that pulses with the energy of a distant civilization.

## event_horizon_echo

- **Date**: 2026-05-06
- **Theme**: Black hole, event horizon, accretion disk, Doppler shift, beautiful night sky
- **Technique**: Relativistic particle simulation (130,000 particles) orbiting a central gravitational singularity. Particles follow Keplerian orbits with additional relativistic drag (1/r^4) and precession. Implements "Doppler beaming" where color and brightness are modulated by the orbital velocity relative to the camera (Approaching = Electric Cyan & Bright; Receding = Amber & Faint). Multi-pass rendering for the intense photon ring and the dark shadow of the event horizon. 60fps high-bitrate MP4 encoding.
- **Description**: A majestic and terrifying view of a supermassive black hole; a shimmering disk of light swirls around a perfect circle of absolute darkness, its colors shifting from electric blue to deep amber as it orbits at near-light speeds against a silent star-dusted void.

## vacuum_fluctuations_p2 (3D Particles)

- **Date**: 2026-05-06
- **Theme**: Vacuum fluctuations, quantum foam, virtual particles, beautiful night sky
- **Technique**: 3D particle simulation (150,000 particles) using a "virtual emission" model. Particles are generated based on structured interference fields (sine-wave probability volumes), representing vacuum excitations. Each particle has a very short lifetime (annihilation) and a high "uncertainty" jitter in its velocity. Multi-pass rendering with life-ratio color mapping (Birth/White to Decay/Indigo). 60fps high-bitrate MP4 encoding.
- **Description**: A mesmerizing view of the "empty" void; the obsidian space is a bubbling cauldron of light where thousands of tiny, indigo and white sparks flicker into existence and vanish in a shimmering quantum dance across the star-dusted night.

## dark_matter_halo

- **Date**: 2026-05-06
- **Theme**: Dark matter, cosmic web, gravitational lensing, beautiful night sky
- **Technique**: 3D particle simulation (120,000 particles) representing the "cosmic web". Particles aggregate into filaments and halos using hub-based attraction. Features a "gravitational lensing" effect where 4,500 background stars are dynamically distorted by the invisible mass of the hubs. Multi-pass rendering with soft, ethereal "halo" glows and ghost-like particle filaments. 60fps high-bitrate MP4 encoding.
- **Description**: A haunting visualization of the universe's hidden architecture; faint, ghostly filaments of ghostly amethyst and cobalt energy weave through the void, while the light from distant stars is warped and bent by the immense, invisible mass of the dark matter halos.

## neutron_star_jet

- **Date**: 2026-05-06
- **Theme**: Neutron star, relativistic jets, pulsar, magnetic precession, beautiful night sky
- **Technique**: High-velocity particle emission (160,000 particles) from two antipodal poles of a central precessing sphere. Particles follow relativistic trajectories with helical twisting (magnetic field) and outward expansion. The rotation axis precesses over time, creating a "lighthouse" sweep effect. Multi-pass rendering for the blindingly bright core and the shimmering spectral jets. 60fps high-bitrate MP4 encoding.
- **Description**: A terrifyingly powerful cosmic lighthouse; two blindingly bright beams of cobalt and magenta energy erupt from a shimmering white core, sweeping through the star-dusted void in a complex precessing rhythm that illuminates the deep celestial void.

## cosmic_loom

- **Date**: 2026-05-06
- **Theme**: Cosmic weaving, spacetime fabric, silken threads, beautiful night sky
- **Technique**: 3D particle simulation (100,000 particles) using a "weaving" attractor model. Three dynamic 3D Bezier splines ("loom stars") move in complex, harmonic paths through the void. Particles are attracted to the nearest points on the splines, creating dense, shimmering filaments that trace the weaving motion. Multi-pass rendering with high-persistence trails and additive blending. 60fps high-bitrate MP4 encoding.
- **Description**: An intricate, shimmering tapestry of light that appears to be woven by invisible celestial needles; silken threads of royal amethyst and electric indigo energy curve and twist across the star-dusted void, leaving glowing white-gold echoes of their harmonic dance.

## photon_fluid

- **Date**: 2026-05-06
- **Theme**: Photon fluid, Bose-Einstein condensation, light dynamics, beautiful night sky
- **Technique**: 2D grid-based fluid simulation (NumPy) with particle advection (100,000 particles). Features a "photon density" field that fluctuations with high-frequency noise before condensing into a coherent central "super-photon" peak. Additive blending and speed-based spectral coloring. 60fps high-bitrate MP4 encoding.
- **Description**: A vibrant, shimmering sea of light that begins as chaotic violet and cyan ripples, slowly converging into a singular, blindingly bright white-gold core at the center of a silent star-dusted void.

## magnetic_storm

- **Date**: 2026-05-06
- **Theme**: Magnetosphere, solar wind, bow shock, auroral energy, beautiful night sky
- **Technique**: Vectorized 3D particle advection (150,000 particles) along a combined magnetic dipole field and constant solar wind flux. Particles are continuously emitted from a solar source and deflected by a parabolic magnetic shield. Features a shimmering bow shock, trapped auroral filaments, and a long magnetotail. Multi-pass rendering for the planet and its atmospheric glow. 60fps high-bitrate MP4 encoding.
- **Description**: A majestic visualization of a planet's invisible shield; a constant stream of molten white-gold particles from the sun is deflected into a beautiful, glowing shell of electric emerald and cyan energy, trailing off into the deep indigo void as a shimmering magnetotail.

## superfluid_vortices

- **Date**: 2026-05-06
- **Theme**: Superfluidity, quantized vortices, Bose-Einstein condensate, beautiful night sky
- **Technique**: Vectorized point-vortex simulation (Biot-Savart law) using NumPy. 120 dynamic vortices and 120,000 particle tracers. The velocity field is calculated as the sum of rotations from all active vortices. Tracers follow the flow with high persistence and sub-pixel glow, creating a dense, iridescent tapestry of quantum turbulence. 60fps high-bitrate MP4 encoding.
- **Description**: A mesmerizing, shimmering visualization of quantum turbulence where 120,000 silken filaments in electric cyan, ice blue, and indigo swirl around invisible singularities; the intricate tapestry of phase-space resonance pulses against a dark, star-dusted night sky.

## galactic_collision

- **Date**: 2026-05-06
- **Theme**: Galactic collision, tidal tails, galactic cannibalism, beautiful night sky
- **Technique**: N-body particle simulation (120,000 particles) using vectorized NumPy gravity (softened kernel). Two initial spiral distributions with distinct angular momenta and rotation axes. Features "tidal tail" formation, star clumping, and a high-density starfield background. Multi-pass rendering for central bulge glow using additive blending. 60fps high-bitrate MP4 encoding.
- **Description**: A massive, slow-motion cosmic dance where two spiral galaxies tear each other apart, leaving long, shimmering filaments of stars across the obsidian void; one galaxy glows in electric cyan while the other burns in royal amethyst, their cores merging into a white-gold brilliance against the silent star-dusted night.

## cometary_ion_tail

- **Date**: 2026-05-05
- **Theme**: Comet, ion tail, dust tail, solar wind, beautiful night sky
- **Technique**: 3D particle simulation (60,000 particles) with a dual-tail physics model. Implements a curved, golden "dust tail" (inertia + radiation pressure) and a straight, electric-blue "ion tail" (noise-driven solar wind advection). Multi-layer rendering for the cometary coma and shimmering tail filaments. 60fps high-bitrate MP4 encoding
- **Description**: A magnificent comet streaking through the deep celestial void; its nucleus glows with a ghostly white light, trailing a massive dual tail that stretches across the stars—one curving gracefully like a golden ribbon, the other pointing rigidly away from the sun in a beam of shimmering electric blue.

## stellar_nursery_dust

- **Date**: 2026-05-05
- **Theme**: Stellar nursery, gravitational collapse, protostars, beautiful night sky
- **Technique**: 3D particle simulation (80,000 particles) using a vectorized gravity model with 12 dynamic mass centers. Features multi-layer rendering: a coarse "gas" background, medium-density "dust" clouds, and white-hot "protostar" cores. 60fps high-bitrate MP4 encoding
- **Description**: A vast, swirling cosmic cloud collapsing under its own weight; deep violet dust gives way to shimmering cyan filaments, culminating in the birth of brilliant white-hot infant stars that illuminate the nebula from within.

## solar_flare_loops

- **Date**: 2026-05-05
- **Theme**: Solar flare loops, magnetic arcs, plasma dynamics, beautiful night sky
- **Technique**: 3D magnetic loop simulation using 24 dynamic Bezier curves and 48,000 particles with volumetric noise offsets. Multi-pass rendering for incandescent core glow and plasma filaments (core/halo), 60fps high-quality MP4 encoding
- **Description**: A high-energy visualization of a star's surface; massive arcs of shimmering plasma rise and fall from the incandescent solar core, pulsing with rhythmic magnetic energy against the silent obsidian void.

## event_horizon_shadow

- **Date**: 2026-05-05
- **Theme**: Black hole, event horizon, accretion disk, light warping, beautiful night sky
- **Technique**: Accretion disk simulation (70,000 particles) with Keplerian orbits, Doppler-shift color mapping (HSB), dramatic gravitational lensing (Einstein ring approximation) on a star-dusted background, 60fps high-quality MP4 encoding
- **Description**: A terrifyingly beautiful visualization of a supermassive black hole; light from the background stars is warped into a shimmering Einstein ring around the central shadow, while a high-energy accretion disk of electric cyan and molten orange plasma swirls at relativistic speeds.

## supernova_remnant

- **Date**: 2026-05-05
- **Theme**: Supernova remnant, expanding shockwaves, interstellar dust, beautiful night sky
- **Technique**: 3D particle simulation (120,000 particles) with radial shockwave expansion, multi-octave sine-based turbulence, velocity drag, multi-pass rendering (glow/core) for high-density volumetric feel, 60fps high-quality MP4 encoding
- **Description**: A massive, explosive expansion of stardust that fragment into intricate filaments of electric violet and crimson; the work simulates the catastrophic death of a star and the subsequent formation of a shimmering nebula within the silent obsidian void.

## string_theory_manifold

- **Date**: 2026-05-05
- **Theme**: Calabi-Yau manifolds, higher dimensions, hidden geometry, beautiful night sky
- **Technique**: 3D parametric surface (P3D) based on nested complex trigonometric transformations, dynamic breathing via harmonic modulation, high-density starfield with localized alpha twinkle, HSB-based iridescent wireframe rendering, 60fps high-quality MP4 encoding
- **Description**: A complex, shimmering geometric form that appears to rotate and fold into itself, revealing hidden symmetries in a silent cosmic void of deep indigo and distant stars.

## cymatic_nebula

- **Date**: 2026-05-05
- **Theme**: Cymatics, acoustic trapping, celestial resonance, beautiful night sky
- **Technique**: 2D grid-based sound pressure simulation (Chladni function), particle advection (80,000 particles) using gradient-descent towards nodal regions, high-persistence silken trails, vectorized additive blending, 60fps high-quality MP4 encoding
- **Description**: A shimmering, silken nebula that self-organizes into complex geometric patterns as if driven by invisible celestial frequencies; glowing filaments in electric indigo and cyan converge into rhythmic standing-wave nodes across a deep, star-dusted void.

## vacuum_fluctuations_p1 (2D Field)

- **Date**: 2026-05-05
- **Theme**: Quantum physics, virtual particles, zero-point energy, beautiful night sky
- **Technique**: Vectorized multi-wave field synthesis (12 oscillators), stochastic excitation thresholding, transient entanglement link simulation (proximity-based), additive blending, 60fps high-quality MP4 encoding.
- **Description**: A shimmering visualization of quantum zero-point energy where tiny, ephemeral points of light emerge and vanish in a deep obsidian void; ghostly cyan threads momentarily connect the fluctuating violet excitations, revealing the hidden connectivity of the vacuum.

## spectral_prism

- **Date**: 2026-05-05
- **Theme**: Optical physics, chromatic dispersion, liquid light, beautiful night sky
- **Technique**: Physical Snell's Law refraction, Cauchy's dispersion equation, multi-pass ray tracing (12 wavelengths), HSB-spectral coloring, P2D additive blending, 60fps high-quality MP4 encoding
- **Description**: A rotating obsidian prism catches a beam of intense white starlight and refracts it into a shimmering, fluid fan of spectral colors that sweep across the canvas like a celestial lighthouse beam against a deep star-dusted void.

## ferrofluid_spikes

- **Date**: 2026-05-05
- **Theme**: Magnetic fluids, physical tension, alien architecture, beautiful night sky
- **Technique**: 3D mesh deformation (P3D, 64x64 grid), magnetic field intensity simulation, Lissajous pole paths, multi-source specular lighting, bioluminescent cobalt highlights, 60fps high-quality MP4 encoding
- **Description**: A dark, viscous liquid surface erupts into sharp, rhythmic spikes in response to moving magnetic poles, creating an alien architectural landscape of obsidian and electric cobalt under a star-dusted night sky.

## differential_expansion

- **Date**: 2026-05-05
- **Theme**: Organic morphogenesis, brain-like folding, cellular growth, beautiful night sky
- **Technique**: Differential growth algorithm (Verlet nodes), Scipy KDTree spatial repulsion optimization, multi-layered bioluminescent rendering (Emerald/Seafoam/Cyan), additive blending, 60fps high-quality MP4 encoding
- **Description**: An organic, brain-like structure that folds and expands through a differential growth algorithm, creating an intricate bioluminescent tapestry of seafoam and cyan energy against a deep oceanic void.

## harmonic_levitation

- **Date**: 2026-05-05
- **Theme**: Resonant assembly, acoustic trapping, celestial geometry, beautiful night sky
- **Technique**: Dynamic multi-source wave interference field (8 oscillators), gradient-based particle advection (60,000 particles), HSB-spectral energy mapping, dense starfield with twinkle effect, 60fps high-quality MP4 encoding
- **Description**: An intricate visualization of matter responding to invisible resonant frequencies; 60,000 particles of light navigate a dynamic wave field, assembling into shimmering geometric nodes that morph and pulse as the frequencies shift, creating a delicate, celestial dance against a deep star-dusted void.

## strange_attractor_dust

- **Date**: 2026-05-05
- **Theme**: Chaos theory, strange attractors, butterfly nebula, beautiful night sky
- **Technique**: Lorenz attractor simulation (120k particles), vectorized numerical integration, high-performance 2D histogram density accumulation, gamma-corrected density mapping, radius-based spectral color interpolation
- **Description**: A dense, swirling vortex of electric violet and crimson stardust that forms a complex, heart-like shell within the obsidian void; the work utilizes 120,000 particles to trace the chaotic yet ordered trajectories of the Lorenz attractor, revealing a luminous, silken nebula that pulses with a hidden mathematical intensity.

## metabolic_rhizome

- **Date**: 2026-05-05
- **Theme**: Organic growth, cosmic connectivity, rhizomatic systems, beautiful night sky
- **Technique**: Space-colonization algorithm (nutrient-driven growth), multi-root initialization, adaptive path thickness (flow-based scaling), bioluminescent teal/violet shading, additive junction highlights
- **Description**: A delicate, glowing web of energy that branches and weaves through a deep star-dusted void; using a space-colonization algorithm, the network self-organizes into an optimized transport system that pulses with bio-phosphor teal and neural violet, revealing the organic, interconnected nature of the cosmic vacuum.

## stellar_caustics

- **Date**: 2026-05-05
- **Theme**: Interstellar gas, light refraction, caustics, beautiful night sky
- **Technique**: Multi-wave superposition (18-fold), turbulence-driven grid distortion, non-linear contrast sharpening, additive solar flare highlights
- **Description**: A luminous, shimmering web of light that feels liquid and alive, pulsing with electric teal and solar amber highlights; the work simulates the complex refraction of starlight through a turbulent interstellar medium, revealing an intricate tapestry of energy against a deep indigo void.

## quasicrystal_void

- **Date**: 2026-05-05
- **Theme**: Aperiodic resonance, cosmic order, quantum vacuum, beautiful night sky
- **Technique**: Quasicrystal wave interference (7-fold plane wave summation), vectorized NumPy field rendering, iridescent multi-stop color mapping, additive focal glows, high-density starfield
- **Description**: An intricate, shimmering field of aperiodic energy that pulses through a deep star-dusted void; the complex interference of 7 plane waves creates an iridescent tapestry of royal amethyst, electric cyan, and stellar gold that never repeats, revealing the hidden mathematical architecture of the vacuum.

## gravitational_warp

- **Date**: 2026-05-05
- **Theme**: Space-time curvature, gravitational lensing, cosmic void, beautiful night sky
- **Technique**: Multi-pass conformal coordinate warping (inverse-square lensing approximation), dual-pass additive sapphire/silver grid rendering, distorted Einstein rings, chromatic aberration (spatial color split), high-density multi-magnitude starfield
- **Description**: A stunning visualization of space-time distortion where the underlying geometric fabric of the universe is warped by four massive, invisible singularities; shimmering silver grid lines bend and arc around luminous sapphire focal points, creating complex "Einstein rings" and delicate spectral fringes that pulse with an ethereal intensity against a deep, star-dusted midnight navy void.

## stochastic_nebula

- **Date**: 2026-05-05
- **Theme**: Cosmic gas clouds, stochastic flow, celestial textures, beautiful night sky
- **Technique**: Langevin dynamics simulation, 90,000-particle vectorized flow, pre-computed 512x512 noise-potential grid, additive blending with slow background decay, multi-scale starfield generation
- **Description**: A vast, shimmering celestial nursery where intricate filaments of light weave through a deep midnight void; using Langevin dynamics and a complex noise-potential field, 90,000 particles of electric cyan, amethyst, and rose gold accumulate into organic, smoky nebula structures that glow with a soft, ethereal light amidst a dense, multi-magnitude starfield.

## prismatic_architecture

- **Date**: 2026-05-05
- **Theme**: Digital brutalism, spectral refraction, modern urbanism, beautiful night sky
- **Technique**: 3D recursive quadtree subdivision, isometric camera projection, spectral "refraction" fringe rendering, transparent "glass" box geometry
- **Description**: A vast, shimmering digital metropolis of glass-like buildings that appears to pulse with light; the architectural slabs of the 5-level recursive city feature spectral cyan and magenta fringes that simulate optical refraction against a deep star-dusted midnight void.

## prismatic_vortices

- **Date**: 2026-05-05
- **Theme**: Fluid dynamics, spectral turbulence, liquid light, beautiful night sky
- **Technique**: Vectorized 60,000-particle advection, Kármán vortex street simulation, triple-pass prismatic RGB rendering, persistent silken trace accumulation
- **Description**: A mesmerizing, shimmering flow of silken light that curls into intricate spectral vortices; as 60,000 particles navigate invisible oscillating obstacles, they create rhythmic, prismatic swirls of electric cyan, laser pink, and golden amber against a deep star-dusted midnight void.

## nebular_ribbons

- **Date**: 2026-05-05
- **Theme**: Celestial ribbons, silken energy, cosmic dance, beautiful night sky
- **Technique**: 3D `TRIANGLE_STRIP` ribbon sheets, multi-octave Simplex noise pathfinding, shimmering width modulation, persistent spectral trails, additive P3D blending
- **Description**: A graceful, shimmering dance of 14 silken energy ribbons that twist and turn through a deep space void; the iridescent sheets in teal, lavender, and rose gold leave glowing spectral echoes as they navigate the star-dusted night sky, pulsing with a rhythmic cosmic breath.

## chromatic_refraction

- **Date**: 2026-05-05
- **Theme**: Optical physics, spectral distortion, cosmic lens, beautiful night sky
- **Technique**: Triple-pass RGB chromatic aberration, multi-octave Simplex noise distortion field, convex lens magnification logic, Gaussian nebula bloom rendering
- **Description**: A shimmering, iridescent "cosmic lens" that warps the star-dusted night sky; as the background starfield passes through the central 15,000-point distortion field, it refracts into vibrant spectral arcs of electric cyan, magenta, and yellow, creating a sense of immense depth and optical complexity in the silent obsidian void.

## supersymmetric_manifold_v2

- **Date**: 2026-05-05
- **Theme**: High-dimensional resonance, spectral motion, supersymmetric breath, beautiful night sky
- **Technique**: Animated Gielis Superformula (P3D), dynamic parameter modulation, persistent spectral trails, 60fps high-quality MP4 encoding
- **Description**: An animated evolution of the `supersymmetric_manifold`, responding to user feedback for a motion version; the shimmering energy manifold pulses and rotates through a deep star-dusted void, with its 8 spectral shells breathing in a complex, rhythmic harmony of electric indigo, cyan, and magenta.

## nebular_loom

- **Date**: 2026-05-05
- **Theme**: Celestial weaving, interstellar threads, cosmic tapestry, beautiful night sky
- **Technique**: Vectorized 50,000-particle advection, harmonic "weaver star" attractors, persistent silken trace accumulation, high-density multi-hue starfield
- **Description**: An intricate, shimmering tapestry of light that appears to be woven by the movement of six "weaver stars" across the cosmos; the 50,000 silken filaments in electric indigo, cobalt, and rose gold create a dense, iridescent fabric that pulses against a deep star-dusted midnight void.

## gasket_metropolis

- **Date**: 2026-05-05
- **Theme**: Fractal urbanism, infinite density, modern city feel, beautiful night sky
- **Technique**: Recursive circle subdivision, 3D isometric building extrusion (P3D), Curvature-based height modulation, Neon spectral lighting
- **Description**: A dense, shimmering metropolis of circular skyscrapers that recedes into infinite fractal detail; the buildings glow with electric blue and laser pink neon highlights, creating a vibrant geometric landscape under a silent, star-dusted midnight sky.

## magnetic_reconnection

- **Date**: 2026-05-05
- **Theme**: Solar physics, plasma energy, magnetic snap, beautiful night sky
- **Technique**: Vectorized 50,000-particle advection, dynamic multi-pole magnetic field reconnection, kinetic energy spectral mapping, high-density starfield rendering
- **Description**: An intricate visualization of solar magnetic physics where 50,000 silken filaments trace the invisible architecture of a multi-pole magnetic field; periodic "reconnection" events send shimmering shockwaves of molten gold and stark white light through the deep star-dusted indigo void.

## algorithmic_crystals

- **Date**: 2026-05-05
- **Theme**: Digital mineralization, recursive lattices, geometric resonance, beautiful night sky
- **Technique**: 3D recursive lattice growth (P3D), iridescent surface mapping, luminous internal glow, high-density starfield rendering
- **Description**: An intricate visualization of synthetic mineralization where glowing digital geodes in molten gold, cyber lime, and royal amethyst pulse and divide in a deep void; the shimmering celestial tapestry of geometric resonance pulses with a rhythmic harmony against a star-dusted midnight sky.

## spectral_mitosis

- **Date**: 2026-05-05
- **Theme**: Synthetic biology, membrane dynamics, information splitting, beautiful night sky
- **Technique**: Stochastic cell simulation (P2D), iridescent membrane oscillation, spectral mitosis bursts, high-density starfield rendering
- **Description**: An intricate visualization of synthetic biological growth where glowing organic forms in electric cyan and cyber magenta pulse and divide in a deep void; the shimmering celestial tapestry of mitosis events pulses with a rhythmic harmony against a star-dusted midnight sky.

## metabolic_nodes

- **Date**: 2026-05-05
- **Theme**: Living networks, organic computation, synthetic synapse, beautiful night sky
- **Technique**: 3D stochastic network construction (P3D), luminous pulse propagation, dynamic node resonance, high-density starfield rendering
- **Description**: An intricate visualization of a living digital network that pulses and breathes in a deep void; glowing cyber lime and royal amethyst pulses travel through dense architectural synapses against a star-dusted midnight sky.

## quantum_entanglement

- **Date**: 2026-05-05
- **Theme**: Non-local connection, particle pairs, spectral resonance, beautiful night sky
- **Technique**: Entangled particle simulation (P2D), spectral connection bridges, phase-locked harmonic pulsing, noise-driven correlation
- **Description**: An intricate visualization of quantum coherence where glowing spectral bridges in electric cyan, cobalt, and rose-gold connect entangled particle pairs; the shimmering celestial tapestry pulses with a rhythmic harmony against a star-dusted midnight void.

## algorithmic_architecture

- **Date**: 2026-05-05
- **Theme**: Recursive urbanism, digital metabolism, synthetic metropolis, beautiful night sky
- **Technique**: 3D recursive quadtree construction (P3D), luminous data highways, dynamic camera rotation, high-density starfield rendering
- **Description**: A vast, shimmering digital metropolis generated by 3D recursive quadtree subdivision that appears to pulse with life; glowing electric cyan and royal amethyst data highways flow across dense architectural forms against a star-dusted midnight sky.

## algorithmic_fluid

- **Date**: 2026-05-05
- **Theme**: Digital liquid, spectral flow, viscous light, beautiful night sky
- **Technique**: Grid-based fluid simulation (P2D), spectral dye advection, velocity-based HSB mapping, high-density starfield rendering
- **Description**: A shimmering, viscous flow of spectral light where electric cyan and royal amethyst dyes swirl and mix in a deep void; the intricate, fluid tapestry of geometric resonance pulses with a rhythmic harmony against a star-dusted midnight sky.

## prismatic_resonator

- **Date**: 2026-05-05
- **Theme**: Optical physics, spectral refraction, geometric resonance, beautiful night sky
- **Technique**: Recursive ray-tracing (P2D), chromatic dispersion simulation, high-persistence path accumulation, additive bloom rendering
- **Description**: An intricate visualization of optical resonance where shimmering spectral rays in electric cyan, cobalt, and amethyst bounce and refract inside a circular resonator; the build-up of silken, thread-like patterns pulses with a geometric harmony against a star-dusted midnight void.

## recursive_membranes

- **Date**: 2026-05-05
- **Theme**: Dimensional folding, iridescent surfaces, organic geometry, beautiful night sky
- **Technique**: 3D noise-warped mesh (P3D), height-based HSB iridescence mapping, translucent layering, dynamic camera rotation, high-density starfield
- **Description**: A shimmering, translucent veil of light that folds and pulses in a deep void; the noise-warped membranes in electric cyan and royal amethyst create an intricate, pearlescent tapestry of geometric resonance under a silent, star-dusted midnight sky.

## stellar_clockwork

- **Date**: 2026-05-05
- **Theme**: Orbital resonance, astronomical instruments, temporal harmony, beautiful night sky
- **Technique**: Nested epicyclic tracers (P2D), harmonic resonance tuning, high-persistence trace accumulation, spectral metal coloring (Gold/Silver/Copper)
- **Description**: An intricate visualization of celestial mechanics where nested golden and silver epicycles weave a complex, shimmering tapestry of orbital paths; the build-up of silken, thread-like textures pulses with a temporal harmony against a star-dusted midnight void.

## metabolic_landscape

- **Date**: 2026-05-05
- **Theme**: Living geography, organic terrain, pulsating resonance, beautiful night sky
- **Technique**: 3D domain-warped mesh (P3D), metabolic contour pulse modulation, dynamic camera rotation, high-density starfield rendering
- **Description**: A vast, dark planetary landscape generated by second-order domain warping that appears to breathe; shimmering neon emerald and electric amethyst contours pulse across organic ridges and valleys against a star-dusted midnight sky.

## spectral_coral

- **Date**: 2026-05-05
- **Theme**: Synthetic marine life, metabolic light, crystalline coral, beautiful night sky
- **Technique**: Stochastic branching growth, metabolic spectral pulse modulation, recursive fractal geometry, additive bloom rendering
- **Description**: An intricate visualization of "spectral coral" structures that grow and pulse in a dark void; the crystalline branches in slate and graphite shimmer with rhythmic pulses of electric cyan, cyber lime, and amethyst against a star-dusted night sky.

## quantum_chromatics

- **Date**: 2026-05-05
- **Theme**: Particle collisions, high-energy resonance, magnetic curvature, beautiful night sky
- **Technique**: Lorentz-force path simulation, stochastic collision fragmentation (5,000 particles), spectral decay mapping (White-Gold to Cyan/Magenta), high-density starfield rendering
- **Description**: A high-energy visualization of quantum collisions where rhythmic bursts of 5,000 white-gold fragments shard into curved filaments of electric cyan and magenta; the shimmering spectral decay creates a vibrant, high-energy "sparkler" effect against a silent, star-dusted night sky.

## quantum_vorticity

- **Date**: 2026-05-05
- **Theme**: Superfluid turbulence, quantized vortices, liquid light, beautiful night sky
- **Technique**: Vectorized 30,000-particle advection along point-vortex velocity fields (Biot-Savart law), HSB spectral mapping, high-density starfield rendering
- **Description**: A shimmering visualization of quantum turbulence where 30,000 silken filaments in electric cyan, royal amethyst, and gold swirl around invisible singularities; the intricate tapestry of phase-space resonance pulses against a darkest indigo midnight void.

## luminous_strata

- **Date**: 2026-05-05
- **Theme**: Geological history, layered resonance, mineral light, beautiful night sky
- **Technique**: Stacked noise-driven ridges (P2D), spectral edge highlighting, mineral texture mapping (Simplex noise), high-density starfield rendering
- **Description**: A shimmering visualization of geological strata where 12 noise-driven layers stack to create a rich, mineral-like landscape; the glowing ridges in emerald, amethyst, and molten gold pulse with a rhythmic planetary resonance against a deep star-dusted midnight void.

## metabolic_voxels

- **Date**: 2026-05-05
- **Theme**: Living architecture, geometric metabolism, digital growth, beautiful night sky
- **Technique**: 3D recursive growth (P3D), spectral edge highlighting, animated "breathing" scale, dynamic camera rotation, high-density starfield
- **Description**: A vast, dark space filled with massive, glowing 3D monoliths that grow and breathe like synthetic corals; the recursive structures in slate and graphite pulse with electric cyan and amethyst highlights against a star-dusted midnight void.

## data_metropolis

- **Date**: 2026-05-05
- **Theme**: Digital urbanism, data flow, quantum connectivity, beautiful night sky
- **Technique**: Recursive quadtree subdivision, isometric building projection, Manhattan-grid particle advection (data packets), spectral edge highlighting
- **Description**: A top-down isometric view of a digital metropolis where luminous data packets in laser pink, cyber lime, and electric blue surge through a complex geometric grid; the architectural slabs of the city pulse with neon light against a star-dusted night sky.

## spectral_filaments

- **Date**: 2026-05-05
- **Theme**: Magnetic resonance, plasma loops, interstellar filaments, beautiful night sky
- **Technique**: Vectorized 40,000-particle advection along rotating dipole fields ($B \propto r^{-2}$), HSB spectral mapping (Emerald/Gold/Cobalt), high-density starfield rendering
- **Description**: A dense, intricate web of 40,000 silken filaments that trace the invisible magnetic architecture of the cosmos; the glowing threads in deep emerald, molten gold, and electric cobalt swirl and resonate against a deep star-dusted navy void.

## tectonic_glow

- **Date**: 2026-05-05
- **Theme**: Planetary stress, seismic energy, crustal fractures, beautiful night sky
- **Technique**: Dynamic proximity mesh, stress-weighted spectral coloring, midpoint-displaced quadratic "cracks", noise-driven drift simulation
- **Description**: A dark, planetary landscape where shifting tectonic plates create glowing fractures of molten gold and electric magenta; the jagged spectral cracks pulse with subterranean energy against a deep star-dusted night sky.

## gravitational_echoes

- **Date**: 2026-05-05
- **Theme**: Gravitational waves, binary merger, spacetime distortion, beautiful night sky
- **Technique**: Phase-space wave superposition, chirping orbital emitters, subpixel starfield distortion (lensing simulation), additive interference rendering
- **Description**: A rhythmic, shimmering visualization of a binary merger where expanding wave-fronts of electric cyan and royal amethyst interfere to create complex spectral fringes; the background starfield is dynamically warped by the passing gravitational waves, culminating in a bright white-gold flash at the center of the obsidian void.

## gluon_flux

- **Date**: 2026-05-05
- **Theme**: Subatomic physics, particle confinement, energetic tension, beautiful night sky
- **Technique**: Force-directed lattice with confinement spring logic ($F \propto r$), additive spectral bloom, high-density starfield rendering, animated tension-weighted edge modulation
- **Description**: A dense, vibrating web of "quarks" held together by shimmering "gluon flux tubes" in electric magenta, lime, and cobalt; as the particles drift apart, the tension-weighted connections flare with white-gold energy, creating a complex, high-energy lattice against a deep star-dusted night sky.

## recursive_interference

- **Date**: 2026-05-04
- **Theme**: Recursive physics, multi-scale interference, digital optics, complex resonance
- **Technique**: Quadtree subdivision driven by moving noise, persistent PGraphics accumulation for temporal glow, triple-shard interference emission, additive spectral highlights
- **Logic Lab Reference**: `fractals/quadtree_part_1/quadtree_part_1.py`, `physics/additive_wave/additive_wave.py`
- **Description**: An incredibly dense, shimmering tapestry of light fringes where the frequency and density of wave emitters are determined by a recursive quadtree; the result is a multi-scale interference field that pulses with organic-yet-digital life against a deep navy night.

## harmonic_vibrance

- **Date**: 2026-05-04
- **Theme**: Harmonic resonance, celestial mechanics, elastic geometry, beautiful night sky
- **Technique**: Concentric Verlet-integrated elastic rings, multi-emitter harmonic wave interference, PGraphics persistent trail accumulation, additive spectral bloom
- **Logic Lab Reference**: `physics/spring_mesh/spring_mesh.py`, `physics/additive_wave/additive_wave.py`
- **Description**: A series of shimmering, elastic geometric rings vibrate and pulse in response to complex harmonic wave interference; the concentric layers of electric cyan, amethyst, and amber leave persistent spectral trails as they resonate against a vast, star-dusted obsidian void.

## fractal_currents

- **Date**: 2026-05-04
- **Theme**: Mathematical fluidity, fractal advection, complex dynamics, beautiful night sky
- **Technique**: Julia-set driven flow field, vectorized particle advection (NumPy), HSB phase-to-hue mapping, atmospheric starfield rendering
- **Description**: A swirling, intricate sea of 40,000 particles flows along the complex-gradient of a Julia Set; the dense iridescent currents in electric teal and soft rose navigate the infinite recursive boundaries of the fractal against a deep star-dusted night sky.

## quantum_entanglement

- **Date**: 2026-05-04
- **Theme**: Quantum physics, entanglement, non-locality, symmetrical energy, beautiful night sky
- **Technique**: Symmetrical mirrored particle systems, stochastic decoherence noise, persistence buffer trails, atmospheric starfield rendering
- **Description**: Two shimmering particle systems in electric cyan and vibrant magenta dance in perfect synchronization across a central void; ghostly white threads connect the entangled pairs, while subtle decoherence noise and long-exposure trails create a sense of invisible connection and rhythmic harmony against a star-dusted night sky.

## magnetic_topography

- **Date**: 2026-05-04
- **Theme**: Hidden magnetic fields, topographical abstraction, energy maps, beautiful night sky
- **Technique**: Magnetic dipole field synthesis, Marching Squares contour extraction, HSB spectral mapping, atmospheric starfield rendering
- **Description**: A dense, shimmering topographical map of magnetic energy where hundreds of flowing lines swirl and converge around invisible dipoles; the colors transition from deep teal to molten copper against a silent, star-dusted charcoal void.

## resonant_void

- **Date**: 2026-05-04
- **Theme**: Cosmic resonance, gravitational waves, shimmering energy, beautiful night sky
- **Technique**: 3D harmonic mesh deformation (P3D), multi-frequency sine superposition, HSB spectral mapping, atmospheric starfield rendering
- **Description**: A central, vibrating energy membrane pulses with multiple overlapping harmonic frequencies in a deep star-dusted void; the shimmering surface shifts between electric cyan and royal amethyst, leaving glowing spectral echoes as it rotates through the silent indigo sky.

## hexagonal_fractalopolis

- **Date**: 2026-05-04
- **Theme**: Non-Euclidean urbanism, fractal infrastructure, modern architectural twist, beautiful night sky
- **Technique**: IH02 Isohedral tiling (TV08 model), recursive Koch curve subdivision, 3D monolithic height modulation (P3D), atmospheric bloom rendering
- **Logic Lab Reference**: `tiling_patterns/ih02_tv08_koch/ih02_tv08_koch.py`
- **Description**: A dense, shimmering landscape of fractal buildings that sprawl across a non-Euclidean hexagonal grid; every structure is defined by recursive Koch edges, creating a "gear-like" architectural complexity that pulses with neon highlights against a deep star-dusted night sky.

## supersymmetric_manifold

- **Date**: 2026-05-04
- **Theme**: High-dimensional geometry, spectral resonance, beautiful night sky
- **Technique**: Layered Gielis Superformula, second-order domain warping, persistence-buffer trail accumulation, Retina-aware pixel-buffer compositing
- **Logic Lab Reference**: `mathematical/superformula/superformula.py`
- **Description**: A shimmering, iridescent manifold of violet and cyan energy threads that pulses and vibrates in a deep star-dusted void; the complex geometric layers flow with a rhythmic "supersymmetric" breath, leaving glowing spectral echoes in their wake.

## metabolic_growth

- **Date**: 2026-05-04
- **Theme**: Algorithmic botany, synthetic life, metabolic pulse, modern twist
- **Technique**: 3D L-System branching, recursive depth modulation, glowing branch gradients, wireframe perspective grid
- **Logic Lab Reference**: `fractals/l_system/l_system.py`
- **Description**: A complex, glowing 3D organism grows from a dark wireframe grid; violet and cyan branches pulse with a rhythmic algorithmic breath, while terminal nodes flicker with spectral light against a deep star-dusted void.

## synthetic_aurora

- **Date**: 2026-05-04
- **Theme**: Atmospheric phenomena, digital beauty, spectral currents, beautiful night sky
- **Technique**: Noise-driven vertical Bezier curtains, chromatic aberration (RGB spatial split), persistence-buffer trail accumulation, additive P2D blending
- **Logic Lab Reference**: `physics/additive_wave/additive_wave.py`, `physics/perlin_noise_walker_lines/perlin_noise_walker_lines.py`
- **Description**: A digital reimagining of the Northern Lights where algorithmic curtains of light shimmer with iridescent chromatic fringes; deep emerald, cyan, and electric pink currents wave across a dark star-dusted void, leaving glowing spectral echoes in their wake.

## stellar_equilibrium

- **Date**: 2026-05-04
- **Theme**: Cosmic energy, physical tension, solar majesty, beautiful night sky
- **Technique**: N-body gravitational simulation, magnetic tension loops (Bezier), noise-driven solar core rendering, persistence-buffer trail accumulation
- **Logic Lab Reference**: `physics/n_body_orbital_simulation/n_body_orbital_simulation.py`, `physics/spring_connection/spring_connection.py`
- **Description**: A massive, pulsing star held in precarious balance between gravitational collapse and magnetic pressure; golden solar prominences surge from the core while violet plasma agents dance in complex orbits against a high-density star-dusted void.

## isohedral_metropolis

- **Date**: 2026-05-04
- **Theme**: Non-Euclidean urbanism, interlocking systems, metabolic pulse, synthetic nature
- **Technique**: IH01 Isohedral tiling, dynamic Bezier deformation, persistence-buffer trail accumulation, high-density starfield rendering
- **Logic Lab Reference**: `tiling_patterns/ih01_deformation/ih01_deformation.py`
- **Description**: A dense, glowing metropolis defined by complex interlocking "living blocks" that pulse and shift against a deep star-dusted night; luminous conduits in cyan and magenta trace the shifting boundaries, while golden data hubs flicker at the intersections of the metabolic grid.

## spectral_currents

- **Date**: 2026-05-04
- **Theme**: Fluidic light, spectral advection, luminous currents, silken motion
- **Technique**: Perlin/Simplex noise vector field, particle advection, accumulation trails, HSB spectral mapping
- **Logic Lab Reference**: `physics/perlin_noise_walker_lines/perlin_noise_walker_lines.py`
- **Description**: A swirling sea of silken light threads that flow and curl through a deep indigo void; thousands of particles leave shimmering iridescent trails, creating a long-exposure effect of bioluminescent fluid motion.

## neural_coral

- **Date**: 2026-05-04
- **Theme**: Biological growth, neural pathways, iridescent calcification
- **Technique**: Gray-Scott Reaction-Diffusion, 3D gradient shading, optimized vectorized simulation, atmospheric bloom
- **Logic Lab Reference**: `physics/reaction_diffusion/reaction_diffusion.py`
- **Description**: A dense, organic maze of coral-like ridges that pulse with light; 3D-like shading and bioluminescent highlights create a sense of deep-sea biological intelligence and intricate natural architecture.

## metabolic_lattice

- **Date**: 2026-05-04
- **Theme**: Kinetic tension, metabolic elasticity, structural vibration, iridescent membranes
- **Technique**: Verlet integration, radial spring mesh, stress-based HSB mapping, atmospheric bloom rendering
- **Logic Lab Reference**: `physics/spring_mesh/spring_mesh.py`
- **Description**: A living, breathing radial lattice of glowing conduits that ripples and shudders under a central metabolic pulse; stress-induced colors shift from deep violet to electric cyan as the structure maintains its precarious equilibrium.

## prismatic_cellularity

- **Date**: 2026-05-04
- **Theme**: Urban metabolism, cellular logic, spectral pressure, modern architectural twist
- **Technique**: Multi-scale Worley noise (L1/L2 hybrid), derivative-based edge detection, HSB spectral mapping, atmospheric haze rendering, optimized NumPy grid-partitioning
- **Logic Lab Reference**: `mathematical/worley_noise/worley_noise.py`
- **Description**: A dense, glowing "cellular metropolis" of blocky, rhythmic structures that pulse and shift against a deep indigo night sky; sharp iridescent edges and soft glowing cores create a sense of operational intelligence and high-tech urban flow.

## entropic_monolith

- **Date**: 2026-05-04
- **Theme**: Digital entropy, decaying geometry, crystalline collapse, monolithic silence
- **Technique**: Recursive geometric polygon fragmentation, stochastic detachment logic, HSB edge-glow simulation, kinematic drift advection
- **Logic Lab Reference**: `mathematical/voronoi/voronoi.py` — used as a conceptual base for spatial partitioning and sharding
- **Description**: A massive, obsidian-like monolith that stands in a pitch-black void, slowly being shattered by invisible entropic forces; hairline cracks of electric cyan appear across its surface as geometric shards break off, drifting away and dissolving into a fine mist of white light.

## interference_topography

- **Date**: 2026-05-04
- **Theme**: Wave mechanics, constructive interference, rhythmic precision, topological light
- **Technique**: High-density vectorized wave interference (10 emitters), contour quantization (18 levels), Lissajous emitter path logic, Retina-aware pixel-buffer compositing
- **Logic Lab Reference**: `physics/fluid_resistance/fluid_resistance.py` — conceptual base for physical field interaction
- **Description**: A dense, vibrating field of sharp geometric contours that ripple outward from multiple moving centers; where the ripples meet, they form intense, glowing "nodes" of gold and cyan light that dance across a dark indigo void.

## liquid_topology

- **Date**: 2026-05-04
- **Theme**: Fluid intelligence, liquid data, topological deformation, metallic reflection
- **Technique**: Multi-octave domain-warped noise terrain, P3D high-density vertex mesh, multi-source specular highlight simulation, viscous motion advection
- **Logic Lab Reference**: `physics/noise_terrain/noise_terrain.py` — used for noise-driven 3D surface generation
- **Description**: A mesmerizing, shimmering field of liquid silver that ripples and flows across the entire canvas; light catches the viscous peaks in electric cyan and deep violet, creating a sense of immense depth and complexity as the topological surface deforms.

## crystalline_bloom

- **Date**: 2026-05-04
- **Theme**: Geometric efflorescence, frozen growth, mineral intelligence
- **Technique**: Fermat spiral (phyllotaxis), recursive polygon subdivision, depth-weighted spectral coloring, animated breathing scaling
- **Logic Lab Reference**: `mathematical/fermat_spiral/fermat_spiral.py` — used for phyllotaxis distribution logic
- **Description**: A complex, multi-layered "mineral bloom" that pulses with cold light; thousands of recursive geometric petals are arranged in a perfect Fermat spiral, shifting between shimmering silver and deep amethyst as the structure breathes and rotates.

## monsoon_circuit

- **Date**: 2026-05-04
- **Theme**: Urban metabolism, torrential data, tropical infrastructure
- **Technique**: Recursive quadtree subdivision, Manhattan-constrained particle flow, Retina-aware pixel-buffer accumulation, chromatic aberration shift
- **Logic Lab Reference**: `fractals/quadtree_part_1/quadtree_part_1.py` — used for recursive subdivision logic
- **Description**: A top-down view of a dense, glowing city grid where luminous rivers of electric teal and neon violet light surge through the streets; brighter pulses flicker at the intersections like rhythmic electronic heartbeats against a deep charcoal background.

## hyperbolic_growth

- **Date**: 2026-05-04
- **Theme**: Non-Euclidean growth, constrained infinity, coral morphology, mathematical lens
- **Technique**: Recursive hyperbolic branching (Poincaré disk model), Mobius coordinate transformation, depth-weighted stochastic jitter, HSB-spectral gradient rendering
- **Logic Lab Reference**: `fractals/stochastic_tree/stochastic_tree.py` — used for recursive branching and stochastic jitter logic
- **Description**: A circular Poincaré disk contains an intricate web of seafoam and amethyst branches that sprout from the center and curve elegantly outward; as they approach the boundary, they become infinitely dense and delicate, accented by golden growth tips against a deep charcoal void.

## algorithmic_brutalism

- **Date**: 2026-05-04
- **Theme**: Industrial logic, brutalist architecture, recursion, monolithic scale
- **Technique**: Animated recursive quadtree subdivision, 3D monolithic slab rendering (P3D), noise-driven height modulation, safety-orange emissive accents, isometric-parallax motion
- **Logic Lab Reference**: `fractals/quadtree_part_1/quadtree_part_1.py` — used for recursive subdivision logic
- **Description**: A stark, shifting landscape of charcoal concrete slabs that subdivide and merge in a rhythmic algorithmic breath; deep shadows and sharp edges emphasize the brutalist scale, while safety-orange pulses reveal the machine-like processing beneath the monolithic surface.

## elastic_residue

- **Date**: 2026-05-04
- **Theme**: Material memory, physical tension, lingering traces, soft-body abstraction
- **Technique**: Verlet cloth simulation (30x30 mesh), persistence-buffer trail accumulation, tension-weighted spectral coloring (Tan→Gold), multi-agent repulsion field
- **Logic Lab Reference**: `research/cloth_simulation/cloth_simulation.py` — used for Verlet integration and constraint satisfaction logic
- **Description**: A luminous web of threads deforms under invisible pressure, leaving a persistent golden record of its peak tension; the dark sienna background holds the "scars" of past movements, creating a complex palimpsest of physical stress and slow recovery.

---

## selection_pressure

- **Date**: 2026-05-04
- **Theme**: Environmental pressure, adaptation, inherited variation, survival memory
- **Technique**: Genetic-algorithm inspired population simulation, selection-weighted reproduction, phenotype mutation, lineage trail rendering, Retina-aware pixel-buffer habitat compositing
- **Logic Lab Reference**: `genetic_algorithms/evolving_bloops/evolving_bloops.py` — used for DNA, mutation, survival, and reproduction structure
- **Description**: A dark habitat field records generations of small abstract phenotypes drifting diagonally through selection pressure; pale moss bodies, muted amber elite rings, and faint extinct variants reveal a population slowly changing shape to survive.

## seismic_tomography

- **Date**: 2026-05-04
- **Theme**: Hidden pressure beneath a surface, measurement, fault memory, geophysical abstraction
- **Technique**: Synthetic seismic velocity-field synthesis, refracted ray tracing, travel-time residual coloring, marching-squares contour extraction, Retina-aware pixel-buffer compositing
- **Description**: A dark subsurface instrument plate is crossed by muted teal and copper ray fans from edge sensors; faint residual contours and a chalk-copper fault trace reveal buried pressure without turning the scene into a literal landscape.

## quantum_lattice

- **Date**: 2026-05-04
- **Theme**: Quantum mechanics, probability fields, entanglement, wave-particle duality
- **Technique**: Complex wave superposition, energy-band quantization, probability-node extraction, optimized pixel-buffer rendering
- **Description**: A vibrant field of shimmering interference fringes where waves of positron pink and electron blue overlap; bright gold quanta emerge at probability peaks against a dark vacuum indigo grid.

## atmospheric_veil

- **Date**: 2026-05-04
- **Theme**: Atmospheric light, noctilucent clouds, twilight, ethereal presence
- **Technique**: Second-order domain warping, fBm noise layers, height-dependent spectral coloring, derivative-based solar edge highlighting
- **Description**: A luminous, shimmering veil of noctilucent clouds ripples across a deep indigo sky; pearlescent silver and electric blue textures catch a faint solar amber glow at their edges against a distant star field.

## flux_lattice

- **Date**: 2026-05-04
- **Theme**: Energy distribution, urban metabolism, hidden currents, systemic flow
- **Technique**: Stochastic lattice routing, pulse-width modulated currents, node-leakage sparks, jittered grid subdivision
- **Description**: A dark, dense network of glowing conduits where "power" surges through neon cobalt trunk lines and gold capillaries, while ghostly magenta sparks reveal high-pressure leakage at the nodes.

## route_arbitration

- **Date**: 2026-05-03
- **Theme**: autonomous negotiation, shared floor, routing pressure, operational intelligence
- **Technique**: Obstacle-field generation, grid shortest-path routing, conflict heat accumulation, reservation tick glyphs
- **Description**: A dark warehouse-like routing map shows steel-blue and green paths threading around matte blockers while amber conflict nodes and white priority markers reveal where autonomous decisions compete for the same floor.

## braid_phase

- **Date**: 2026-05-03
- **Theme**: separate histories, crossing paths, layered memory, mathematical weaving
- **Technique**: Phase-driven strand paths, over-under depth masking, contour-lit strokes, low-contrast phase-field background
- **Description**: Teal, violet, and muted-copper strands cross through a dark interference field in layered over-under rhythms; pale edge highlights mark the moments where one history rises above another.

## redaction_current

- **Date**: 2026-05-03
- **Theme**: censorship, suppressed communication, signal leakage, modern abstraction
- **Technique**: Redaction block field, sinusoidal signal leakage, wake accumulation around barriers, ghost baseline synthesis
- **Description**: A document-like dark field is crossed by hard black redaction bars while cyan currents, magenta edge residue, and muted amber wakes leak around the blocks, suggesting a suppressed message that still carries charge.

## impact_palimpest

- **Date**: 2026-05-03
- **Theme**: repeated collision, regolith memory, natural surface abstraction
- **Technique**: Crater heightfield synthesis, asymmetric rim lighting, ballistic ejecta rays, slope-based relief shading
- **Description**: A dark regolith-like surface is overwritten by overlapping impact bowls, muted copper ejecta rays, cold shadowed basins, and pale worn rims; the image reads as an abstract record of repeated collisions.

## pulsar_cartogram

- **Date**: 2026-05-03
- **Theme**: time signals, deep-space navigation, astronomical instrument record
- **Technique**: Polar pulsar placement, pulse train encoding, barycentric timing arcs, sparse chart grid synthesis
- **Description**: A near-black astronomical cartogram turns rhythmic pulse arrivals into coordinates; cyan tick trains radiate from a central reference while amber timing arcs, rose halos, and faint chart lanes cross the quiet sky.

## lenticular_night

- **Date**: 2026-05-03
- **Theme**: optical surface, hidden images, nocturnal perception, angle-shifted memory
- **Technique**: Phase-shifted lenticular stripe masks, warped layer fields, crisp separator bands, sparse glint synthesis
- **Description**: A dark optical field flickers with cyan, muted rose, and pale-gold fragments revealed through precise slanted seams; multiple hidden layers misregister into a dense full-canvas lenticular surface.

## avalanche_ledger

- **Date**: 2026-05-03
- **Theme**: arithmetic avalanche, computational sediment, collapse record
- **Technique**: Abelian sandpile relaxation, residue-state coloring, logarithmic topple heat layer, nearest-neighbor crisp upscaling
- **Description**: A full-canvas computational avalanche leaves a sharp ledger of teal, mauve, ochre, and pale residues; dense central collapse patterns expand outward into blocky fractal boundaries and audit-like hatching.

## jacobian_drift

- **Date**: 2026-05-03
- **Theme**: invisible pressure, coordinate weather, mathematical deformation
- **Technique**: Nonlinear coordinate warp, finite-difference Jacobian analysis, warped coordinate families, tensor ellipse glyph rendering
- **Description**: A dark indigo coordinate field bends under hidden Gaussian pressure centers; silver-blue warped traces and coral tensor ellipses reveal local stretch, compression, and rotation across the full canvas.

## crease_memory

- **Date**: 2026-05-03
- **Theme**: folded memory, stored pressure, geometric material abstraction
- **Technique**: Signed crease distance fields, procedural origami heightfield, normal-based relief shading, ridge stress highlighting
- **Description**: A dark folded surface fills the canvas with graphite planes, teal incisions, mauve shadows, and copper-white stress ridges; every luminous crease reads as a stored pressure mark in a synthetic material sheet.

## eigenveil

- **Date**: 2026-05-03
- **Theme**: hidden order, woven abstraction, spectral pressure, quiet machinery
- **Technique**: Weighted graph Laplacian eigenmodes, bilinear field expansion, quantized contour threading, gradient-based stress accents
- **Description**: A dark full-canvas veil of teal and violet contour threads reveals hidden mathematical pressure beneath the surface; restrained amber points flicker along steep spectral bends without exposing the underlying graph directly.

## signal_fossil

- **Date**: 2026-05-03
- **Theme**: digital archaeology, damaged broadcast, memory, modern abstraction
- **Technique**: Gabor-like wave packet synthesis, contour quantization, packet dropout masking, additive multi-hue glow
- **Description**: A damaged future signal appears as a luminous fossil excavated from a near-black technological substrate; cyan contour shards, amber stress edges, violet missing-data shadows, and vertical recovery ticks form a full-canvas abstract relic of compressed light.

## kinetic_mandala

- **Date**: 2026-05-03
- **Theme**: sacred geometry, rhythm, symmetry, meditation, kinetic art
- **Technique**: 16-fold rotational symmetry, counter-rotating nested rings, high-density line moiré, additive blending, pulsing scale oscillations
- **Description**: A complex, golden "digital mandala" that breathes and rotates with hypnotic precision; thousands of fine lines in stellar gold and amber overlap to create intricate moiré patterns and glowing energy points in a dark charcoal void.

## neon_gasket

- **Date**: 2026-05-03
- **Theme**: fractal urbanism, cyberpunk, geometry, infinite detail
- **Technique**: Apollonian Gasket (Descartes' Circle Theorem), isometric projection, curvature-based height mapping, neon hexagonal prisms
- **Description**: A dense, fractal metropolis reimagined from the Apollonian Gasket; 800 glowing hexagonal buildings in electric blue, laser pink, and cyber lime are projected isometrically, with tiny needle-like towers pulsing at extreme heights around massive central hubs.

## soft_membranes

- **Date**: 2026-05-03
- **Theme**: organic flow, translucency, bioluminescence, deep sea
- **Technique**: Stacked domain-warped noise layers, alpha accumulation, additive blending, dynamic ribbon geometry
- **Description**: 24 translucent, bioluminescent membranes drift through a dark indigo void; layered noise-driven ribbons in seafoam, rose, and amethyst overlap to create complex prismatic interference and luminous depth, accompanied by drifting marine snow particles.

## urban_pulse

- **Date**: 2026-05-03
- **Theme**: urbanism, connectivity, kinetic energy, modern city, data flow
- **Technique**: Recursive grid subdivision, Manhattan-distance flow field, pulse-modulated particle brightness, architectural window grid synthesis
- **Description**: A top-down "satellite" view of a glowing digital city; 40,000 particles surge through a Manhattan-grid street network in neon cyan and magenta, while flickering window grids in dark blocks create a dense architectural texture synchronized to a global "pulse" heartbeat.

## lissajous_web

- **Date**: 2026-04-25
- **Theme**: harmonic mathematics, signal, parametric curves
- **Technique**: Lissajous figures (multiple frequency-ratio pairs), direct vertex stroke rendering, layered alpha compositing
- **Description**: 24 Lissajous figures with frequency ratios from 1:2 to 7:11 overlaid in distinct hues; boundary accumulations form a glowing frame and interior crossings encode harmonic relationships

## truchet_tiles

- **Date**: 2026-04-25
- **Theme**: algorithmic tiling, geometry, emergence
- **Technique**: Truchet quarter-circle arc tiling, binary random orientation, two-color complementary palette
- **Description**: 576 tiles each randomly assigned one of two arc orientations; arcs connect seamlessly at boundaries producing emergent S-curves, loops, and wave trains in rose-coral and cyan-teal on black

## contour_field

- **Date**: 2026-04-25
- **Theme**: abstract cartography, landscape, topology
- **Technique**: 2D FFT spectral terrain synthesis (1/f² power spectrum), topographic contour band coloring
- **Description**: Fractal terrain field via inverse FFT rendered as 14 colorful topographic contour bands with sharp dark borders; organic hills unique to every run

## cellular_automaton

- **Date**: 2026-04-25
- **Theme**: computation, fractal, emergence from simple rules
- **Technique**: Wolfram Rule 90 elementary cellular automaton, single-cell seed, generation-depth HSV gradient
- **Description**: Rule 90 evolved 540 generations from one center cell produces the Sierpinski triangle; amber-to-violet gradient encodes computational time as color

## cellular_automata

- **Date**: 2026-04-29
- **Theme**: computation, emergence, probabilistic systems, organic growth
- **Technique**: Probabilistic cellular automaton with density-based coloring, age-based color transitions, multiple seed clusters
- **Description**: 12 random seed clusters evolve through 180 generations using probabilistic survival/birth rules; magenta→teal→purple age gradient with golden density highlights creates organic cellular patterns against deep midnight

## modulo_circles

- **Date**: 2026-04-25
- **Theme**: number theory, abstract geometry, mathematical visualization
- **Technique**: modular arithmetic chord connections, envelope curves, layered transparency
- **Description**: 300 circle points connected by chords via six multipliers (M=2,3,5,7,13,51); chord envelopes form cardioid, nephroid, and star-polygon families in distinct hues

## domain_warp

- **Date**: 2026-04-25
- **Theme**: pure abstraction, mathematics, generative color
- **Technique**: iterative domain warping, multi-chain coordinate distortion, harmonic sampling, numpy vectorization
- **Description**: Three independent warp chains distort a 2D field through layered sine/cosine transformations; randomized parameters produce a unique abstract color swirl on every run

## lsystem_tree

- **Date**: 2026-04-25
- **Theme**: nature, botany, recursion
- **Technique**: stochastic recursive fractal branching, depth-based color/thickness taper
- **Description**: 11-level stochastic fractal tree with random angle jitter at each fork; sienna trunk transitions to sage-gold tips against a deep indigo gradient sky

## voronoi_cells

- **Date**: 2026-04-25
- **Theme**: geometry, organic structure, spatial partitioning
- **Technique**: Voronoi tessellation, banded numpy distance fields, center-glow gradient, earth-tone palette
- **Description**: 220 seed points partition the canvas into warm-toned Voronoi polygons with exponential center glow and sharp geometric borders, evoking stained glass and biological tissue

## flow_field

- **Date**: 2026-04-25
- **Theme**: fluid dynamics, emergence, field theory
- **Technique**: particle system, noise-based vector field, trail accumulation, log-scale tone mapping
- **Description**: 80k particles following a multi-frequency sine/cosine vector field, converging onto emergent closed-loop orbits that trace luminous stream lines on black

## julia_set

- **Date**: 2026-04-25
- **Theme**: mathematics, complex dynamics, fractal geometry
- **Technique**: Julia set iteration, smooth escape-time coloring, numpy vectorization
- **Description**: Douady rabbit Julia set rendered with smooth coloring; intricate spiral dendrites mark the boundary between bounded and unbounded complex orbits

## reaction_diffusion

- **Date**: 2026-04-25
- **Theme**: biology, emergence, self-organization
- **Technique**: Gray-Scott reaction-diffusion PDE, numpy simulation, 2000 steps
- **Description**: Labyrinthine floral clusters formed by two interacting virtual chemicals, resembling coral or animal markings

## wave_interference

- **Date**: 2026-04-25
- **Theme**: physics, wave phenomena
- **Technique**: wave superposition, analytical computation, numpy vectorization
- **Description**: Nine wave sources superimposed to form a standing wave interference pattern with yellow constructive nodes on a blue field

## clifford_attractor

- **Date**: 2026-04-25
- **Theme**: chaos theory, mathematics
- **Technique**: strange attractor, vectorized multi-trajectory, density accumulation, log-scale mapping
- **Description**: Two million points tracing a Clifford attractor, rendered as a density field with an amber glow on black

## newton_fractal

- **Date**: 2026-04-25
- **Theme**: mathematics, complex dynamics, numerical analysis
- **Technique**: Newton-Raphson iteration on z⁵−1, basin-of-convergence coloring, convergence-speed brightness mapping
- **Description**: Five colored basins separate the complex plane into regions converging to each fifth-root of unity; the fractal Julia-set boundary between basins traces dark lace of infinite detail

## boid_flock

- **Date**: 2026-04-25
- **Theme**: emergence, swarm intelligence, organic motion
- **Technique**: Reynolds boid rules (separation/alignment/cohesion), vectorized numpy physics, heading-based HSV color, circular trail buffer
- **Description**: 300 boids forming emergent flocks; heading-angle coloring makes each flock a coherent color ribbon; 50-frame trails trace swooping collective paths as brush-stroke formations on black

## fourier_epicycles

- **Date**: 2026-05-03 (Polished)
- **Theme**: mathematics, Fourier analysis, Iridescent Cosmos, spectral harmonics
- **Technique**: Fourier epicycles (15 nested rotating circles), single-chain trace, multi-stop iridescent color gradient, enhanced glow effects
- **Description**: A complex chain of 15 rotating epicycles traces a vibrant, iridescent path across a deep space background; the multi-stop spectral gradient and enhanced glow transform the mechanical trace into a rhythmic, celestial light display.

## shell_spiral

- **Date**: 2026-04-26
- **Theme**: nature, biology, mathematics, growth, logarithmic spiral
- **Technique**: Moseley's logarithmic spiral model, chamber segmentation, age-based radial shading
- **Description**: Nautilus shell cross-section rendered via r=r₀·eᵇᶿ with 4.5 whorls and 32 chambers delimited by septa; ivory outer whorls shade to dark ochre at the columella center

## chladni_figures

- **Date**: 2026-04-26
- **Theme**: physics, acoustics, resonance, standing waves
- **Technique**: superposed square-plate vibrational modes, nodal-zone threshold coloring, smooth density gradient
- **Description**: Five vibrational modes of a square plate superimposed; sand accumulates at the nodal lines (|f| < threshold) revealing the hidden geometry of resonance as organic looping cream patterns on dark felt

## sphere_world

- **Date**: 2026-04-26
- **Theme**: space, astronomy, 3D rendering, procedural terrain
- **Technique**: ray-sphere intersection, Lambertian shading, 7-octave fBm terrain, atmospheric limb scattering
- **Description**: Analytic ray-sphere rendering with multi-octave noise terrain colored by elevation (ocean to snow); atmospheric blue glow at the limb and stars in the background create a convincing distant-planet scene

## phyllotaxis

- **Date**: 2026-04-26
- **Theme**: botany, mathematics, golden ratio, nature's geometry
- **Technique**: Vogel's phyllotaxis formula, golden angle seed placement, radial color/size encoding
- **Description**: 8500 seed discs placed at golden angle intervals with √n radial spacing; Fibonacci spiral families (34 and 55 arms) emerge as an optical effect from the irrational angle; amber→gold→cream radial gradient encodes seed age

## magnetic_field

- **Date**: 2026-04-26
- **Theme**: physics, electromagnetism, invisible forces, streamlines
- **Technique**: Euler streamline integration of analytic dipole field, color-encoded pole polarity
- **Description**: 72 field lines seeded at uniform angles from the N pole and integrated through a two-pole dipole field; N→S connecting lines rendered with warm-red→cold-blue gradient; escaping lines appear as dim peripheral arcs

## lorenz_attractor

- **Date**: 2026-04-26
- **Theme**: chaos theory, physics, meteorology, strange attractor
- **Technique**: RK4 ODE integration, 800 parallel trajectories, density accumulation, log tone mapping
- **Description**: 20 million trajectory points traced through the Lorenz convection system projected onto the (x,z) plane; density accumulation reveals the twin-lobed butterfly with dark hollow cores and warm amber density gradient

## dla_lightning

- **Date**: 2026-04-26
- **Theme**: electricity, physics, branching fractal, nature
- **Technique**: midpoint displacement fractal with stochastic branching, numpy glow accumulation, log-scale tone mapping
- **Description**: A single lightning bolt rendered via recursive midpoint displacement — each segment splits at a randomly displaced midpoint, spawning side branches with depth-weighted probability; depth encodes color from near-white core to dim steel-blue tips

## aurora_borealis

- **Date**: 2026-04-26
- **Theme**: atmosphere, polar light, electromagnetism, landscape
- **Technique**: layered vertical ribbon waves (180 columns × 5 phases), alpha accumulation, star scatter, tree silhouette
- **Description**: 900 sine-wave ribbon strips in five overlapping layers form the characteristic waviness of the Northern Lights; horizontal gradient from electric green through cold teal to deep violet encodes the spectral emission bands of excited atmospheric gases above a conifer treeline

## woven_fabric

- **Date**: 2026-04-26
- **Theme**: textile, crafts, mathematics, pattern, Jacquard weaving
- **Technique**: per-pixel thread classification via modular arithmetic, sinusoidal weave matrix, 1px dark-edge shading for 3-D thread relief
- **Description**: Sienna warp and indigo weft threads interlace under control of a sine-cosine weave matrix; large-scale flowing organic patterns emerge from the mathematical weave function while the cloth texture remains visible throughout

## rossler_attractor

- **Date**: 2026-04-26
- **Theme**: chaos theory, mathematics, physics, strange attractor
- **Technique**: vectorised RK4 ODE (250 trajectories × 35k steps), z-height split into 3 density layers, additive colour compositing violet→teal→gold, log tone mapping
- **Description**: The Rössler chaotic system rendered with z-height coloring; the spiral body glows violet, the snap-back fold burns gold, revealing the 3D fold structure in a (x,y) projection with depth as color

## hilbert_curve

- **Date**: 2026-04-26
- **Theme**: mathematics, space-filling curves, topology, self-similarity
- **Technique**: vectorised d→(x,y) Hilbert bit-pair mapping, 256×256 cell grid, cyclic 3-stop palette (20 cycles) reveals winding structure
- **Description**: Order-8 Hilbert curve with 65536 cells; a cyclic indigo→teal→amber palette repeating 20× along the 1D path makes the self-similar U-winding visible at every scale simultaneously

## snowflake_crystal

- **Date**: 2026-04-26
- **Theme**: nature, crystallography, winter, 6-fold symmetry, fractal
- **Technique**: recursive depth-7 branching with per-depth random parameters (decay, angle, branch fraction) applied identically to all 6 arms; depth-based color interpolation blue→white; stroke weight tapering
- **Description**: A unique hexagonal snow crystal each run; six recursive fractal arms with randomized branching angles and decay ratios produce dendritic plate and stellar-dendrite morphologies against a midnight-sky star field

## kaleidoscope

- **Date**: 2026-04-26
- **Theme**: optics, symmetry, mandala, geometry, stained glass
- **Technique**: polar coordinate folding into canonical sector, multi-frequency sine product pattern, cyclic 4-stop jewel-tone palette, circular mask
- **Description**: 12-fold kaleidoscope; a 15° wedge of interfering sine harmonics is reflected and rotated to fill a circle; jewel-tone cyclic palette produces concentric stained-glass rings

## moire_pattern

- **Date**: 2026-04-26
- **Theme**: optics, geometry, interference, optical illusion
- **Technique**: two concentric ring distance fields from offset centers, boolean ring intersection coloring, three-state pixel mapping (ring A / ring B / overlap)
- **Description**: Two families of 20px-spaced concentric rings from horizontally offset centers interfere at crossing points; the bright lavender-white overlap points trace classical moiré elliptic and hyperbolic fringes against dark crimson and navy ring families

## particle_life

- **Date**: 2026-04-26
- **Theme**: emergence, artificial life, self-organization, complex systems
- **Technique**: N×N pairwise force matrix (random signed attraction/repulsion), quadratic force profile in interaction ring, toroidal boundaries, numpy vectorized Euler integration
- **Description**: 1000 particles of 5 types governed by a random force matrix self-organize into clusters, cell-like membranes, and predator-prey structures; every run produces a unique emergent ecology from the same simple physics

## harmonograph

- **Date**: 2026-04-26
- **Theme**: physics, oscillation, mechanical drawing, decay
- **Technique**: dual-pendulum harmonograph (4-component parametric x/y), exponential decay, near-rational 2:3 frequency ratios, age-based gold→amber color gradient
- **Description**: A single 500k-point trace follows the full life of a dual-pendulum plotter from wide gold swings to dim amber spirals converging at center; twisted-ribbon forms emerge from the interplay of two slightly incommensurate oscillating pendulums

## mandelbrot_set

- **Date**: 2026-04-26
- **Theme**: mathematics, complex dynamics, fractal geometry, parameter space
- **Technique**: vectorized numpy escape-time iteration, smooth coloring (ν = i+1−log₂(log₂|z|)), 3-stop violet→amber→gold gradient
- **Description**: The Mandelbrot set rendered with smooth escape-time coloring; the fractal boundary glows amber-gold where orbits take longest to escape, cooling to deep violet in the empty exterior; the interior remains near-black

## barnsley_fern

- **Date**: 2026-04-26
- **Theme**: nature, botany, fractal, self-similarity, IFS
- **Technique**: Barnsley IFS (4 affine transforms), 800k stochastic iterations, 2D density accumulation, log-scale 3-stop color gradient
- **Description**: 800k stochastic IFS iterations accumulate into a density field that reveals the Barnsley fern — stem, main self-similar frond, and paired lateral leaflets; log-scale mapping with a dark-forest-to-pale-tip gradient produces a photorealistic fractal fern frond

## spirograph

- **Date**: 2026-04-26
- **Theme**: mathematics, mechanical drawing, symmetry, petal geometry
- **Technique**: parametric hypotrochoid equations (d = R−r rose mode), 8 overlaid curves with petal counts 4–12, normalized radii, semi-transparent concentric layering
- **Description**: Eight hypotrochoid rose curves in distinct colors (crimson through rose) overlaid at the canvas center; petal counts 4, 5, 6, 7, 8, 9, 11, 12 build a stained-glass mandala where overlapping petals create color interference patterns

## halftone_waves

- **Date**: 2026-04-26
- **Theme**: printing, halftone, wave interference, graphic design
- **Technique**: two interleaved dot grids (offset by half cell), cosine wave superposition amplitude drives dot radius, power-stretch contrast, complementary two-color fields
- **Description**: Four wave point sources create interference; amplitude drives navy dot radius on a regular grid and complementary (inverted) amplitude drives sienna dots on a half-cell-offset grid; constructive and destructive peaks appear as clusters of large navy or sienna dots with bare cream paper at interference nulls

## sand_dunes

- **Date**: 2026-04-26
- **Theme**: desert landscape, geology, atmosphere, light
- **Technique**: layered ridge silhouettes back-to-front, 1D cosine noise profiles (2–5 octaves), filled polygon depth compositing, sky gradient via numpy pixel buffer
- **Description**: 14 dune ridge silhouettes progress from dark brown near the horizon to pale ivory cream in the foreground, with a burnt-sienna-to-amber sky gradient; front layers have higher octave noise and greater amplitude, producing sharp desert crests while back layers dissolve into hazy distance

## dragon_curve

- **Date**: 2026-04-26
- **Theme**: mathematics, fractals, space-filling curves, self-similarity
- **Technique**: binary fold sequence iteration, cumulative angle integration mod 4, 16 cyclic color bands along path
- **Description**: 15-iteration Harter-Heighway dragon curve with 32,767 right-angle segments; the path is divided into 16 sequential color bands cycling through a 4-stop indigo-coral-teal-gold palette, making the self-similar winding visible at every scale against near-black

## penrose_tiling

- **Date**: 2026-04-26
- **Theme**: mathematics, aperiodic tiling, quasicrystals, 5-fold symmetry
- **Technique**: Robinson triangle substitution (golden-ratio split), 7 iterations from decagonal seed, 5-sector angular coloring
- **Description**: ~6100 half-rhombus triangles from 7 rounds of Penrose P3 substitution; fat rhombuses colored in 5 warm shades and thin rhombuses in 5 cool shades by angular sector, forming a never-repeating mosaic with perfect 10-fold symmetry

## apollonian_gasket

- **Date**: 2026-04-26
- **Theme**: mathematics, fractals, circle packing, recursive geometry
- **Technique**: Descartes' Circle Theorem (inverse no-sqrt BFS formula), 6-stop curvature-octave palette, iterative gap filling
- **Description**: Apollonian gasket from (-1,2,2,3) seed; each gap between three tangent circles is filled with a unique inscribed circle; 6-stop warm-to-cool palette cycles by curvature octave (log₂k), encoding scale as color while the fractal limit set emerges at the boundary

## ink_diffusion

- **Date**: 2026-04-26
- **Theme**: ink wash, washi paper, calligraphy, diffusion, texture
- **Technique**: stochastic Brownian particle diffusion, fiber-direction anisotropy, inter-drop tendril flow, satellite splatter, log-scale density tone mapping
- **Description**: Sumi-e ink drops on washi paper simulated via 60k particles per drop diffusing along paper fiber direction; variable concentration creates tonal range from dilute wash to dense pools; nearby drops connect through flowing tendrils; satellite spatters add authentic imperfection

## crystal_growth

- **Date**: 2026-04-26
- **Theme**: geology, crystallography, emergence, mineral, cave
- **Technique**: stochastic dendritic branching with crystallographic angle constraints (60°/90°/30°), depth-controlled sub-branching, anti-aliased line segments, multi-scale Gaussian glow, age-based 4-stop color gradient
- **Description**: Multiple crystal seeds in cave darkness sprout dendritic arms at crystallographic angles up to 8 levels deep; age-based gradient from deep violet core through amethyst and quartz rose to mineral gold tips; multi-scale glow creates atmospheric luminosity

## tidal_erosion

- **Date**: 2026-04-26
- **Theme**: geology, coastal erosion, ocean, strata, natural forces
- **Technique**: procedural cliff geometry with multi-frequency profiles, 2D fractal noise erosion weighted by waterline proximity, noise-perturbed sea caves, wavy strata boundaries, vectorized numpy rendering
- **Description**: Cross-section coastal cliff with 12 geological strata progressively carved by simulated tidal erosion; noise-based erosion creates organic undercuts and sea caves at waterline; overhanging cliff face, vertical cracks, seafoam, and mist spray complete the scene

## smoke_rings

- **Date**: 2026-04-26
- **Theme**: fluid dynamics, vortex rings, physics, atmospheric
- **Technique**: point vortex Biot-Savart simulation, 50k particles per ring, bincount density accumulation, log tone mapping
- **Description**: Three vortex ring cross-sections (cerulean · gold · mint) formed by counter-rotating point vortex pairs; 50k particles per ring trace the toroidal Biot-Savart flow field for 200 steps; density accumulation reveals tight glowing cores and diffuse return-flow halos against near-black

## gravity_lensing

- **Date**: 2026-04-26
- **Theme**: space, physics, general relativity, optics, black hole
- **Technique**: thin-lens point-mass deflection (α = r_E²/r), bilinear interpolation via map_coordinates, amplification ring, Doppler-brightened accretion disk, photon sphere glow, gaussian star PSF
- **Description**: A synthetic black hole rendered via gravitational lensing: each pixel's light ray is deflected back to its unlensed star-field origin; a golden Einstein ring encircles the pitch-black event horizon, an orange accretion disk glows across the equator with Doppler brightening, and a blue-white photon sphere halo marks the last photon orbit

## water_caustics

- **Date**: 2026-04-26
- **Theme**: water, light, optics, physics, swimming pool, refraction
- **Technique**: analytic sinusoidal wave surface, vector Snell's law refraction, bincount photon-density accumulation, three-zone tone mapping (floor / glow / flare), tile grid compositing
- **Description**: Sunlight refracted through a random 8-wave water surface projected onto a virtual pool floor; bright caustic lines form a golden shimmering web where many rays converge, dark voids appear where they diverge, against a deep navy ceramic-tile floor

## soap_film

- **Date**: 2026-04-26
- **Theme**: optics, thin-film interference, iridescence, light, physics
- **Technique**: 6-octave fBm thickness field (0–680 nm), 21-wavelength spectral integration of I(λ)=½(1−cos(4πnt/λ)) with CIE sensitivity curves, saturation boost + power-law tone map
- **Description**: A soap film's iridescent colour field rendered from first-principles thin-film optics; Newton's interference colour sequence (black film → first-order violet/blue → green → orange/red → second-order) swirls across an fBm thickness landscape, gravity-biased thicker at the bottom

## spider_web

- **Date**: 2026-04-26
- **Theme**: nature, geometry, morning dew, organic structure, precision
- **Technique**: logarithmic spiral row spacing, quadratic bezier sag per segment, 4-layer composited dew-drop circles with specular highlight, hub glow compositing, per-run randomised geometry
- **Description**: Orb spider's web at dawn: 30–40 radial threads with angle jitter fan out to a frame polygon; 22–30 logarithmically spaced capture-silk spiral rows sag gently toward the hub via bezier; ~80% of intersections carry layered dew-drop pearls with white specular highlights against deep midnight blue

## city_rain

- **Date**: 2026-04-26
- **Theme**: urban, night, atmosphere, rain, reflection, neon
- **Technique**: 4-depth-layer procedural building generation, window probability grid per layer, ripple-distorted wet-pavement reflection, directional rain via exponential field + gaussian filter, additive bloom compositing
- **Description**: Nocturnal cityscape in the rain: back-to-front building towers lit by grids of amber/blue/orange windows and neon signs; the lower 40% of canvas shows the skyline reflected in wet asphalt, sinusoidally ripple-distorted and fading toward the ground; thin rain streaks and a bloom post-pass complete the scene

## paper_marbling

- **Date**: 2026-04-26
- **Theme**: craft, textile, fluid, Turkish ebru, Ottoman art, paper marbling
- **Technique**: ink-drop radial expansion (new_d = sqrt(d²+r²)), alternating x/y sinusoidal comb strokes with decaying amplitude, smooth palette interpolation across 6 jewel-tone colours in 5 stripe cycles, Gaussian grain post-processing
- **Description**: Ebru paper marbling simulation: 7–11 ink drops push the colour-stripe field radially outward, then 5–9 alternating comb strokes apply sinusoidal warps to create the characteristic Ottoman marbling pattern; peacock blue, emerald, gold, cream, burgundy, and midnight navy flow in complex organic bands

## crystal_lattice

- **Date**: 2026-04-26
- **Theme**: crystallography, physics, X-ray diffraction, hidden order, symmetry
- **Technique**: reciprocal lattice Fourier transform, structure factor with multi-atom basis, Debye-Waller damping, Gaussian spot rendering, Laue zone rings
- **Description**: X-ray diffraction pattern from a randomly chosen 2D crystal lattice (hexagonal/square/rectangular/oblique); reciprocal lattice spots glow cyan-to-gold with intensity from structure-factor phase summation; systematic extinctions reveal multi-atom basis symmetry against deep midnight with concentric Laue rings

## magnetic_pendulum

- **Date**: 2026-04-26
- **Theme**: chaos theory, determinism, fate, basin of attraction, physics
- **Technique**: damped magnetic pendulum ODE simulation (3 magnets), per-pixel basin-of-attraction mapping, convergence-speed brightness, Laplacian edge enhancement
- **Description**: Each pixel is colored by which of three magnets captures a damped pendulum started at that position; the fractal boundary between basins reveals sensitive dependence on initial conditions in amethyst, teal, and copper

## mycelium_network

- **Date**: 2026-04-26
- **Theme**: nature, biology, underground ecosystems, decomposition, fungal growth
- **Technique**: stochastic branching growth algorithm with age-based color mapping, glow effects on active growth tips, depth-based stroke tapering
- **Description**: 15 fungal networks spread across dark soil, growing, branching, and aging from cream (active) to brown (mature); delicate glow surrounding young tips emphasizes the underground kingdom where mycelium silently connects and decomposes the forest

## bonfire

- **Date**: 2026-04-26
- **Theme**: nature, fire, heat, chaos, organic motion
- **Technique**: fractal noise domain warping (two warp layers + base fBm), height-dependent Gaussian horizontal focus, power-law vertical taper, classic fire color palette
- **Description**: Organic flame tongues rise from a white-hot ember base through amber and orange to dim crimson tips; two layers of fBm domain-warp distort the heat field horizontally to create the characteristic lateral flicker of real fire against a deep black void

## stellar_nursery

- **Date**: 2026-04-26
- **Theme**: space, astronomy, star formation, emission nebula, cosmos
- **Technique**: multi-scale fBm spectral noise for gas density, narrowband emission palette (Hα/OIII/SII), protostar glow with core+halo, dust extinction, multi-scale bloom post-processing, HDR tone mapping
- **Description**: A stellar nursery rendered from first-principles astrophotography: layered fractal gas clouds in hydrogen-alpha red, oxygen-III teal, and sulfur-II amber; embedded protostars illuminate the nebula from within; dust lanes carve dark silhouettes; film grain and vignette mimic a deep-sky telescope exposure

## ikeda_attractor

- **Date**: 2026-04-28
- **Theme**: chaos theory, mathematics, strange attractor, phase space
- **Technique**: Ikeda map discrete-time dynamical system, 50k trajectory points, iteration-based color gradient (cyan→magenta→white), point rendering with alpha blending
- **Description**: A chaotic system spiraling through phase space; the Ikeda attractor generates complex organic trajectories from simple mathematical rules, rendered as a glowing spiral that transitions from electric cyan through warm magenta to bright white against a deep midnight blue background

## tiled_fractal

- **Date**: 2026-04-28
- **Theme**: fractal geometry, recursion, organic asymmetry, tiling
- **Technique**: recursive square subdivision with asymmetric quadrant sizes, rotation at each recursion level, dramatic color gradient transitions, seed-based organic variation
- **Description**: A dynamic fractal pattern that breaks mechanical grid symmetry through organic asymmetry and rotation; squares subdivide asymmetrically with 22.5° rotation increments, creating visual movement with dramatic color transitions from deep emerald to bright teal and deep amber to bright coral against deep charcoal

## bioluminescent_forest

- **Date**: 2026-04-28
- **Theme**: nature, bioluminescence, forest, night, organic growth, particle systems
- **Technique**: recursive tree structures with randomized parameters, particle system with swarm behavior (cohesion, alignment, wandering), depth-based scaling and opacity for 3D spatial relationships, attraction points for organic clustering, varied glow strength based on tree age, ground vegetation with smaller recursive structures, purple/magenta accents in deeper forest areas
- **Description**: A mesmerizing bioluminescent forest where glowing trees and floating fireflies create an enchanting nighttime atmosphere; organic tree structures with randomized parameters, depth-based layering for 3D spatial relationships, and vibrant color transitions from teal to amber to violet with purple and magenta accents in deeper areas

## fluid_dynamics

- **Date**: 2026-04-28
- **Theme**: fluid dynamics, mathematics, physics, organic flow, turbulence
- **Technique**: Navier-Stokes-based fluid dynamics simulation with vorticity visualization, stable fluid solver with dye advection, diffusion, projection (divergence-free velocity field), and vorticity confinement to create organic swirling patterns
- **Description**: A mathematical fluid simulation revealing the hidden patterns of flow and turbulence; Navier-Stokes equations create organic swirling patterns that resemble ocean currents or atmospheric flow, rendered in electric cyan, warm coral, and golden amber on a deep navy background

## chromatic_aberration

- **Date**: 2026-04-28
- **Theme**: optics, light, physics, chromatic aberration, dispersion, prismatic color
- **Technique**: wavelength-dependent refraction indices, ray tracing through optical elements (convex lenses, prisms, concave lenses), additive blending, glow effects
- **Description**: Chromatic aberration simulation using wavelength-dependent refraction indices; creates prismatic color separation through simulated optical elements with rainbow patterns, revealing the hidden spectrum within white light

## diffraction_pattern

- **Date**: 2026-04-29
- **Theme**: optics, wave physics, interference, diffraction, mathematical precision
- **Technique**: Fraunhofer diffraction simulation using Fourier transform principles, 2D FFT for far-field diffraction patterns, multiple aperture types (circular, rectangular, double slit)
- **Description**: Wave interference patterns revealed through Fraunhofer diffraction; concentric diffraction rings and interference fringes created by light passing through apertures, demonstrating the wave nature of light with mathematical precision

## coral_reef

- **Date**: 2026-04-29
- **Theme**: marine biology, underwater ecosystems, organic growth, biodiversity
- **Technique**: procedural coral generation with recursive branching, randomized parameters, depth-based layering, underwater lighting effects
- **Description**: Five distinct coral morphologies (branching, plate, staghorn, brain, fan) grow organically across the sea floor; vibrant coral pink, seafoam teal, golden amber, soft lavender, and bright turquoise colonies rise from deep navy waters with atmospheric light rays and rising bubbles

## sound_waves

- **Date**: 2026-04-29
- **Theme**: acoustics, sound visualization, frequency patterns, audio waves
- **Technique**: procedural waveform generation with frequency-based layering, amplitude modulation, harmonic overtones, spectrogram-style visualization
- **Description**: Eight layered horizontal sound waves with harmonic overtones, twelve radiating circular wave patterns, and a spectrogram-style background create a complex audio visualization; electric blue, warm magenta, and bright cyan waves interfere against a deep charcoal field with frequency bars at the bottom

## slime_intelligence

- **Date**: 2026-05-02
- **Theme**: nature, biology, emergent intelligence, biological networks
- **Technique**: agent-based Physarum simulation, trail map diffusion, vectorized NumPy physics
- **Description**: 100k autonomous agents simulate the foraging behavior of a slime mold, self-organizing into an organic transport network with bioluminescent indigo, teal, and gold trails against a deep obsidian void

## cyber_circuits

- **Date**: 2026-05-02
- **Theme**: urban, machine, cybernetics, digital metaphor
- **Technique**: recursive grid subdivision, Manhattan random walk, particle trails, additive blending
- **Description**: A pulsating digital metropolis where data packets navigate a hierarchical network of glowing circuits in cyber lime, electric blue, and hot pink

## quantum_foam

- **Date**: 2026-05-02
- **Theme**: cosmos, physics, quantum mechanics, energy
- **Technique**: dynamic Voronoi tessellation, noise-driven seeds, energy bursts, additive blending
- **Description**: The frantic, chaotic bubbling of spacetime at the Planck scale, rendered as a flickering froth of ultraviolet and magenta energy flashes

## luminescent_bloom

- **Date**: 2026-05-02
- **Theme**: nature, botanical, space, magic
- **Technique**: Bezier curves, polar symmetry, particle system, additive blending
- **Description**: Exotic bioluminescent flowers swaying in a deep-space garden, unfurling glowing violet petals as golden pollen drifts through the void

## chromatic_drift

- **Date**: 2026-05-02
- **Theme**: synesthesia, optics, memory, pure abstraction
- **Technique**: multi-channel particle system, noise flow field, SCREEN blending, long exposure
- **Description**: The ethereal separation of light into its constituent R, G, B channels as it drifts through a hazy, prismatic void

## metamorphic_flow

- **Date**: 2026-05-02
- **Theme**: geology, metamorphic rock, deep time, pressure
- **Technique**: domain-warped fractal noise, mineral vein thresholding, stone grain synthesis, vectorized NumPy
- **Description**: Organic, compressed geological strata resembling polished agate, rendered through domain-warped noise with obsidian, sienna, and gold mineral tones

## solar_wind

- **Date**: 2026-05-02
- **Theme**: plasma, magnetic fields, solar activity, cosmic energy
- **Technique**: magnetic dipole streamline integration, particle systems, additive blending, cosmic noise background
- **Description**: High-energy plasma ribbons of cyan and violet being deflected and channeled by a planetary magnetic field against a star-dusted void

## glitch_strata

- **Date**: 2026-05-02
- **Theme**: digital decay, data corruption, archaeology, glitch art
- **Technique**: recursive stratification, horizontal displacement mapping, block corruption, scanline synthesis
- **Description**: A vertical cross-section of corrupted digital memory, rendered as high-contrast neon strata with horizontal tearing and geometric data blocks

## neural_synapse

- **Date**: 2026-05-02
- **Theme**: neuroscience, connectivity, biological computation, signals
- **Technique**: stochastic branching growth, multi-scale action potential glow, additive blending, organic cell simulation
- **Description**: A glowing biological network of neural connections with flickering electrical pulses in gold, cyan, and violet racing between irregular cell bodies

## crystallized_time

- **Date**: 2026-05-02
- **Theme**: time, crystals, geometry, fragility
- **Technique**: recursive subdivision, prismatic diffraction, SCREEN blending, geometric clipping
- **Description**: A luminous, shattered field of crystalline shards in ice blue and prism violet, with rainbow diffraction on the edges and brilliant prismatic flares

## fluid_mosaic

- **Date**: 2026-05-02
- **Theme**: molecular biology, cell membrane, fluidity, life
- **Technique**: fluid simulation, noise-driven velocity fields, dual-scale particle systems, multi-layer trail accumulation
- **Description**: A shimmering microscopic landscape where vibrant coral and amber protein complexes drift through a fluid sea of teal phospholipids and wispy extracellular fibers

## kinetic_typography

- **Date**: 2026-05-02
- **Theme**: language, communication, digital flow, data
- **Technique**: text-based particle system, vortex vector fields, chromatic aberration, glitch shifts
- **Description**: A swirling vortex of multilingual characters that transitions from emerald chaos to a structured, glowing white grid with digital display distortion

## orbital_mechanics

- **Date**: 2026-05-02
- **Theme**: astronomy, gravity, orbits, cosmic dance
- **Technique**: RK4 N-body simulation, velocity-based line thickness, long-exposure trail accumulation
- **Description**: A complex, glowing map of hundreds of satellite orbits in gold and seafoam dancing around a multi-planet system with subtle rings and atmospheric halos

## tectonic_drift

- **Date**: 2026-05-02
- **Theme**: geology, plate tectonics, planetary evolution, crustal movement
- **Technique**: Voronoi tessellation, boundary vector analysis, fractal noise mountains, magmatic rift synthesis
- **Description**: A planetary-scale map of shifting crustal plates, featuring voluminous basalt mountain ranges at collision zones and glowing orange magma rifts in divergent valleys

## bioluminescent_deep

- **Date**: 2026-05-02
- **Theme**: marine biology, deep sea, bioluminescence, organic form
- **Technique**: radial noise shapes, internal glow organs, curling tentacle simulation, organic plankton clustering
- **Description**: A stunning view into the midnight zone of the ocean, featuring glowing jellyfish-like creatures in magenta and cyan surrounded by a dense cloud of bioluminescent plankton and falling marine snow

## geometric_growth

- **Date**: 2026-05-02
- **Theme**: mathematics, recursion, L-systems, architecture
- **Technique**: L-system branching, recursive geometric subdivision, multi-layered depth, architectural rendering
- **Description**: A dense, golden architectural forest growing across an obsidian void, where fractal L-system branches transition into intricate, Mondrian-style subdivision tiles

## liquid_crystal

- **Date**: 2026-05-02
- **Theme**: physics, microscopic, iridescence, soft matter
- **Technique**: Schlieren texture simulation, director field noise, iridescent mapping, polarized light physics
- **Description**: Shimmering iridescent patterns of a liquid crystal thin film under a cross-polarized microscope, featuring dynamic Schlieren textures and topological defects

## ca_reef

- **Date**: 2026-05-02
- **Theme**: cellular automata, biology, self-organization, coral
- **Technique**: multi-state CA, organic polyp rendering, noise-based jitter, atmospheric depth pass
- **Description**: A vibrant, living grid of coral polyps in coral pink and seafoam green, emerging from a calcified rocky base and shimmering underwater atmosphere

## ethereal_echoes

- **Date**: 2026-05-03
- **Theme**: physics, resonance, invisible fields, light, abstraction
- **Technique**: Interferometry simulation via multi-source wave interference, non-linear field mapping for sharp fringes, prismatic color interpolation, vectorized NumPy rendering
- **Description**: A visualization of intersecting wave fields that produce complex, glowing interference patterns with sharp, prismatic "echo" lines.


## radiolarian_pulse

- **Date**: 2026-05-03
- **Theme**: marine biology, geometry, deep sea, organic pulse
- **Technique**: icosphere subdivision, spherical inversion, 3D Perlin noise, layered SCREEN blending, particle glow
- **Description**: A bioluminescent microscopic skeleton pulses and inverts through its own center; bone-white and electric-cyan geometric threads form an intricate lattice surrounded by drifting gold marine snow against a deep abyss.

## fractal_metropolis

- **Date**: 2026-05-04
- **Theme**: Fractal urbanism, data-metabolism, spectral infrastructure, cosmic scale
- **Technique**: Deformed hexagonal lattice, recursive Koch-polygon architecture, spectral edge-glow simulation, multi-scale starfield synthesis
- **Logic Lab Reference**: `tiling_patterns/ih02_tv08_koch/ih02_tv08_koch.py`
- **Description**: A sprawling, glowing metropolis of fractal monoliths extends into a deep-space void; each structure is built from shimmering geometric layers that subdivide and pulse with electric cyan and laser pink light, while a distant starfield and violet horizon haze suggest an infinite atmospheric scale.


## prismatic_reflection

- **Date**: 2026-05-03
- **Theme**: optics, geometry, physics, spectral dispersion
- **Technique**: recursive ray-casting, 15-channel spectral decomposition, additive blending, star-polygon mirror maze
- **Description**: A complex web of light fractured into its constituent rainbow colors through 20 levels of reflection within a geometric star-shaped mirror maze; high-brilliance spectral fringes against a deep navy void.


## superfluid_tangle

- **Date**: 2026-05-03
- **Theme**: physics, fluid dynamics, quantum turbulence
- **Technique**: 2D Biot-Savart point-vortex simulation, 3000-particle flow field, HSB velocity mapping, additive trail synthesis
- **Description**: A dense, glowing web of electric cyan and violet filaments swirling around ten hidden vortex cores; a visualization of frictionless quantum turbulence with long, liquid-like trails against a dark navy void.


## tectonic_tension

- **Date**: 2026-05-03
- **Theme**: geology, physics, tectonics, volcanic energy
- **Technique**: Voronoi-based plate simulation, ridge stress analysis, multi-layered additive glow, kinetic magma particles
- **Description**: A visceral visualization of shifting geological plates; dark basalt slabs drift and collide, releasing intense orange magma glow and sparkling ejecta at the boundaries against a hazy, volcanic atmosphere.


## neural_synapse

- **Date**: 2026-05-03
- **Theme**: biology, networks, intelligence, electricity
- **Technique**: Stochastic graph-based signal propagation, 3D perspective projection, branching activation cascades, additive bloom trails
- **Description**: A complex, glowing web of bioluminescent nodes firing electric magenta and cyan signals; pulses cascade through a rotating 3D network, creating a shimmering, interconnected mind against a deep indigo void.

## spectral_mirage

- **Date**: 2026-05-03
- **Theme**: optics, atmosphere, prismatic light, ice crystals
- **Technique**: noise-guided ray-casting, spectral dispersion (wavelength-dependent refraction), structured beam clustering, multi-pass glow rendering
- **Description**: A cold, shimmering veil of light Fractured into prismatic filaments as it passes through a simulated ice-density field; electric blue and prism violet fringes emerge from structured beams against a deep midnight navy void.

## spectral_synchrony

- **Date**: 2026-05-03
- **Theme**: mathematics, synchronization, emergence, networks, resonance
- **Technique**: Kuramoto model simulation, coherence-based edge rendering, phase-mapped pulsing, additive SCREEN blending
- **Description**: 200 coupled oscillators self-organize from chaos into a rhythmic collective heartbeat; electric cyan and deep magenta connections emerge as neighbors synchronize their internal phases, forming a breathing web of light against deep charcoal.

## prismatic_architecture

- **Date**: 2026-05-03
- **Theme**: architecture, crystals, iridescence, geometry, modularity
- **Technique**: recursive isometric cube subdivision, thin-film interference color mapping, additive SCREEN blending, stochastic growth
- **Description**: A futuristic metropolis of shimmering crystalline structures; iridescent teal, rose, and gold faces refract light across a recursive geometric landscape, creating intense luminosity where structures converge against an obsidian sky.

## fractal_metropolis

- **Date**: 2026-05-04
- **Theme**: Fractal urbanism, data-metabolism, spectral infrastructure, cosmic scale
- **Technique**: Deformed hexagonal lattice, recursive Koch-polygon architecture, spectral edge-glow simulation, multi-scale starfield synthesis
- **Logic Lab Reference**: `tiling_patterns/ih02_tv08_koch/ih02_tv08_koch.py`
- **Description**: A sprawling, glowing metropolis of fractal monoliths extends into a deep-space void; each structure is built from shimmering geometric layers that subdivide and pulse with electric cyan and laser pink light, while a distant starfield and violet horizon haze suggest an infinite atmospheric scale.

## photonic_bandgap_waveguide

- **Date**: 2026-05-17
- **Theme**: Light guided through a labyrinth of silent obsidian pillars, trapped within a designed defect where it flows around a sharp turn without scattering, visualizing the control of light at the microscopic scale.
- **Technique**: 2D TM-polarized FDTD wave solver on a square dielectric lattice with an L-shaped defect channel and edge absorption.
- **Description**: Sinusoidal electric field waves (Teal crests and Coral troughs) propagate down a channel and bend perfectly at a 90-degree corner, while adjacent gold pillars scatter the evanescent field, breathing with gold light.

## adaptive_nerve_bloom

- **Date**: 2026-05-17
- **Theme**: Artificial intelligence learning to recognize patterns through dynamic synaptic adaptation, visualizing the emergence of computational intelligence.
- **Technique**: Procedural neural network simulation with 180 stochastically-positioned neurons, proximity-based synapse generation (250px radius), adaptive synapse strength decay, and activation-driven signal propagation with distance-weighted color mapping. 15s 4K/60fps MP4.
- **Description**: A constellation of glowing neural nodes blooms across a dark void, forming a dense web of cyan, magenta, and gold connections that pulse with computational energy. As signals propagate through the network, synaptic connections strengthen and weaken in real time, visualizing the dynamic learning process of artificial intelligence reorganizing itself.

## wildfire_front_propagation

- **Date**: 2026-05-17
- **Theme**: A spreading wildfire racing across dry grassland, visualizing how heat and fuel interact to drive the expanding flame front with organic chaos.
- **Technique**: Cellular automata fire propagation on 240×135 grid with heat diffusion, probabilistic neighbor-spreading, fuel depletion, and temperature-mapped RGB coloring. 18s 4K/60fps MP4.
- **Description**: A spark ignites in darkness and erupts into an expanding wildfire, creating jagged flame fronts that spread in organic, chaotic patterns. Brilliant incandescent white cores glow through vibrant orange and scarlet reds to deep charred boundaries, creating visceral heat intensity while leaving blackened ash in the fire's wake.

## tidal_wave_propagation

- **Date**: 2026-05-17
- **Theme**: A massive tsunami expanding radially from a seismic epicenter, visualizing the relentless propagation of energy through ocean water.
- **Technique**: 2D wave equation simulation with Laplacian diffusion on 200×120 grid, depth-based color gradient rendering, periodic re-excitation pulses, and foam particle effects. 20s 4K/60fps MP4.
- **Description**: A central disturbance erupts in bright cyan light that radiates outward in concentric rings. The dark navy ocean blooms with glowing aqua wave patterns, their crests catching golden highlights as energy propagates across the canvas, leaving traces of foam-white in expanding arcs.

## cellular_division_bloom

- **Date**: 2026-05-17
- **Theme**: Microscopic view of cells dividing and growing exponentially in a petri dish, creating fractal-like branching patterns.
- **Technique**: Recursive cell division simulation with generation-based lifecycle, directional propagation, size-scaling per generation, pulsing radius animation, and generation-depth color mapping. 16s 4K/60fps MP4.
- **Description**: A single cell erupts and immediately divides into a cascade of exponential growth. Green and cyan cells multiply and branch symmetrically, creating elegant fractal structures that fill the canvas. Each cell pulses rhythmically with a deep purple nucleus, visualizing the mathematical beauty of biological reproduction.

## fractal_tree_generation

- **Date**: 2026-05-17
- **Theme**: Recursive tree growth using Lindenmayer systems, visualizing how simple branching rules create complex botanical fractals.
- **Technique**: Recursive L-system tree generation with turtle graphics rendering, binary branching (±0.4 rads), length scaling (75% per generation), generation-based coloring, progressive animation reveal, and leaf particle effects. 14s 4K/60fps MP4.
- **Description**: A single trunk erupts and recursively splits into increasingly fine branches. Warm brown wooden limbs extend upward through ten generations while glowing green leaves bloom along mature branches, creating a living fractal tree with organic mathematical elegance.

## noise_field_flow

- **Date**: 2026-05-17
- **Theme**: Particles flowing along invisible currents defined by turbulent noise, visualizing emergent fluid-like behavior.
- **Technique**: Perlin noise-based velocity field particle advection with 5000 particles, velocity smoothing (0.8 decay), noise-value coloring gradient, variable size based on local noise magnitude. 12s 4K/60fps MP4.
- **Description**: Thousands of cyan and magenta particles swirl and flow in organic curves, guided by invisible Perlin noise currents. Electric ribbons weave and spiral, creating vortices and laminar flow patterns that mimic natural fluid dynamics while remaining purely particle-driven.

## sortation_dawn

- **Date**: 2026-05-19
- **Theme**: A modern logistics floor waking before sunrise, where silent machines route parcels with choreographed precision.
- **Technique**: Event-driven conveyor network animation with easing-based lane transfers, rotating diverter gates, scanner sweeps, restrained additive glow, and procedural parcel traffic. 10s 1920x1080/60fps MP4.
- **Description**: A graphite industrial floor becomes a nocturnal city grid of moving packages, cyan scanner beams, amber status lights, and pivoting diverter gates. Parcels glide and change lanes across seven conveyor bands, turning logistics infrastructure into a precise, modern routing choreography.

## elevator_memory

- **Date**: 2026-05-19
- **Theme**: A glass tower remembering every elevator trip as pale vertical traces in the night.
- **Technique**: Multi-shaft elevator choreography with eased triangular motion, fading path memory, stochastic window calls, parallax city silhouettes, and restrained glow passes. 10s 1920x1080/60fps MP4.
- **Description**: A translucent high-rise facade becomes a vertical traffic recorder: elevator cabins rise and descend through nine shafts while previous trips remain as cyan, amber, silver, and rose traces. The work turns routine urban circulation into a quiet architectural memory field.

## drone_port_lattice

- **Date**: 2026-05-19
- **Theme**: A rooftop drone-port network negotiating quiet autonomous arrivals under a dark city sky.
- **Technique**: Routed flight-arc animation with stochastic landing pads, easing-based drone interpolation, pad occupancy pulses, parallax skyline layers, and aviation-light accents. 10s 1920x1080/60fps MP4.
- **Description**: A graphite rooftop becomes a near-future autonomy map: circular charging pads pulse across a skewed landing deck while small drones follow faint curved routes between numbered ports. Teal, amber, white, and red navigation lights keep the image modern and restrained.

## recurrence_chamber

- **Date**: 2026-05-19
- **Theme**: A dark instrument chamber where nonlinear vibration briefly loses order, then remembers its first tone.
- **Technique**: Alpha-FPUT coupled oscillator lattice with fixed boundaries, velocity Verlet integration, sine-mode projection, modal recurrence meter, resonator bars, and energy-band traces. 12s 1920x1080/60fps MP4.
- **Description**: A graphite laboratory chamber holds a row of vertical resonators that bend with nonlinear displacement while cyan, amber, rose, and silver mode traces pass through them. The animation visualizes energy leaving the fundamental tone and returning as a measured recurrence pulse.

## liquidity_tide

- **Date**: 2026-05-19
- **Theme**: A market order book breathing like a tide as invisible pressure moves around the midprice.
- **Technique**: Stochastic limit-order-book simulation with bid/ask depth arrays, order arrivals, cancellations, trade pulses, spread pressure, scrolling depth-memory heatmap, and imbalance meter. 10s 1920x1080/60fps MP4.
- **Description**: A dark market terminal becomes a living depth map: cyan bid liquidity and rose ask liquidity accumulate, thin out, and ripple around a silver midprice while amber spread pressure frames the center. Trade impacts appear as circular pulses, turning microstructure into a restrained financial tide.

## wafer_stepper_drift

- **Date**: 2026-05-19
- **Theme**: A semiconductor wafer passing through a quiet lithography exposure cycle as alignment errors drift below perception.
- **Technique**: Procedural wafer die grid with dose accumulation, moving scanner slit, overlay-error vector field, alignment control pulses, and circular inspection sweep. 10s 1920x1080/60fps MP4.
- **Description**: A dark cleanroom field frames a circular wafer as a cyan exposure slit scans across the die grid. Violet resist dose accumulates inside each chip field while tiny amber overlay vectors and silver inspection geometry turn fabrication tolerance into a precise nocturnal ritual.

## battery_formation_field

- **Date**: 2026-05-19
- **Theme**: A battery-cell formation rack balancing hundreds of quiet charge states before the cells become useful.
- **Technique**: Procedural cell-array simulation with charge-state waves, balancing shunts, thermal drift, diagnostic traces, and rack-level meters. 10s 1920x1080/60fps MP4.
- **Description**: A graphite formation rack holds rows of glowing cells whose cyan and green charge columns rise through slow stochastic phases. Amber balancing shunts and red thermal warnings punctuate the field while low diagnostic traces turn cell formation into a restrained industrial calibration ritual.

## cold_chain_pulse

- **Date**: 2026-05-19
- **Theme**: A refrigerated storage wall breathing through compressor cycles as cold air and humidity drift through each bay.
- **Technique**: Procedural cold-chain sensor grid with bay temperatures, humidity rings, compressor pulses, condensation particles, and scrolling thermal traces. 10s 1920x1080/60fps MP4.
- **Description**: A dark insulated panel holds rows of refrigerated bays whose blue-cyan fields shift with compressor phase and door-load drift. Mist particles and ice rings make the cold visible, while thin sensor traces turn refrigerated logistics into a quiet atmospheric control system.

## harbor_crane_ballet

- **Date**: 2026-05-19
- **Theme**: A night container terminal where gantry cranes move with the calm precision of choreography.
- **Technique**: Procedural port scene with container stacks, ship berths, gantry crane kinematics, trolley/load motion, berth scheduling arcs, haze fields, and water reflections. 10s 1920x1080/60fps MP4.
- **Description**: A dark harbor becomes a staged terminal ballet: gantry cranes glide across rails, glowing loads descend between ship and yard, and stacked containers form dense signal blocks. Cyan and amber scheduling arcs hover over the berth while water reflections stretch the industrial lights into the night.

## nanopore_signal_loom

- **Date**: 2026-05-19
- **Theme**: A sequencing flow cell listening to strands of DNA as tiny current interruptions become readable signals.
- **Technique**: Procedural nanopore sensor channels with stochastic base events, ion-current traces, pore glow pulses, molecule drift, base-call rings, and quality meter. 10s 1920x1080/60fps MP4.
- **Description**: A graphite flow-cell panel streams twelve cyan ion-current traces while colored base-call rings bloom where molecular events interrupt the signal. Drifting molecule specks and a small quality meter frame live DNA sequencing as a quiet conversion of physical blockage into information.

## lenia_morphogenesis

- **Date**: 2026-05-21
- **Theme**: Continuous Cellular Automata (Lenia) & Particle Morphogenesis
- **Technique**: Vectorized 2D FFT convolutions, density gradient advection (100,000 tracers), and multi-channel color blending. 15s 1920x1080/60fps MP4.
- **Description**: A stunning continuous cellular automaton simulation where organic violet and cyan cell bodies slide dynamically over an obsidian background, forming active golden cores. As they glide and mutate, 100,000 golden particles are drawn along the density gradients, trailing glowing bioluminescent dust that highlights the self-organizing flow.

<!-- Add new works above this line using the format below:

## kinetic_tensegrity_sculpture_3d

- **Date**: 2026-05-24
- **Theme**: Kinetic sculpture, tensegrity, balance, physics simulation, tension vs compression, impossible floating geometry.
- **Technique**: Simulates a 3D system of nodes with rigid distance constraints (struts) and dynamic spring constraints (cables). The resting lengths of the cables are continuously modulated by a 3D Perlin noise field and sine waves. This causes the tensegrity structure to organically breathe, fold, twist, and turn inside out in 3D space, constantly seeking a new equilibrium. The struts are rendered as thick, bright, glowing white/cyan bars, while the cables are thin, semi-transparent magenta/blue lines using additive blending. 15s 60fps MP4.
- **Description**: A delicate, glowing tensegrity structure floats in the dark. Built from rigid, neon-cyan struts and semi-transparent magenta tension cables, the entire object seems to defy gravity. As invisible forces continuously pull and release the tension in the cables, the structure breathes and twists, collapsing in on itself before expanding outward into complex, shifting geometric forms. The organic motion of the cables contrasts beautifully with the sharp, rigid geometry of the struts, creating a mesmerizing kinetic sculpture.

## geometric_fractal_hilbert_curve_3d

- **Date**: 2026-05-24
- **Theme**: Fractals, space-filling curves, infinity, digital circuitry, labyrinth, dimensionality, sacred math.
- **Technique**: Generates an 8,000-point 3D lattice self-avoiding random walk that mimics the dense geometry of a 3D Hilbert Curve. The entire structure is drawn as a single continuous line using `py5.begin_shape(py5.LINE_STRIP)` with additive blending. To create a mesmerizing kinetic effect, the coordinate scale is modulated by an expanding and collapsing sine wave over time. High-frequency 3D noise is injected into the vertices as they expand, making the rigid digital circuitry crackle with electric energy. The color smoothly cycles through the HSB spectrum based on vertex index and time. 15s 60fps MP4.
- **Description**: A dense, microscopic cluster of glowing neon energy suddenly expands outward, revealing itself to be a massive, perfectly cubic labyrinth of digital circuitry. The continuous 3D line folds and weaves through space, filling the entire volume of the cube without ever intersecting itself. As the structure reaches its maximum expansion, the energetic lines crackle with rainbow light before slowly collapsing back into a dense, glowing singularity.

## generative_particle_life_ecosystem

- **Date**: 2026-05-24
- **Theme**: Artificial life, emergent behavior, microscopic organisms, cells, particle physics, chemistry.
- **Technique**: Simulates 2,500 particles divided into 4 color "species". The behavior is governed by a 4x4 interaction matrix of attraction and repulsion forces, optimized using NumPy vectorization. The values in the interaction matrix slowly oscillate over time using 2D Perlin noise, causing the ecosystem to continuously transition between chaotic swarms and structured cells. Rendered in 4K with additive blending.
- **Description**: A vibrant, microscopic petri dish of artificial life. Four distinct species of brightly colored particles dance and swarm together, constantly forming temporary cell-like structures, wriggling worms, and crystalline clusters before dissolving back into a chaotic soup as the laws of their physics continuously mutate.
