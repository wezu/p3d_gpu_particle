//GLSL
#version 140
#pragma include "inc_config.glsl"
in vec3 normal;
in vec4 world_pos;

out vec4 normal_height;

void main()
    {
    vec3 N=normalize(normal);
    normal_height=vec4(normal.xyz, world_pos.z+WFX_HEIGHTMAP_PADDING);
    }
