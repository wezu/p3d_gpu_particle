//GLSL
#version 140
uniform vec2 screen_size;
uniform sampler2D tex;

flat in vec2 center;
flat in float point_size;

void main()
    {
    vec2 uv = (gl_FragCoord.xy / screen_size - center) / (point_size / screen_size) + 0.5;
    vec4 final_color=texture(tex, uv);
    //final_color=v_color;
    gl_FragData[0]=final_color;
    }
