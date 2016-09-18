//GLSL
#version 140
uniform vec2 screen_size;
uniform sampler2D tex;

uniform float osg_FrameTime;

flat in vec2 center;
flat in float point_size;
flat in float life;

void main()
    {
    vec2 uv = (gl_FragCoord.xy / screen_size - center) / (point_size / screen_size) + 0.5;
    uv.y*=0.0625;//8 tiles in the texture
    uv.y-=0.0625*ceil(life/0.0625);
    vec4 final_color=texture(tex, uv);
    gl_FragData[0]=final_color;
    }
