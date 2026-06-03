# fluid_vector_field_topology_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: A swirling, high-density 3D vector field of flowing ribbons representing fluid dynamics or magnetic field topology. The ribbons twist and turn continuously through space.
- **Technique**: Using 3D noise (Perlin/Simplex) to generate a velocity vector field. Hundreds of particles trace paths through the field. Instead of simple points, we draw ribbons (using `py5.begin_shape(py5.QUAD_STRIP)`) that leave a trailing history, twisting according to the local curl of the vector field. To keep it fast, we update fixed-length history arrays. Additive blending enhances the overlapping trails.
- **Color palette**:
  - Background: Deep Navy
  - Dominant (60%): Aqua / Teal
  - Secondary (30%): Electric Purple
  - Accent (10%): Luminous Coral
  - Mood: fluid / dynamic

## Description
An animated 3D simulation of a massive fluid vector field. Hundreds of luminous ribbons trace the invisible currents of a 3D noise field, twisting and flowing continuously. The ribbons are rendered using quad strips with a trailing history, giving them a physical presence as they snake through the dark navy void in shades of aqua, electric purple, and coral.
