"""
Wezu Effects (Wfx) is a gpu particle rendering system for Panda3D
"""
from panda3d.core import *
import json

__author__ = "wezu"
__copyright__ = "Copyright 2016"
__license__ = "ISC"
__version__ = "0.21"
__email__ = "wezu.dev@gmail.com"
__status__ = "Work In Progress"

class Wfx():
    def __init__(self,
                num_emitters=1,
                update_speed=60.0,
                use_aux_texture=False,
                camera=None,
                root=None,
                window=None,
                vector_field=None,
                voxel_size=Vec3(200, 200, 200),
                heightmap_resolution=0,
                world_size=100,
                heightmap_mask=17,
                heightmap_padding=0.5,
                collision_depth=1.0,
                velocity_constant=0.05):
        """
        Setup

        Args:
            update_speed (float)     - how fast will the simulation run in FPS
            use_aux_texture(bool)    - do the particles need to render to a second render target
            camera(NodePath/Camera)  - the default scene camera
            root(NodePath)           - root node for the simulation
            window(GraphicsOutput)   - the window to display the particles in (needed only for it's size)
            heightmap_resolution(int)- if set to 0 disables rendering a heightmap(default) else the size of the heightmap
            world_size(float)        - the size of the heightmap in world space units
            heightmap_mask(int)      - camera bitmask value (0-32) for rendering collision heightmap
            heightmap_padding        - an offset for rendering the heightmap (should be equal to hals of the size of particles)
            collision_depth          - how far are particles tested for collisions
            velocity_constant        - all forces are multiplied by this value (sort of... )
        """
        #setup
        self.num_emitters=num_emitters
        self.use_aux_texture=int(use_aux_texture)
        self.world_size=world_size
        self.use_heightmap_collision=0
        self.heightmap_padding=heightmap_padding
        self.collision_depth=collision_depth
        self.velocity_constant=velocity_constant
        if heightmap_resolution>0:
            self.use_heightmap_collision=1
        self.update_speed=1.0/update_speed
        self.use_vector_field=0
        if vector_field:
            self.vector_field=loader.loadTexture(vector_field)
            self.vector_field.setFormat(Texture.F_rgba32)
            self.use_vector_field=1
        self.voxel_size=voxel_size

        #the shaders are hardcoded now, if you want your own shaders edit the shaders provided
        #or change the path below...
        #the shader that will run the physic simulation
        self.physics_shader_txt=self._read_shader_text('wfx_shaders/physics_v.glsl', 'wfx_shaders/physics_f.glsl')
        #the shader that will draw vertex as textures billbords
        self.particle_shader_txt=self._read_shader_text('wfx_shaders/particle_v.glsl', 'wfx_shaders/particle_f.glsl')
        #the shader that will draw a heighmapt/normal
        self.heightmap_shader_txt=self._read_shader_text('wfx_shaders/heightmap_v.glsl', 'wfx_shaders/heightmap_f.glsl')

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
        self.root.hide(BitMask32.bit(heightmap_mask))
        #the size of the window is needed to generate uv for the particles
        #it may not be base.win if rendering to a smaller off-screen buff
        #for soft particles or something like it
        self.window=base.win
        if window:
            self.window=window

        self.pause=False
        self.ping_pong=None
        self.task=None

        #collisions with heightmap
        if heightmap_resolution>0:
            self.collision_map=WorldHeightMap(heightmap_resolution, world_size, heightmap_mask)

    ###################
    #Private functions:
    ###################

    def _read_shader_text(self, v_shader, f_shader):
        with open(v_shader) as f:
            v = f.read()
        with open(f_shader) as f:
            f = f.read()
        return (v,f)

    def _reload_shaders(self):
        #reloading shaders without writing a include file to hd
        #...needlessly complicated

        #put the values in a dict
        setup={'num_emitters':int(self.num_emitters),
                'aux_tex':int(self.use_aux_texture),
                'use_heightmap':int(self.use_heightmap_collision),
                'height_pad':float(self.heightmap_padding),
                'coll_depth':float(self.collision_depth),
                'velocity_const':float(self.velocity_constant),
                'vector_field':int(self.use_vector_field)}
        #make a string and format it with the values above
        header=('#define WFX_NUM_EMITTERS {num_emitters}\n'
                '#define WFX_AUX_RENDER_TARGET {aux_tex}\n'
                '#define WFX_USE_HEIGHTMAP_COLLISIONS {use_heightmap}\n'
                '#define WFX_HEIGHTMAP_PADDING {height_pad}\n'
                '#define WFX_COLLISION_DEPTH {coll_depth}\n'
                '#define WFX_VELOCITY_CONST {velocity_const}\n'
                '#define WFX_USE_3D_COLLISIONS {vector_field}\n')
        header=header.format(**setup)

        #replace all the '#define import 1' in the shaders with the above
        physics_v=self.physics_shader_txt[0]
        physics_f=self.physics_shader_txt[1]
        particle_v=self.particle_shader_txt[0]
        particle_f=self.particle_shader_txt[1]
        heightmap_v=self.heightmap_shader_txt[0]
        heightmap_f=self.heightmap_shader_txt[1]
        physics_v=physics_v.replace('#define import 1', header)
        physics_f=physics_f.replace('#define import 1', header)
        particle_v=particle_v.replace('#define import 1', header)
        particle_f=particle_f.replace('#define import 1', header)
        heightmap_v=heightmap_v.replace('#define import 1', header)
        heightmap_f=heightmap_f.replace('#define import 1', header)

        #make the shaders
        self.physics_shader = Shader.make(Shader.SL_GLSL,physics_v, physics_f)
        self.particle_shader = Shader.make(Shader.SL_GLSL,particle_v, particle_f)
        self.heightmap_shader = Shader.make(Shader.SL_GLSL,heightmap_v, heightmap_f)

        #apply the shaders if there's something to apply them to
        try:
            state_np = NodePath("state_node")
            state_np.setShader(self.heightmap_shader ,1)
            self.collision_map.cam.node().setInitialState(state_np.getState())
        except AttributeError:
            pass
        try:
            shader_attrib = ShaderAttrib.make(self.particle_shader)
            shader_attrib = shader_attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
            self.root.setAttrib(shader_attrib)
        except AttributeError:
            pass
        try:
            self.ping_pong.setShader(self.physics_shader)
        except AttributeError:
            pass

    def _set_blend(self, node,  mode):
        if mode=='dual':
            node.setTransparency(TransparencyAttrib.MDual, 1)
        elif mode =='add':
            color_attrib = ColorBlendAttrib.make(ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one )
            node.setAttrib(color_attrib)
            node.setBin("fixed", 0)
            node.setDepthTest(True)
            node.setDepthWrite(False)

    def _make_points(self, num_points):
        #print '_make_points', num_points
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

    def _reset_window_size(self, window=None):
        if window:
            self.window=window
        self.root.setShaderInput('screen_size', Vec2(self.window.getXSize(), self.window.getYSize()))

    def _update(self, task):
        dt=globalClock.getDt()
        self.root.setShaderInput('camera_pos', base.camera.getPos(self.root))
        if not self.pause:
            self.ping_pong.update(dt)
        self.root.setShaderInput('pos_tex', self.ping_pong.output)
        return task.again

    ###################
    #Public functions:
    ###################
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
        needed_kwargs={'pos_0','pos_1','mass','size','one_pos','zero_pos','data', 'texture', 'offset', 'props'}

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
                    new_kwargs[name[:-4]].setWrapU(SamplerState.WM_clamp)
                    new_kwargs[name[:-4]].setWrapV(SamplerState.WM_clamp)
                    new_kwargs[name[:-4]].setMagfilter(SamplerState.FT_nearest)
                    new_kwargs[name[:-4]].setMinfilter(SamplerState.FT_nearest)
                    f=new_kwargs[name[:-4]].getFormat()
                    if f== Texture.F_rgb:
                        new_kwargs[name[:-4]].setFormat(Texture.F_rgb32)
                    elif f== Texture.F_rgba:
                        new_kwargs[name[:-4]].setFormat(Texture.F_rgba32)
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
            self.num_emitters=kwargs['data']['num_emitters']
            if 'aux_texture' in kwargs:
                self.use_aux_texture=1
            else:
                self.use_aux_texture=0
            self._reload_shaders() #make sure the inc is written!
            self.current_status=kwargs['data']['status']
            if 'forces' in kwargs['data']:
                self.current_forces=kwargs['data']['forces']
            else:
                self.current_forces=[Vec3(0,0,0) for x in range(self.num_emitters)]
            status=PTA_LVecBase4f()
            for i in range(self.num_emitters):
                v=Vec4(0,0,0,0)
                v[0]=self.current_forces[i][0]
                v[1]=self.current_forces[i][1]
                v[2]=self.current_forces[i][2]
                v[3]=float(self.current_status[i])
                status.pushBack(v)

            shader_inputs={'one_pos':kwargs['one_pos'],
                        'zero_pos':kwargs['zero_pos'],
                        'mass_tex':kwargs['mass'],
                        'size_tex':kwargs['size'],
                        'props_tex':kwargs['props'],
                        'global_force':Vec4(0,0,-1.0,0),
                        'status':status}
            if self.use_heightmap_collision:
                shader_inputs['collision_map']=self.collision_map.get()
                shader_inputs['world_size']=float(self.world_size)
            if self.use_vector_field:
                shader_inputs['voxel_map']=self.vector_field
                shader_inputs['voxel_size']=self.voxel_size
            x=kwargs['one_pos'].getXSize()
            y=kwargs['one_pos'].getYSize()
            #emitters, for now it's all self.root (default to render)
            emitters=[]
            for i in range(self.num_emitters):
                emitters.append(self.root)
            if self.ping_pong is None:
                self.ping_pong=BufferRotator(self.physics_shader, kwargs['pos_0'], kwargs['pos_1'], shader_inputs, emitters, update_speed=self.update_speed)
                #add blending
                dual_blending=(x*y)-kwargs['data']['blend_index']
                #print 'add', kwargs['data']['blend_index']
                self.points_add_blend=self._make_points(kwargs['data']['blend_index'])
                self._set_blend(self.points_add_blend, 'add')
                #mod blending
                self.points_dual_blend=self._make_points(dual_blending)
                self._set_blend(self.points_dual_blend, 'dual')
                #print 'dual', dual_blending
            else:
                self.ping_pong.setShaderInputsDict(shader_inputs)
                self.ping_pong.reset_textures(kwargs['pos_0'], kwargs['pos_1'])

            #shader and inputs
            shader_attrib = ShaderAttrib.make(self.particle_shader)
            shader_attrib = shader_attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
            self.root.setAttrib(shader_attrib)
            self.root.setShaderInput('tex', kwargs['texture'])
            self.root.setShaderInput('one_pos', kwargs['one_pos'])
            self.root.setShaderInput('zero_pos', kwargs['zero_pos'])
            self.root.setShaderInput('offset_tex', kwargs['offset'])
            self.root.setShaderInput('size_tex', kwargs['size'])
            self.root.setShaderInput('props_tex', kwargs['props'])
            self.root.setShaderInput('index_offset', 0.0)
            self.root.setShaderInput('status',status)
            if 'aux_texture' in kwargs:
                self.root.setShaderInput('aux_texture', kwargs['aux_texture'])
            self.points_dual_blend.setShaderInput('index_offset', float(kwargs['data']['blend_index']))


            self.ping_pong.updateEmitterMatrix()
            self.root.setShaderInput('camera_pos', base.camera.getPos(self.root))
            self.root.setShaderInput('pos_tex', self.ping_pong.output)
            self._reset_window_size()
        else:
            print 'error'
            for arg in args:
                print 'arg:', arg
            print kwargs

    def start(self):
        """
        Starts the particle system, call this after calling load()
        """
        self.root.show()
        if self.task is None:
            self.task=taskMgr.add(self._update, 'wfx_update_tsk')

    def set_pause(self):
        """
        Pauses the particle system without hiding anything, use this for 'time stop'
        ..or just set self.pause to True
        """
        self.pause = not self.pause

    def restart(self):
        """
        Restarts the whole system to the initial value (after load() was called)
        """
        self.ping_pong.state=0

    def reset(self):
        """
        Resets the system, removes all values set by load()
        """
        taskMgr.remove(self.task)
        self.points_dual_blend.removeNode()
        self.points_add_blend.removeNode()
        self.ping_pong.remove()
        self.ping_pong=None

    def cleanup(self):
        """
        Removes everything, call this when you now longer need the particle system
        """
        self.reset()
        self.physics_shader=None
        self.particle_shader=None
        self.root=None
        self.window=None

    def set_global_force(self, force):
        """
        Sets a force affecting all particles, force should be vector in world space (list/tuple will also work)
        """
        try:
            self.ping_pong.setShaderInput('global_force', Vec4(force[0], force[1], force[2], 0.0))
        except AttributeError:
            pass

    def set_emitter_force(self, emitter_id, force):
        """
        Sets a local force affecting all particles with a given emitter_id
        """
        try:
            status=PTA_LVecBase4f()
            for i in range(self.num_emitters):
                v=Vec4(0,0,0,0)
                if i == emitter_id:
                    v[0]=force[0]
                    v[1]=force[1]
                    v[2]=force[2]
                    self.current_forces[i][0]=force[0]
                    self.current_forces[i][1]=force[1]
                    self.current_forces[i][2]=force[2]
                else:
                    v[0]=self.current_forces[i][0]
                    v[1]=self.current_forces[i][1]
                    v[2]=self.current_forces[i][2]
                v[3]=float(self.current_status[i])
                status.pushBack(v)
            self.ping_pong.setShaderInput('status',status)
        except AttributeError:
            pass

    def set_emitter_active(self, emitter_id, active):
        """
        Turns on (active=1) or off (active=0) all the particles with a given emitter_id
        """
        try:
            status=PTA_LVecBase4f()
            for i in range(self.num_emitters):
                v=Vec4(0,0,0,0)
                if i == emitter_id:
                    v[3]=float(active)
                    self.current_status[i]=active
                else:
                    v[3]=float(self.current_status[i])
                v[0]=self.current_forces[i][0]
                v[1]=self.current_forces[i][1]
                v[2]=self.current_forces[i][2]
                #print i, v
                status.pushBack(v)
            self.ping_pong.setShaderInput('status',status)
            self.root.setShaderInput('status',status)
        except AttributeError:
            pass

    def set_emitter_on(self, emitter_id):
        """
        Turns on all the particles with a given emitter_id
        """
        self.set_emitter_active(emitter_id, 1.0)

    def set_emitter_off(self, emitter_id):
        """
        Turns off all the particles with a given emitter_id
        """
        self.set_emitter_active(emitter_id, 0.0)

    def set_emitter_node(self, emitter_id, node):
        """
        Links a node with a emitter_id.

        When the node moves or rotates, then the origin of particles
        with that emitter_id moves or rotates with it.
        """
        self.ping_pong.emitters[emitter_id]=node

    def on_window_resize(self):
        """
        Call this function each time the window changes its size!
        """
        self._reset_window_size()



