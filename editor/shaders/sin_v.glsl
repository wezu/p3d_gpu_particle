//GLSL
#version 140

uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;

out vec2 uv;
in vec2 p3d_MultiTexCoord0;

void main()
    {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv=vec2(p3d_MultiTexCoord0.x,p3d_MultiTexCoord0.y*2.0)-vec2(0.0, 1.0);
    }
