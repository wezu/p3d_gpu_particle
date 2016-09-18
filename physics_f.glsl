//GLSL
#version 140
uniform sampler2D pos_tex_prelast;
uniform sampler2D pos_tex_last;
uniform sampler2D zero_pos;
uniform sampler2D one_pos;
in vec2 uv;

out vec4 final_pos;

void main()
    {
    float tex_size=textureSize(pos_tex_last, 0).x;
    vec4 pos_last=texture(pos_tex_last, uv);
    vec4 pos_prelast=texture(pos_tex_prelast, uv);
    vec4 pos_one=texture(one_pos, uv);
    vec4 pos_zero=texture(zero_pos, uv);
    
    float life =pos_last.w;
    if (life>pos_one.w)
        life=-1.0;
    
    if (life<=0.0)
        {
        final_pos=vec4(pos_zero.xyz, life+1.0);
        }
    else 
        {
        if (life<=1.0)    
            final_pos=vec4(pos_one.xyz, life+1.0);    
        else
            {
            vec3 velocity=pos_last.xyz-pos_prelast.xyz;
            vec3 force = vec3(0.0, 0.0, -1.0);
            float mass=pos_zero.w;                       
            velocity += (force*mass)*0.05;
            vec3 new_pos=pos_last.xyz+velocity; 
            final_pos=vec4(new_pos.xyz, life+1.0);        
            }   
        }    
    }