class BufferRotator():
    """
    This is a helper class that switches between 3 texture buffers,
    where each buffer is in turn the output or one of the inputs.
    You don't need to do anything with this class.
    """
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
        if x<2:
            x=2
        if y<2:
            y=2
        props = FrameBufferProperties()
        props.setRgbaBits(bits,bits, bits, bits)
        props.setSrgbColor(False)
        props.setFloatColor(True)
        tex.setWrapU(SamplerState.WM_clamp)
        tex.setWrapV(SamplerState.WM_clamp)
        tex.setMagfilter(SamplerState.FT_nearest)
        tex.setMinfilter(SamplerState.FT_nearest)
        tex.setFormat(Texture.F_rgba32)
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
        #print 'setting input', name, value
        self.quadA.setShaderInput(name, value)
        self.quadB.setShaderInput(name, value)
        self.quadC.setShaderInput(name, value)

    def setShader(self, shader):
        self.quadA.setShader(shader)
        self.quadB.setShader(shader)
        self.quadC.setShader(shader)

    def updateEmitterMatrix(self):
        #emitter_data= PTA_LVecBase4f()
        emitter_data=PTALMatrix4f()
        for emitter in self.emitters:
            mat=emitter.getMat(render)
            emitter_data.pushBack(UnalignedLMatrix4f(mat))
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

