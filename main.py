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
        #number of points, make it power-o-2, tested up to 1024*1024= 1 048 576 particles@ 90-120fps on a AMD R7
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
        #self.point_node.setInstanceCount(num_points)

        #we will run the physics using position data only
        #velocity is pos_at_frame_1 minus pos_at_frame_0 (given a constant timestep of 1)
        # the location is in xyz, w is the particle life

        #the size of the texture needed
        xy_size=int(math.sqrt(num_points))


        #initial textures, only the life (alpha) is important, rest should be 0
        life=-1.0
        pos_0_pfm=PfmFile()
        pos_0_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec4(0.0, 0.0, 0.0, life)
                pos_0_pfm.setPoint4(x, y, v)
                life -=1.0
                if life<-100.0:
                    life=-1.0

        pos_1_pfm=PfmFile()
        pos_1_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        life=0.0
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec4(0.0, 0.0, 0.0, life)
                pos_1_pfm.setPoint4(x, y, v)
                life -=1.0
                if life<-100.0:
                    life=0.0
        #texture for life=0, alpha == mass
        zero_pos_pfm=PfmFile()
        zero_pos_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec4(float(x), float(y), 0.0, random.uniform(0.2, 0.4))
                zero_pos_pfm.setPoint4(x, y, v)
        #texture for life=1, alpha == max_life
        one_pos_pfm=PfmFile()
        one_pos_pfm.clear(x_size=xy_size, y_size=xy_size, num_channels=4)
        for x in range(xy_size):
            for y in range(xy_size):
                v=Vec4(float(x)+random.uniform(-0.5, 0.5), float(y)+random.uniform(-0.5, 0.5), 1.0, random.uniform(200.0, 400.0))
                one_pos_pfm.setPoint4(x, y, v)

        #TODO:
        #other props (per emitter?):
        #-size change over life
        #-mass change over life
        #-uv offset, animation speed(???)
        #-forces
        #change over time is made using a sin function
        #change= (sin(current_life/max_life+sin_offset)*Pi*frequency)*scale + offset
        #the values are encoded as Vec4(sin_offset, frequency, scale, offset)
        # example settings:
        # from 0 to 1 (almost) linear: Vec4(0.0, 0.0001, 1000.0*math.pi, 0.0)
        # from 1 to 0 (almost) linear: Vec4(0.0, 0.0001, -1000.0*math.pi, 1.0)
        #from 0 to 1 (convex): Vec4(0.0, 0.5, 1.0, 0.0)
        #from 0 to 1 (concave): Vec4(-1.0, 0.5, 1.0, 1.0)
        #from 0 to 1 (smooth): Vec4(0.5, 1.0, -0.5, 0.5)
        #from 0 to 1 then back to 0: Vec4(0.0, 1.0, 1.0, 0.0)
        #constant 17:  Vec4(0.0, 0.0, 1.0, 17.0)
        #to make any kind of shape multiple sin (or cos) functions would have to be added
        #the cost of this would get high and I don't think this would be needed very often

        pos_tex0=Texture()
        pos_tex1=Texture()
        one_pos=Texture()
        zero_pos=Texture()
        pos_tex0.load(pos_0_pfm)
        pos_tex1.load(pos_1_pfm)
        one_pos.load(one_pos_pfm)
        zero_pos.load(zero_pos_pfm)

        shader_inputs={'one_pos':one_pos, 'zero_pos':zero_pos}

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
        return task.again

d=Demo()
base.run()
