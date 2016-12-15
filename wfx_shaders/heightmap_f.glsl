#version 140
//#pragma include "inc_config.glsl"
//The line below is more or less the same as the one above,
//just using a custom parser to avoid re-writing the include file to hd
//Don't remove it!!!!
#define import 1

in vec3 normal;
in vec4 world_pos;

out vec4 normal_height;

void main()
    {
    vec3 N=normalize(normal);
    normal_height=vec4(normal.xyz, world_pos.z+WFX_HEIGHTMAP_PADDING);
    }