class WorldHeightMap():
    """
    This class renders a height/normal map of the world
    The world space normal is in output.xyz the height in output.w
    """
    def __init__(self, resolution, world_size, heightmap_mask, bits=16):
        self.resolution=resolution
        #we render to a flaoting point texture, so we need the right props
        props = FrameBufferProperties()
        props.setRgbaBits(bits,bits, bits, bits)
        props.setSrgbColor(False)
        props.setFloatColor(True)

        self.output=Texture()
        self.output.setWrapU(SamplerState.WM_clamp)
        self.output.setWrapV(SamplerState.WM_clamp)
        self.output.setMagfilter(SamplerState.FT_nearest)
        self.output.setMinfilter(SamplerState.FT_nearest)
        if bits==16:
            self.output.setFormat(Texture.F_rgba16)
        elif bits==32:
            self.output.setFormat(Texture.F_rgba32)
        else:
            self.output.setFormat(Texture.F_rgba)
        self.buffer=base.win.makeTextureBuffer("buff", resolution, resolution, self.output, to_ram=False, fbp=props)
        self.buffer.setClearValue(GraphicsOutput.RTP_color, (0.0, 0.0, 0.0, 0.0)) #??
        self.buffer.setSort(-100)
        #the camera for the buffer
        self.cam=base.makeCamera(win=self.buffer)
        self.cam.reparentTo(render)
        self.cam.setPos(0,0, world_size)
        self.cam.setP(-90)
        lens = OrthographicLens()
        lens.setFilmSize(world_size, world_size)
        self.cam.node().setLens(lens)
        self.cam.node().setCameraMask(BitMask32.bit(heightmap_mask))
        #self.cam.node().showFrustum()

        #apply a shader to the camera
        state_np = NodePath("state_node")
        state_np.setShader(Shader.load(Shader.SLGLSL, "wfx_shaders/heightmap_v.glsl","wfx_shaders/heightmap_f.glsl"),1)
        self.cam.node().setInitialState(state_np.getState())

    def get(self):
        self.buffer.setActive(True)
        return self.output

    def stop(self):
        self.buffer.setActive(False)
