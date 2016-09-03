//GLSL
#version 140
uniform sampler2D pos_tex_prelast;
uniform sampler2D pos_tex_last;
uniform sampler2D noise;
in vec2 uv;


void main()
    {
    vec4 pos_last=texture(pos_tex_last, uv);
    vec4 pos_prelast=texture(pos_tex_prelast, uv);
    vec3 noise_tex=texture(noise, uv).xyz;
    float life =pos_last.w;
    vec3 new_pos=vec3(0.0, 0.0, 0.0);

    if (life > 300.0)//reset after some time
        {
        vec3 v =mix(vec3(0.1, 0.0, -0.5), noise_tex, 0.3);
        new_pos.xyz=vec3(uv.xy*256.0, 0.0)+v;
        life=-1.0;
        }
    else
        {
        if (life<1.0) //new spawn, give it some initial velocity
            {
            //vec3 v =mix(vec3(0.1, 0.0, -0.5), noise_tex, 0.1);
            new_pos=vec3(uv.xy*256.0, 0.0);
            }
        else //middle of the simulation, apply gravity
            {
            vec3 velocity=pos_last.xyz-pos_prelast.xyz;
            vec3 force = vec3(0.0, 0.0, -1.0);
            float mass= abs(noise_tex.r*0.5)+0.1;
            velocity += (force*mass)*0.05;
            new_pos=pos_last.xyz+velocity;
            }
        }
    //increment life
    life+=1.0;

    gl_FragData[0]=vec4(new_pos.xyz, life);
    }
