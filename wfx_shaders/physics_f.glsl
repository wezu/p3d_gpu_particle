//GLSL
#version 140
#pragma include "inc_config.glsl"

uniform sampler2D pos_tex_prelast;
uniform sampler2D pos_tex_last;
uniform sampler2D zero_pos;
uniform sampler2D one_pos;
uniform sampler2D mass_tex;
uniform vec4 global_force;
uniform vec4 emitter_data[4*WFX_NUM_EMITTERS];
//uniform float status[WFX_NUM_EMITTERS]; //1*num_emitters
uniform vec4 status[WFX_NUM_EMITTERS];

in vec2 uv;

out vec4 final_pos;

void main()
    {
    float tex_size=textureSize(pos_tex_last, 0).x;
    vec4 pos_last=texture(pos_tex_last, uv);
    vec4 pos_prelast=texture(pos_tex_prelast, uv);
    vec4 pos_one=texture(one_pos, uv);
    vec4 pos_zero=texture(zero_pos, uv);
    vec4 mass_curve=texture(mass_tex, uv);
    //insert emmiter id here for multiple emitters
    int emmiter_id=int(pos_zero.w);
    mat4 emmiter_matrix= mat4(emitter_data[0],emitter_data[1],emitter_data[2],emitter_data[3]);

    if (status[emmiter_id].w == 0.0)
        final_pos=pos_last;
    else
        {
        float life =pos_last.w;
        float max_life=pos_one.w;
        if (life>max_life)
            life=-1.0;

        if (life<=0.0)
            {
            pos_zero=emmiter_matrix *vec4(pos_zero.xyz, 1.0);
            final_pos=vec4(pos_zero.xyz, life+1.0);
            }
        else
            {
            if (life<=1.0)
                {
                pos_one=emmiter_matrix *vec4(pos_one.xyz, 1.0);
                final_pos=vec4(pos_one.xyz, life+1.0);
                }
            else
                {
                vec3 velocity=pos_last.xyz-pos_prelast.xyz;
                vec3 force = global_force.xyz + status[emmiter_id].xyz; //status.xyz is the per-emitter local force
                float mass= (sin((life/max_life)+mass_curve.x)*3.141592653589793*mass_curve.y)*mass_curve.z + mass_curve.w;
                velocity += (force*mass)*0.05;
                vec3 new_pos=pos_last.xyz+velocity;
                final_pos=vec4(new_pos.xyz, life+1.0);
                }
            }
        }
    }
