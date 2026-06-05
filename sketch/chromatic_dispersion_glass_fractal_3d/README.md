# chromatic_dispersion_glass_fractal_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: A slow-rotating, complex 3D fractal (a Menger sponge variation) made of highly refractive glass that splits light into intense chromatic aberration.
- **Technique**: Instead of true raytracing, chromatic dispersion is simulated by rendering the recursive 3D geometry three times with additive blending (`py5.ADD`): once in pure Red, once in pure Green, and once in pure Blue. By applying slight offsets in rotation and scale driven by a sine wave, the overlapping colors combine to form pristine white edges that fracture into vibrant rainbows.
- **Color palette**:
  - Background: Pitch Black
  - Dominant (60%): Prismatic White (Additive RGB)
  - Secondary (30%): Cyan / Magenta / Yellow (Overlap edges)
  - Accent (10%): Pure Red, Green, Blue
  - Mood: crystalline / optical

## Description
An animated 3D simulation of a massive, glowing fractal crystal rotating in the void. Simulated chromatic aberration separates the light passing through the structure into its component RGB channels. As the fractal turns and breathes, the channels drift apart and recombine, painting the edges with intense neon rainbows and searing white additive light.
