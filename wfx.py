"""
Wezu Effects (Wfx) is a gpu particle rendering system for Panda3D
"""
from panda3d.core import *
import json

__author__ = "wezu"
__copyright__ = "Copyright 2016"
__license__ = "ISC"
__version__ = "0.1"
__email__ = "wezu.dev@gmail.com"
__status__ = "Work In Progress"

class Wfx():
    def __init__(self,
                num_emitters=1,
                update_speed=60.0,
                physics_shader=None,
                particle_shader=None,
                camera=None,
                root=None,
                window=None,
                heightmap_mask=17):
        """
        Setup

        Args:
            update_speed (float)    - how fast will the simulation run in FPS
            physics_shader(Shader)  - shader that will run the physic simulation
            particle_shader(Shader) - shader that will draw vertex as textures billbords
            camera(NodePath/Camera) - the default scene camera
            root(NodePath)          - root node for the simulation
            window(GraphicsOutput)  - the window to display the particles in (needed only for it's size)
            heightmap_mask(int)     - camera bitmask value (0-32) for rendering collision heightmap (wip)
        """
        #setup
        self.num_emitters=num_emitters
        #write the include for shaders
        with open('wfx_shaders/inc_config.glsl', 'w') as out_file:
            out_file.write('//WFX config, do not edit, it will be overriden anyway\n')
            out_file.write('#define WFX_NUM_EMITTERS '+str(num_emitters))
        self.update_speed=1.0/update_speed
        #the shader that will run the physic simulation
        self.physics_shader=Shader.load(Shader.SL_GLSL,'wfx_shaders/physics_v.glsl', 'wfx_shaders/physics_f.glsl')
        if physics_shader:
            self.physics_shader=physics_shader

        #the shader that will draw vertex as textures billbords
        self.particle_shader=Shader.load(Shader.SL_GLSL,'wfx_shaders/particle_v.glsl', 'wfx_shaders/particle_f.glsl')
        if particle_shader:
            self.particle_shader=particle_shader

        #a camera position needed to scale the particles that are away
        self.camera=base.camera
        if camera:
            self.camera=camera

        #the system sets some global shader inputs, so to avoid conficts
        # a dummy node can be inserted
        self.root=render.attachNewNode('wfx_root')
        if root:
            self.root=root.attachNewNode('wfx_root')
        self.root.hide()

        #the size of the window is needed to generate uv for the particles
        #it may not be base.win if rendering to a smaller off-screen buff
        #for soft particles or something like it
        self.window=base.win
        if window:
            self.window=window

        self.pause=False
        self.ping_pong=None
        self.task=None
        #update task
        #taskMgr.add(self._update, 'wfx_update_tsk')

    def reload_shaders(self):
        with open('wfx_shaders/inc_config.glsl', 'w') as out_file:
            out_file.write('//WFX config, do not edit, it will be overriden anyway\n')
            out_file.write('#define WFX_NUM_EMITTERS '+str(self.num_emitters))

        physics_v=self.physics_shader.getFilename(Shader.ST_vertex)
        physics_f=self.physics_shader.getFilename(Shader.ST_fragment)
        self.physics_shader=Shader.load(Shader.SL_GLSL, physics_v, physics_f)

        particle_v=self.particle_shader.getFilename(Shader.ST_vertex)
        particle_f=self.particle_shader.getFilename(Shader.ST_fragment)
        self.particle_shader=Shader.load(Shader.SL_GLSL, particle_v, particle_f)
        try:
            self.ping_pong.setShader(self.physics_shader)
        except AttributeError:
            pass
        try:
            shader_attrib = ShaderAttrib.make(self.particle_shader)
            shader_attrib = shader_attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
            self.root.setAttrib(shader_attrib)
        except AttributeError:
            pass

    def load(self, *args, **kwargs):
        """
        Loads values needed to run the simulation.

        Args:
            multifile
            pos_0
            pos_1
            mass
            size
            one_pos
            zero_pos
            data
            texture
            offset
        """
        needed_kwargs={'pos_0','pos_1','mass','size','one_pos','zero_pos','data', 'texture', 'offset'}

        if len(args)==1 or 'multifile' in kwargs:
            if 'multifile' in kwargs:
                mutlifile_path = kwargs['multifile']
            else:
                mutlifile_path = args[0]
            mf = Multifile()
            mf.openReadWrite(mutlifile_path)
            file_names=mf.getSubfileNames()
            new_kwargs={}
            for index, name in enumerate(file_names):
                if name[-3:]=='pfm':
                    pfm=PfmFile()
                    pfm.read(mf.openReadSubfile(index))
                    new_kwargs[name[:-4]]=Texture()
                    new_kwargs[name[:-4]].load(pfm)
                    new_kwargs[name[:-4]].setWrapU(Texture.WM_clamp)
                    new_kwargs[name[:-4]].setWrapV(Texture.WM_clamp)
                    new_kwargs[name[:-4]].setMagfilter(SamplerState.FT_nearest)
                    new_kwargs[name[:-4]].setMinfilter(SamplerState.FT_nearest)
                if name[-3:]=='png':
                    p = PNMImage()
                    p.read(mf.openReadSubfile(index))
                    new_kwargs[name[:-4]]=Texture()
                    new_kwargs[name[:-4]].load(p)
                    #new_kwargs[name[:-4]].setCompression(Texture.CM_dxt5)
                if name[-3:]=='txt':
                    ss=StringStream()
                    mf.extractSubfileTo(index,ss)
                    data=json.loads(ss.getData())
                    new_kwargs['data']=data

            #feed back the loaded pfm files back to self.load()
            self.load(**new_kwargs)
        elif needed_kwargs <= set(kwargs): #check if all the needed args are given
            #print kwargs['data']
            num_emiters=kwargs['data']['num_emitters']
            status=PTAFloat()
            for i in range(num_emiters):
                status.pushBack(float(kwargs['data']['status'][i]))

            shader_inputs={'one_pos':kwargs['one_pos'],
                        'zero_pos':kwargs['zero_pos'],
                        'mass_tex':kwargs['mass'],
                        'size_tex':kwargs['size'],
                        'status':status}
            x=kwargs['one_pos'].getXSize()
            y=kwargs['one_pos'].getYSize()
            #emitters, for now it's all self.root (default to render)
            emitters=[]
            for i in range(kwargs['data']['num_emitters']+1):
                emitters.append(self.root)
            if self.ping_pong is None:
                self.ping_pong=BufferRotator(self.physics_shader, kwargs['pos_0'], kwargs['pos_1'], shader_inputs, emitters, update_speed=self.update_speed)
                #add blending
                dual_blending=(x*y)-kwargs['data']['blend_index']
                print 'add', kwargs['data']['blend_index']
                self.points_add_blend=self.make_points(kwargs['data']['blend_index'])
                self.set_blend(self.points_add_blend, 'add')
                #mod blending
                self.points_dual_blend=self.make_points(dual_blending)
                self.set_blend(self.points_dual_blend, 'dual')
                print 'dual', dual_blending
            else:
                self.ping_pong.setShaderInputsDict(shader_inputs)
                self.ping_pong.reset_textures(kwargs['pos_0'], kwargs['pos_1'])

            #shader and inputs
            shader_attrib = ShaderAttrib.make(self.particle_shader)
            shader_attrib = shader_attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
            self.root.setAttrib(shader_attrib)
            self.root.setShaderInput('tex', kwargs['texture'])
            self.root.setShaderInput('one_pos', kwargs['one_pos'])
            self.root.setShaderInput('offset_tex', kwargs['offset'])
            self.root.setShaderInput('size_tex', kwargs['size'])
            self.root.setShaderInput('index_offset', 0.0)
            self.points_dual_blend.setShaderInput('index_offset', float(kwargs['data']['blend_index']))


            self.ping_pong.updateEmitterMatrix()
            self.root.setShaderInput('camera_pos', base.camera.getPos(self.root))
            self.root.setShaderInput('pos_tex', self.ping_pong.output)
            self.reset_window_size()
        else:
            print 'error'
            for arg in args:
                print 'arg:', arg
            print kwargs

    def set_blend(self, node,  mode):
        if mode=='dual':
            node.setTransparency(TransparencyAttrib.MDual, 1)
        elif mode =='add':
            color_attrib = ColorBlendAttrib.make(ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one )
            node.setAttrib(color_attrib)
            node.setBin("fixed", 0)
            node.setDepthTest(True)
            node.setDepthWrite(False)

    def make_points(self, num_points):
        #print 'make_points', num_points
        if num_points>1:
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
            point_node=render.attachNewNode(geom_node)
        else:
            point_node=render.attachNewNode('empty')
        point_node.setRenderMode(RenderModeAttrib.MPoint, 1)
        point_node.reparentTo(self.root)
        return point_node

    def start(self):
        self.root.show()
        if self.task is None:
            self.task=taskMgr.add(self._update, 'wfx_update_tsk')

    def set_pause(self):
        self.pause = not self.pause

    def restart(self):
        self.ping_pong.state=0

    def reset(self):
        taskMgr.remove(self.task)
        self.points_dual_blend.removeNode()
        self.points_add_blend.removeNode()
        self.ping_pong.remove()
        self.ping_pong=None

    def cleanup(self):
        self.reset()
        self.physics_shader=None
        self.particle_shader=None
        self.root=None
        self.window=None

    def reset_window_size(self, window=None):
        if window:
            self.window=window
        self.root.setShaderInput('screen_size', Vec2(self.window.getXSize(), self.window.getYSize()))

    def set_global_force(self, force):
        pass

    def set_emitter_force(self, emitter_id, force):
        pass

    def set_emitter_on(self, emitter_id):
        pass

    def set_emitter_off(self, emitter_id):
        pass

    def set_emitter_node(self, emitter_id, node):
        self.ping_pong.emitters[emitter_id]=node

    def _update(self, task):
        dt=globalClock.getDt()
        self.root.setShaderInput('camera_pos', base.camera.getPos(self.root))
        if not self.pause:
            self.ping_pong.update(dt)
        self.root.setShaderInput('pos_tex', self.ping_pong.output)
        return task.again




