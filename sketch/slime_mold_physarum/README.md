# slime_mold_physarum

The foraging behavior of Physarum polycephalum (slime mold).

- **Date**: 2026-05-23
- **Theme**: Biological growth, multi-agent systems, emergent behavior, slime mold.
- **Technique**: A massive multi-agent particle simulation running entirely on a 2D grid. 150,000 independent sensory agents deposit chemical pheromones on the grid as they move. They also sense the local pheromone gradient using three forward sensors and steer towards the highest concentration. The global pheromone grid is continuously diffused and decayed using `scipy.ndimage.gaussian_filter`. Rendered via nearest-neighbor upscaling into a bio-luminescent Electric Green and Deep Violet palette directly in the `py5.np_pixels` buffer. 15s 60fps MP4.
- **Description**: What starts as an amorphous ring of individual particles quickly organizes into striking, pulsing transport networks. The agents follow each other's chemical trails, spontaneously forming dense super-highways of glowing electric green that branch, weave, and restructure themselves like the veins of a living organism.
