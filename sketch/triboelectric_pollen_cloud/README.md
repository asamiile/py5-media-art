# triboelectric_pollen_cloud

10-second 4K/60fps py5 animation of pollen grains suspended in a dim air column while moving static charges pull thin blue-violet field lines around them.

The renderer combines a procedural electrostatic potential field with ring-shaped pollen shells and a fading charge-memory buffer. Frames are rendered through py5's pixel buffer, encoded with FFmpeg as `output.mp4`, mirrored to `triboelectric_pollen_cloud.mp4`, and sampled at mid-frame for `triboelectric_pollen_cloud_p1.png`.
