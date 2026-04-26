# snowflake_crystal

**Theme**: "Singular crystal" — a single hexagonal snow crystal grown by recursive fractal branching; each run produces a unique snowflake because branch angles and decay rates are randomized, but perfect 6-fold symmetry is enforced by applying identical parameters to all six arms

**Technique**: Recursive depth-7 branching; per-depth parameters (trunk decay ratio, side-branch angle, branch length fraction) are drawn once from random uniform ranges and applied symmetrically to all 6 arms at 60° intervals; depth-based color interpolation from deep ice-blue (trunk) to near-white (tips); stroke weight tapers with depth

**Description**: Six main arms radiate at 60° intervals from the canvas center. At each recursion level, the arm continues (with a length-decay factor) and spawns two symmetric side branches (bilateral symmetry within each arm, 6-fold across all arms). Branch angles range 55°–72° and length fractions 50%–68%, producing the characteristic dendritic plate and stellar-dendrite morphologies of real ice crystals. A subtle star field suggests falling snow in a winter sky.

**Palette**:
- Background: `#080c18` midnight blue-black
- Trunk: `#3c64c8` deep ice blue
- Tips: `#dceaff` near-white
- Stars: dim steel-blue scattered dots

**Preview**: `preview.png`
