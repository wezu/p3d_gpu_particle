#version 140
#define import 1


#if WFX_USE_HEIGHTMAP_COLLISIONS==1
uniform sampler2D collision_map;
uniform vec3 world_pos_size;
#endif

#if WFX_USE_3D_COLLISIONS==1
uniform sampler3D voxel_map;
uniform vec3 voxel_size;
#endif

uniform sampler2D pos_tex_prelast;
uniform sampler2D pos_tex_last;
uniform sampler2D zero_pos;
uniform sampler2D one_pos;
uniform sampler2D mass_tex;
uniform sampler2D props_tex;
uniform vec4 global_force;
//uniform vec4 emitter_data[4*WFX_NUM_EMITTERS];
uniform mat4 emitter_data[WFX_NUM_EMITTERS];
uniform vec4 status[WFX_NUM_EMITTERS];// local_force=status.xyz, active_state=status.w

in vec2 uv;

out vec4 final_pos;

void main()
    {
    vec4 pos_last=texture(pos_tex_last, uv);
    vec4 pos_prelast=texture(pos_tex_prelast, uv);
    vec4 pos_one=texture(one_pos, uv);
    vec4 pos_zero=texture(zero_pos, uv);
    vec4 mass_curve=texture(mass_tex, uv);
    // props.x = start_life,  y=max_life z=emitter_id, w=bounce
    vec4 props=texture(props_tex, uv);
    //emitter id here for multiple emitters
    int emitter_id=int(props.z);
    mat4 emitter_matrix=emitter_data[emitter_id];


    float life =pos_last.w;
    float max_life=props.y;
    if (life>max_life)
        life=props.x;

    if (life<=0.0)
        {
        if (status[emitter_id].w == 0.0)
            final_pos=vec4(pos_last.xyz, -1.0);
        else
            {
            pos_zero=emitter_matrix *vec4(pos_zero.xyz, 1.0);
            final_pos=vec4(pos_zero.xyz, life+1.0);
            }
        }
    else
        {
        if (life<=1.0)
            {
            pos_one=emitter_matrix *vec4(pos_one.xyz, 1.0);
            final_pos=vec4(pos_one.xyz, life+1.0);
            }
        else
            {
            vec3 velocity=pos_last.xyz-pos_prelast.xyz;
            vec3 force = global_force.xyz + status[emitter_id].xyz; //status.xyz is the per-emitter local force
            float mass= (sin((life/max_life)+mass_curve.x)*3.141592653589793*mass_curve.y)*mass_curve.z + mass_curve.w;
            velocity += (force*mass)*WFX_VELOCITY_CONST;
            vec3 new_pos=pos_last.xyz+velocity;

            #if WFX_USE_HEIGHTMAP_COLLISIONS==1
            vec4 hm=texture(collision_map, (pos_last.xy+world_pos_size.xy)/world_pos_size.z);
            if ((new_pos.z<hm.w)&&(pos_last.z>hm.w-WFX_COLLISION_DEPTH))//&&(hm.xyz!=vec3(0.0,0.0,0.0)))
                {
                velocity=pos_last.xyz-pos_prelast.xyz;
                velocity=reflect(normalize(-hm.xyz), normalize(velocity))*length(velocity)*props.w;
                velocity.xy*=-1.0;
                new_pos.xyz=pos_last.xyz+velocity;
                }
            #endif

            #if WFX_USE_3D_COLLISIONS==1
            vec3 uvw=((new_pos.xyz+WFX_COLLISION_DEPTH)+voxel_size.xyz*0.5)/voxel_size.xyz;
            if (all(greaterThanEqual(uvw, vec3(0.0, 0.0, 0.0))) && all(lessThanEqual(uvw, vec3(1.0, 1.0, 1.0))))
                {
                uvw.y*=-1.0;
                vec4 voxel=texture(voxel_map, uvw);
                if (voxel.w > 0.0)
                    {
                    velocity=pos_last.xyz-pos_prelast.xyz;
                    velocity=reflect(normalize(-voxel.xyz), normalize(velocity))*length(velocity)*props.w;
                    velocity.xy*=-1.0;
                    velocity += (force*mass)*WFX_VELOCITY_CONST*(vec3(1.0, 1.0, 1.0)-normalize(voxel.xyz));
                    //velocity.xyz+=voxel.xyz*WFX_COLLISION_DEPTH*WFX_VELOCITY_CONST;
                    new_pos.xyz=pos_last.xyz+velocity;
                    }
                else
                    {
                    new_pos+=voxel.xyz*WFX_VELOCITY_CONST;
                    }
                }
            #endif


            final_pos=vec4(new_pos.xyz, life+1.0);
            }
        }
    }
