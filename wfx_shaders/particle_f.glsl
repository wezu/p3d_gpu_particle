//GLSL
#version 140
#pragma include "inc_config.glsl"

uniform vec2 screen_size;
uniform sampler2D tex;

uniform float osg_FrameTime;

flat in vec2 center;
flat in float point_size;
flat in float life;
in vec4 uv_offset;

void main()
    {
    vec2 uv = (gl_FragCoord.xy / screen_size - center) / (point_size / screen_size) + 0.5;
    uv.y*=1.0/uv_offset.w;
    uv.y-=(ceil(life*uv_offset.w))/uv_offset.w;
    uv.x*=uv_offset.z;
    uv.x+=uv_offset.x;
    vec4 final_color=texture(tex, uv);
    gl_FragData[0]=final_color;
    }
