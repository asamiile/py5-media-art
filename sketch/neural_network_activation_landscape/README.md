# neural_network_activation_landscape

A visual journey through the hidden activation landscape of a deep neural network processing spatial data.

- **Date**: 2026-05-23
- **Theme**: Artificial intelligence, latent space, continuous neural representations, generative art.
- **Technique**: We construct a 2-hidden-layer Multi-Layer Perceptron (MLP) purely in NumPy. A dense grid of 2D $(X, Y)$ coordinates acts as the input batch, and we perform a full forward pass (`Dense -> ReLU -> Dense -> ReLU -> Dense -> Sin`) for every pixel on the canvas simultaneously. Over time, the internal weight matrices of the network are smoothly rotated using a skew-symmetric matrix multiplier, simulating a slow, continuous walk through the network's high-dimensional latent space. The 3-channel output is directly mapped to the RGB pixel buffer. 15s 60fps MP4.
- **Description**: The screen is covered in smooth, surreal blobs and sharply creased bands of vibrant color. As the hidden "brain" slowly rewires its internal connections, the decision boundaries warp, flow, and fold into one another. It feels like peering into the fluid, geometric dreams of an artificial intelligence.
