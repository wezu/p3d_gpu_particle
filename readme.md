This is a Particle system for Panda3D.

This works by sending 256*256 vertex to the gpu then using a ping-pong buffer to render a texture with the locations for each vertex.
The vertex are then drawn as textures points.

At this point it just throws a bunch of particles in the air and let's them fall. Not all that impressive.