class BufferRotator():
    def __init__(self, shader, tex0, tex1, shader_inputs={}, emitters=None, bits=32, update_speed=None):
        #upadate speed - how often is the who thing run
        if update_speed:
            self.update_speed=update_speed
        else:
            self.update_speed=1.0/60.0

        self.emitters=[render]
        if emitters:
            self.emitters=emitters

        self.tex0=tex0
        self.tex1=tex1
        self.texA=Texture()
        self.texB=Texture()
        self.texC=Texture()

        self.buffA, self.quadA, self.camA = self.makeBuffer(self.texA, shader, shader_inputs, bits)
        self.buffB, self.quadB, self.camB = self.makeBuffer(self.texB, shader, shader_inputs, bits)
        self.buffC, self.quadC, self.camC = self.makeBuffer(self.texC, shader, shader_inputs, bits)

        self.quadA.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadA.setShaderInput('pos_tex_last',self.tex1)
        self.quadB.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadB.setShaderInput('pos_tex_last',self.tex1)
        self.quadC.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadC.setShaderInput('pos_tex_last',self.tex1)

        self.output=self.tex1
        self.state=0
        self.time=0

    def reset_textures(self, tex0, tex1):
        self.tex0=tex0
        self.tex1=tex1
        self.quadA.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadA.setShaderInput('pos_tex_last',self.tex1)
        self.quadB.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadB.setShaderInput('pos_tex_last',self.tex1)
        self.quadC.setShaderInput('pos_tex_prelast',self.tex0)
        self.quadC.setShaderInput('pos_tex_last',self.tex1)
        self.state=0

    def debug_getPixel(self, x, y):
        size_x=self.tex0.getXSize()
        size_y=self.tex0.getYSize()
        p=PfmFile()
        p.clear(x_size=size_x, y_size=size_y, num_channels=4)
        self.output.store(p)
        return p.getPoint4(x,y)

    def flipBuffers(self):
        #print self.state
        if self.state==0:
            self.state=1
            self.quadA.setShaderInput('pos_tex_prelast',self.tex0)
            self.quadA.setShaderInput('pos_tex_last',self.tex1)
            self.output=self.texA
            self.buffA.setActive(True)
            self.buffB.setActive(False)
            self.buffC.setActive(False)
        elif self.state==1:
            self.state=2
            self.quadB.setShaderInput('pos_tex_prelast',self.tex1)
            self.quadB.setShaderInput('pos_tex_last',self.texA)
            self.output=self.texB
            self.buffA.setActive(False)
            self.buffB.setActive(True)
            self.buffC.setActive(False)
        elif self.state==2:
            self.state=3
            self.quadC.setShaderInput('pos_tex_prelast',self.texA)
            self.quadC.setShaderInput('pos_tex_last',self.texB)
            self.output=self.texC
            self.buffA.setActive(False)
            self.buffB.setActive(False)
            self.buffC.setActive(True)
        elif self.state==3:
            self.state=4
            self.quadA.setShaderInput('pos_tex_prelast',self.texB)
            self.quadA.setShaderInput('pos_tex_last',self.texC)
            self.output=self.texA
            self.buffA.setActive(True)
            self.buffB.setActive(False)
            self.buffC.setActive(False)
        elif self.state==4:
            self.state=5
            self.quadB.setShaderInput('pos_tex_prelast',self.texA)
            self.quadB.setShaderInput('pos_tex_last',self.texC)
            self.output=self.texB
            self.buffA.setActive(False)
            self.buffB.setActive(True)
            self.buffC.setActive(False)
        elif self.state==5:
            self.state=6
            self.quadA.setShaderInput('pos_tex_prelast',self.texC)
            self.quadA.setShaderInput('pos_tex_last',self.texB)
            self.output=self.texA
            self.buffA.setActive(True)
            self.buffB.setActive(False)
            self.buffC.setActive(False)
        elif self.state==6:
            self.state=7
            self.quadC.setShaderInput('pos_tex_prelast',self.texB)
            self.quadC.setShaderInput('pos_tex_last',self.texA)
            self.output=self.texC
            self.buffA.setActive(False)
            self.buffB.setActive(False)
            self.buffC.setActive(True)
        elif self.state==7: #at this point the sequence repeats
            self.state=5
            self.quadB.setShaderInput('pos_tex_prelast',self.texA)
            self.quadB.setShaderInput('pos_tex_last',self.texC)
            self.output=self.texB
            self.buffA.setActive(False)
            self.buffB.setActive(True)
            self.buffC.setActive(False)

    def makeBuffer(self, tex, shader, shader_inputs={}, bits=32):
        root=NodePath("bufferRoot")
        x=self.tex0.getXSize()
        y=self.tex0.getYSize()
        #buffer was empty if it has x1 size in any direction
        #may be a driver bug?
        #not important, the texture should have 256x256 anyway
        if x<2:
            x=2
        if y<2:
            y=2
        props = FrameBufferProperties()
        props.setRgbaBits(bits,bits, bits, bits)
        props.setSrgbColor(False)
        props.setFloatColor(True)
        tex.setWrapU(Texture.WM_clamp)
        tex.setWrapV(Texture.WM_clamp)
        tex.setMagfilter(SamplerState.FT_nearest)
        tex.setMinfilter(SamplerState.FT_nearest)
        tex.setFormat(Texture.F_srgb_alpha)
        buff=base.win.makeTextureBuffer("buff", x, y, tex, to_ram=False, fbp=props)
        buff.setClearValue(GraphicsOutput.RTP_color, (0.0, 0.0, 0.0, 0.0)) #??
        buff.setSort(-100)
        #the camera for the buffer
        cam=base.makeCamera(win=buff)
        cam.reparentTo(root)
        cam.setPos(x/2,y/2,100)
        cam.setP(-90)
        lens = OrthographicLens()
        lens.setFilmSize(x, y)
        cam.node().setLens(lens)
        #plane with the texture
        cm = CardMaker("plane")
        cm.setFrame(0, x, 0, y)
        quad=root.attachNewNode(cm.generate())
        quad.lookAt(0, 0, -1)
        quad.setDepthTest(0)
        quad.setDepthWrite(0)
        ShaderAttrib.make(shader)
        quad.setAttrib(ShaderAttrib.make(shader))
        #pass shader inputs
        for name, value in shader_inputs.items():
            quad.setShaderInput(str(name), value)
        #return the buff and quad
        return buff, quad, cam

    def setShaderInputsDict(self, shader_inputs_dict):
        for name, value in shader_inputs_dict.items():
            self.setShaderInput(name, value)

    def setShaderInput(self, name, value):
        self.quadA.setShaderInput(str(name), value)
        self.quadB.setShaderInput(str(name), value)
        self.quadC.setShaderInput(str(name), value)

    def setShader(self, shader):
        self.quadA.setShader(shader)
        self.quadB.setShader(shader)
        self.quadC.setShader(shader)

    def updateEmitterMatrix(self):
        emitter_data= PTA_LVecBase4f()
        for emitter in self.emitters:
            mat=emitter.getMat(render)
            for i in range(4):
                emitter_data.pushBack(mat.getRow(i))
        self.setShaderInput('emitter_data', emitter_data)

    def remove(self):
        engine = base.win.getGsg().getEngine()
        self.buffA.clearRenderTextures()
        self.buffB.clearRenderTextures()
        self.buffC.clearRenderTextures()
        engine.removeWindow(self.buffA)
        engine.removeWindow(self.buffB)
        engine.removeWindow(self.buffC)
        self.quadA.removeNode()
        self.quadB.removeNode()
        self.quadC.removeNode()
        self.camA.removeNode()
        self.camB.removeNode()
        self.camC.removeNode()
        self.tex0=None
        self.tex1=None
        self.texA=None
        self.texB=None
        self.texC=None
        self.output=None
        self.emitters=None


    def update(self, dt):
        self.time+=dt
        if self.time >= self.update_speed:
            self.time=0
            self.updateEmitterMatrix()
            self.flipBuffers()
        else:
            self.buffA.setActive(False)
            self.buffB.setActive(False)
            self.buffC.setActive(False)
