//GLSL
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrixInverse;
uniform vec2 screen_size;
uniform float  radius;
uniform vec3 camera_pos;
uniform sampler2D pos_tex;

in vec4 p3d_Vertex;

flat out vec2 center;
flat out float point_size;

void main()
    {
    float id=float(gl_VertexID);
    vec2 pos_uv=vec2(mod(id, 256.0)/256.0, ceil(id/256.0)/256.0);

    vec4 offset=textureLod(pos_tex, pos_uv, 0);
    vec4 vert = p3d_Vertex;
    vert.xyz+=offset.xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * vert;
    float dist =distance(vert.xyz,camera_pos);
    point_size = (radius*screen_size.y)/ dist;
    if (point_size<1.0)
        point_size=0.0;
    gl_PointSize = point_size;
    center = (gl_Position.xy / gl_Position.w * 0.5 + 0.5);

    //if (offset.w<0.0)
    //    gl_PointSize = 0.0;
    }
