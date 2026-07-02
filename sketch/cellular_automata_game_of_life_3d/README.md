# cellular_automata_game_of_life_3d

## Metadata
- **Date**: 2026-05-23
- **Theme**: A 3D adaptation of Conway's Game of Life, visualizing emergent behaviors in a volumetric grid
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A 3D adaptation of Conway's Game of Life, visualizing emergent behaviors in a volumetric grid.

- **Date**: 2026-05-23
- **Theme**: Cellular automata, emergence, 3D voxel graphics, Game of Life.
- **Technique**: Operates a 32x32x32 state grid using a 3D extension of the Game of Life rules (the "4555 rule": a cell survives if it has 4 or 5 neighbors, and is born if it has exactly 5 neighbors out of the possible 26 in a 3x3x3 Moore neighborhood). The neighbor counting is highly optimized using `scipy.signal.convolve`. To make the visualization compelling, the age of each surviving cell is tracked. When rendered using `py5.box`, older cells grow slightly larger and shift their HSB hue over time, making it easy to distinguish stable geometric structures from chaotic, newly-born noise. 15s 60fps MP4.
- **Description**: A cluster of randomly blinking neon blocks floats in the center of the screen. Suddenly, complex geometric patterns begin to emerge from the noise. Symmetrical gliders shoot off into the darkness, while oscillating central structures slowly shift through rainbow colors as they survive from generation to generation. The camera smoothly orbits the entire 3D voxel structure, revealing the intricate internal architecture of the emergent lifeforms.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details
