# kinetic_haboku_sansui_ink_wash_mountain_mist_2d

Autonomous generative media art animation exploring classical Japanese Haboku Sansui (破墨山水, "broken ink landscape") and atmospheric valley mist dispersion across warm mulberry torinoko washi paper (`#f6f0e4`) in 4K UHD 60fps (12.0s seamless loop).

## Concept

Originating in Song dynasty China and brought to monumental heights by Zen master-painter Sesshū Tōyō (雪舟等楊, 1420–1506) and the Southern School (*Nanga*), **Haboku Sansui** (破墨山水, "broken ink mountain and water") discards rigid academic line drawings in favor of explosive, calligraphic splashes of wet-in-wet sumi ink, delicate tonal washes, and the profound void (*ma* 間 / *yohaku* 余白) of unpainted space representing rolling clouds and misty waters.

This artwork translates traditional ink wash landscape principles and classical aerial perspective into dynamic computational fluid atmospheres:

1. **The Three Distances (San'en 三遠)**:
   - **Kōen (高遠, High Distance)**: Looking up from deep gorges to towering monolithic crags piercing the celestial morning sky.
   - **Shin'en (深遠, Deep Distance)**: Looking beyond layered mountain crests into mysterious receding gorges shrouded in rolling fog.
   - **Hei'en (平遠, Level Distance)**: Looking across tranquil misty river waters and sandbars vanishing into the lower horizon.

2. **Seven Multi-Tier Mountain Ridges (Sumi & Mineral Glazes)**:
   - Procedural heightmaps combining Gaussian massif peaks, fractal harmonic folds, and sharp *axe-cut texture strokes* (斧劈皴 *fu-pi-cun*) on steep vertical granite escarpments.
   - Solid polygon masses anchored down to the base datum, preventing visual transparency artifacts while simulating opaque mountain strata.
   - Authentic Japanese mineral glaze washes:
     - **Azurite Gunjō** (群青 indigo): Glazed across mid-distance mountain shoulders.
     - **Raw Umber Taisha** (代赭 burnt sienna / iron oxide): Warm sunlit earthen slopes.
     - **Malachite Celadon Rokushō** (緑青 mineral green): Verdant mossy ledges and forested ridges.
     - **Rich Pitch Sumi Nōboku** (濃墨 carbon black): Foreground promontory crags.

3. **Volumetric Billowing Cloud Seas (雲海 Unkai)**:
   - Multi-stage Gaussian ribbon mist banks advecting horizontally across the inter-tier valleys with closed periodic harmonic drift ($x_{\text{drift}} = A \sin(\omega \tau + \phi)$).
   - High-density mineral white oyster shell pigment (*gofun* 胡粉) blanketing the mountain bases to create authentic "floating mountain islands".

4. **Mountain Cataracts, Cantilevered Pines & Perched Pavilions**:
   - Plunging waterfalls emerging from mountain saddles and clefts, tumbling into foamy spray pools nestled within valley mist.
   - Gnarled bonsai-style cantilevered pine trees (*matsu* 松) gripping rocky ledges with fan-shaped needle clusters (*matsuba* 松葉).
   - Solitary mountain pavilions (*azumaya* 東屋) with sweeping curved eaves perched above deep abysses.
   - A flight of soaring white cranes (*kōkaku* 孤鶴) wheeling smoothly in 12.0s harmonic cycles across the morning sun.

## Technical Specifications

- **Resolution**: 3840 × 2160 (4K UHD)
- **Framerate**: 60 fps
- **Duration**: 720 frames (12.0s seamless loop)
- **Loop Mathematics**: All periodic motion functions are harmonic closed cycles $\tau = t / T \in [0, 1)$ modulated by $\sin(2\pi \tau)$ and $\cos(2\pi \tau)$, guaranteeing exact frame-0 to frame-720 continuity.
- **Color Palette**:
  - Torinoko Mulberry Washi Paper Ground (`#f6f0e4`)
  - Rich Pitch Sumi Nōboku (`#10141a` / `#181c22`)
  - Intermediate Sumi Chūboku (`#525e6e` / `#76869c`)
  - Pale Distant Mist Tanboku (`#cfd4dc`)
  - Azurite Mineral Indigo Gunjō (`#5a738e`)
  - Raw Umber Earth Glaze Taisha (`#84664a`)
  - Malachite Celadon Mineral Wash Rokushō (`#2a5546`)
  - Mineral Oyster-Shell White Gofun (`#f8f4ea`)
- **Strict Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, artist signatures, monograms, initials, or personal seals.
