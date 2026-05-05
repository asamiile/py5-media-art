# isohedral_metropolis

A non-Euclidean urban grid where interlocking "living blocks" pulse with data.

## Description

`isohedral_metropolis` reimagines the city as a biological-mechanical hybrid. Instead of rigid rectangular blocks, the urban fabric is defined by complex IH01 isohedral tilings. These boundaries are not static; they breathe and deform through harmonic oscillations, suggesting a city that adaptation and grows in real-time. Luminous conduits in electric cyan and laser pink carry data across the grid, while golden "hubs" pulse at the intersections of this high-tech metabolic network.

## Technical Details

- **Base Algorithm**: IH01 Isohedral Tiling (a hexagonal lattice derivative where each cell has 6 edges that can be independently deformed while maintaining perfect interlocking).
- **Deformation**: Dynamic Bezier edge warping driven by a bank of harmonic oscillators.
- **Rendering**: 
    - Retina-aware pixel buffer accumulation (persistence) for luminous "long-exposure" trails.
    - Multi-layer stroke rendering for glow effects.
    - High-density starfield background for atmospheric depth.
- **Palette**: `City Night` — Deep Indigo, Electric Cyan, Laser Pink, Solar Amber.

## Logic Lab Reference

- `tiling_patterns/ih01_deformation/ih01_deformation.py` — base isohedral tiling logic.
