//GLSL
#version 140
uniform sampler2D pos_tex_prelast;
uniform sampler2D pos_tex_last;
in vec2 uv;


void main()
    {
    vec4 pos_last=texture(pos_tex_last, uv);
    vec4 pos_prelast=texture(pos_tex_prelast, uv);
    float life =pos_last.w;

    vec3 new_pos=vec3(0.0, 0.0, 0.0);
    vec3 velocity=pos_last.xyz-pos_prelast.xyz;
    vec3 force = vec3(0.0, 0.0, -1.0);
    float mass=0.1;
    velocity += (force*mass)*0.01;
    new_pos=pos_last.xyz+velocity;

    //life+=0.1;
    //if (life>20.0)
    //    {
    //    life=-0.2;
    //    new_pos=vec3(0.0, 0.0, 0.0);
    //    }
    gl_FragData[0]=vec4(new_pos.xyz, life);
    }
