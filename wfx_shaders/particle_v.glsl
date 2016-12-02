//GLSL
#version 140
#pragma include "inc_config.glsl"

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrixInverse;
uniform vec2 screen_size;
uniform vec3 camera_pos;
uniform sampler2D pos_tex;
uniform sampler2D size_tex;
uniform sampler2D one_pos;
uniform sampler2D zero_pos;
uniform sampler2D offset_tex;
uniform float index_offset;
uniform vec4 status[WFX_NUM_EMITTERS];
in vec4 p3d_Vertex;

flat out vec2 center;
flat out float point_size;
flat out float life;
out vec4 uv_offset;

void main()
    {
    float id=float(gl_VertexID)+index_offset;
    float tex_size=textureSize(pos_tex, 0).x;

    vec2 pos_uv=vec2(mod(id, tex_size)/tex_size, 1.0-ceil(id/tex_size)/tex_size);
    pos_uv+=vec2(0.5/tex_size,0.5/tex_size);//read from the center of a texel
    uv_offset=textureLod(offset_tex, pos_uv, 0);
    vec4 offset=textureLod(pos_tex, pos_uv, 0);
    life=clamp(offset.w/textureLod(one_pos, pos_uv, 0).w, 0.0, 1.0);
    vec4 size_curve=textureLod(size_tex, pos_uv, 0);
    vec4 vert = p3d_Vertex;
    vert.xyz+=offset.xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * vert;
    float dist =distance(vert.xyz,camera_pos);
    point_size = screen_size.y/ dist;

    point_size*= (sin(life+size_curve.x)*3.141592653589793*size_curve.y)*size_curve.z + size_curve.w;

    if (point_size<1.0)
        point_size=0.0;
    center = (gl_Position.xy / gl_Position.w * 0.5 + 0.5);

    if (offset.w<0.0)
        point_size = 0.0;

    vec4 pos_zero=textureLod(zero_pos, pos_uv, 0);
    int emmiter_id=int(pos_zero.w);
    if (status[emmiter_id].w == 0.0)
        point_size = 0.0;

    gl_PointSize = point_size;
    }
