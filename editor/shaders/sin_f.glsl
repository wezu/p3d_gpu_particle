//GLSL
#version 140
uniform sampler2D p3d_Texture0;
uniform float offset;
uniform float freq;
uniform float multi;
uniform float x_offset;

in vec2 uv;

float PI=3.141592653589793;

bool almost(float x, float epsilon)
    {
    if (x<=-epsilon || x>=epsilon)
            return false;
    return true;
    }

void main()
    {
    float y=uv.y - (sin((uv.x+offset)*freq*PI)*sign(multi));
    float pixel =2.0/512.0;
    vec4 graph_line=vec4(0.0, 0.0, 0.0, 1.0);
    //the sin graph
    if (almost(y, pixel))
        graph_line=vec4(1.0, 0.0, 0.0, 1.0);

    vec4 graph_grid=vec4(0.0, 0.0, 0.0, 1.0);

    //guide lines
    if (almost(mod(uv.y+x_offset/multi, 1.0/multi), pixel))
        if (almost(uv.y+x_offset/multi, pixel))
            graph_grid=vec4(1.0, 1.0, 1.0, 1.0);
        else
            graph_grid=vec4(0.35, 0.4361, 0.7, 1.0);
    //background
    //vec4 graph_tex=texture(p3d_Texture0, vec2(uv.x, (uv.y*0.5)+0.5-x_offset));

    gl_FragData[0]=graph_grid+graph_line;
    }
