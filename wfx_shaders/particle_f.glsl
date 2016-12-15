#version 140
//#pragma include "inc_config.glsl"
//The line below is more or less the same as the one above,
//just using a custom parser to avoid re-writing the include file to hd
//Don't remove it!!!!
#define import 1

#if WFX_AUX_RENDER_TARGET==1
uniform sampler2D tex_aux;
#endif

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

    //uv_offset.xy = uv offset, uv_offset.z = frame size, uv_offset.w= number of frames
    uv.y-=1.0;
    uv*=uv_offset.z;
    uv+=uv_offset.xy;
    uv.y-=floor(life*uv_offset.w)*uv_offset.z;

    gl_FragData[0]=texture(tex, uv);

    #if WFX_AUX_RENDER_TARGET==1
    gl_FragData[1]=texture(tex_aux, uv);
    #endif
    }
