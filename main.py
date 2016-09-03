from panda3d.core import loadPrcFileData
loadPrcFileData("", "show-frame-rate-meter  1")
loadPrcFileData("", "sync-video 0")
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "textures-power-2 none")
loadPrcFileData("", "show-buffers 0")
from panda3d.core import *
from direct.showbase import ShowBase
from buff_rotator import BufferRotator
import random
import math


def mix(x, y, a):
    return x*(1.0-a)+y*a

class Demo():
    def __init__(self):
        base = ShowBase.ShowBase()
        #number of points, make it power-o-2,
        #later we get a texture size for it as int(math.sqrt(num_points))
        num_points=256*256
        #some global shader inputs
        render.setShaderInput('screen_size', Vec2(800.0, 600.0))
        render.setShaderInput('camera_pos', base.camera.getPos(render))

        #create a vertex-point... well num_points of them
        aformat = GeomVertexArrayFormat("vertex", 1, GeomEnums.NT_uint8, GeomEnums.C_other)
        format = GeomVertexFormat.register_format(GeomVertexFormat(aformat))
        vdata = GeomVertexData('abc', format, GeomEnums.UH_static)
        vdata.set_num_rows(num_points)
        geom = Geom(vdata)
        p = GeomPoints(Geom.UH_static)
        #p.add_vertex(0)
        p.addNextVertices(num_points)
        geom.add_primitive(p)
        geom.set_bounds(OmniBoundingVolume())
        geom_node = GeomNode('point')
        geom_node.addGeom(geom)
        #the final point node (with lots of points inside)
        self.point_node=render.attachNewNode(geom_node)
        self.point_node.setRenderMode(RenderModeAttrib.MPoint, 1) #the point size is overriden in the shader

        #we will run the physics using position data only
        #velocity is pos_at_frame_1 minus pos_at_frame_0 (given a constant timestep of 1)
        # the location is in xyz, w is the particle life

        #the size of the texture needed
        xy_size=int(math.sqrt(num_points))

        pos_0_pfm=PfmFile()
        pos_0_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        for x in range(xy_size):
            for y in range(xy_size):
                noise=Vec4(random.uniform(-1.0,1.0),random.uniform(-1.0,1.0), random.uniform(-1.0,1.0), 0.0)
                r=mix(Vec4(-0.1, 0.0, 0.5, 0.0), noise, 0.3)
                v=Vec4(float(x), float(y), 0.0, 1.0)
                pos_0_pfm.setPoint4(x, y, v+r)

        pos_1_pfm=PfmFile()
        pos_1_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        life=0.0
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec4(float(x), float(y), 0.0, life)
                pos_1_pfm.setPoint4(x, y, v)
                life+=1.0
                if life>300.0:
                    life=0.0

        pos_tex0=Texture()
        pos_tex1=Texture()
        pos_tex0.load(pos_0_pfm)
        pos_tex1.load(pos_1_pfm)

        #noise texture
        noise_pfm=PfmFile()
        noise_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=3)
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec3(random.uniform(-1.0,1.0),random.uniform(-1.0,1.0), random.uniform(-1.0,1.0))
                v.normalize()
                noise_pfm.setPoint3(x, y, v)
        noise_tex=Texture()
        noise_tex.load(noise_pfm)

        shader_inputs={'noise':noise_tex}

        physics_shader=Shader.load(Shader.SL_GLSL,'physics_v.glsl', 'physics_f.glsl')
        self.ping_pong=BufferRotator(physics_shader, pos_tex0, pos_tex1,shader_inputs)


        #set the shader for the point(s)
        shader_attrib = ShaderAttrib.make(Shader.load(Shader.SLGLSL, 'particle_v.glsl','particle_f.glsl'))
        shader_attrib = shader_attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
        self.point_node.setAttrib(shader_attrib)
        self.point_node.setShaderInput('radius', 5.0)
        tex=loader.loadTexture("point.png")
        self.point_node.setShaderInput('tex', tex)
        self.point_node.setShaderInput('pos_tex', self.ping_pong.output)

        self.point_node.setTransparency(TransparencyAttrib.MBinary)

        #additive blend
        #color_attrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OOne, ColorBlendAttrib.OOneMinusIncomingColor)
        #self.point_node.setAttrib(color_attrib)
        #self.point_node.setBin("fixed", 0)
        #self.point_node.setDepthTest(True)
        #self.point_node.setDepthWrite(False)

        taskMgr.add(self.update, 'update')

    def update(self, task):
        dt=globalClock.getDt()
        render.setShaderInput('camera_pos', base.camera.getPos(render))
        self.ping_pong.update(dt)
        self.point_node.setShaderInput('pos_tex', self.ping_pong.output)
        #print self.ping_pong.output
        return task.again

d=Demo()
base.run()
