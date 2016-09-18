//GLSL
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrixInverse;
uniform vec2 screen_size;
uniform float  radius;
uniform vec3 camera_pos;
uniform sampler2D pos_tex;
uniform sampler2D size_tex;
uniform sampler2D one_pos;
in vec4 p3d_Vertex;

flat out vec2 center;
flat out float point_size;
flat out float life;

void main()
    {
    float id=float(gl_VertexID);
    float tex_size=textureSize(pos_tex, 0).x;

    vec2 pos_uv=vec2(mod(id, tex_size)/tex_size, ceil(id/tex_size)/tex_size);
    //pos_uv=+vec2(0.5/tex_size,0.5/tex_size);//??

    vec4 offset=textureLod(pos_tex, pos_uv, 0);
    life=offset.w/textureLod(one_pos, pos_uv, 0).w;
    vec4 size_curve=textureLod(size_tex, pos_uv, 0);
    vec4 vert = p3d_Vertex;
    vert.xyz+=offset.xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * vert;
    float dist =distance(vert.xyz,camera_pos);
    point_size = (radius*screen_size.y)/ dist;

    point_size*= (sin(life+size_curve.x)*3.141592653589793*size_curve.y)*size_curve.z + size_curve.w;

    if (point_size<1.0)
        point_size=0.0;
    center = (gl_Position.xy / gl_Position.w * 0.5 + 0.5);

    if (offset.w<0.0)
        point_size = 0.0;

     gl_PointSize = point_size;
    }
