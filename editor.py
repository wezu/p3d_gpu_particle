from panda3d.core import loadPrcFileData
loadPrcFileData('', 'textures-power-2 None')
loadPrcFileData('', 'win-size 1024 768')
from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase import ShowBase
from direct.interval.IntervalGlobal import *

from editor.editor_gui import GUI
from editor.pfm_generator import PfmGen
from editor.tex_combine import TextureCombiner
from editor.cmd import *
from wfx import Wfx

from random import randrange, randint, choice, shuffle, random, uniform
import math
import json
import os

class Editor(DirectObject):
    def __init__(self):
        #init ShowBase
        base = ShowBase.ShowBase()
        #base.setBackgroundColor(0.0, 0.0, 0.0, 1)
        #base.disableMouse()
        base.trackball.node().setPos(0, 140, -10)
        base.trackball.node().setHpr(0, 30, 0)

        #init the GUI sub system
        self.gui=GUI()

        #text for the help popups
        self.help_txt=["Particle Pool is the number of available particles, and it's also the size of the texture used internally. The value will be rounded to the nearest a power-of-two size.",
                      "The number (subset) of particles drawn with an alternative blending mode (additive blending). The number must be no larger then the total number of particles (particle pool). The particles not using the alternative blending mode will be drawn with dual alpha blending (MDual).",
                      "Background is the scene geometry loaded as a reference for the particles. The scene is displayed with a simple shader that just uses the first texture and no lights.",
                      "You can add special nodes to the scene, these nodes can be used as movable particle emitters.  The first node added will have a NodeID=1, the second one NodeID=2 and so forth.  NodeID=0 is always 'render'. You'll be able to link each particle with a NodeID later on.",
                      "'Model' can be a string or a Python function or expression returning a string (model path). 'Cmd' is a Python function  or expression, here 'node' is an alias for the model NodePath. Clicking 'X' will remove the node. Check source/readme for more info.",
                      "This is the number of still available, unused particles left in the pool (using the given blend mode).",
                      "This is the currently used blend mode, click to change.",
                      "This setting defines how many particles will be generated using the current setting. The aliases 'number' and 'n' may be used in the fields bellow to get the index of current iteration. ",
                      "The start position relative to the emitter. This should be a Vec3, or a list/tupe of 3 elements (each a float or int). This can also be a Python function or expression that returns data in the given format. The alias 'pos' may be used in the fields bellow to get the position in the current iteration.",
                      "Particle starting velocity, given as a direction vector. This should be a Vec3, or a list/tupe of 3 elements (each a float or int) or a Python function/expression returning valid data. The alias 'vec' may be used in the fields bellow to get the vector in the current iteration.",
                      "Initial life. Life is incremented by 1 each simulation step (1/60seconds). This should be an integer (or a function/expression returning one), negative numbers mean that the particle will be spawned in the future. The alias 'life' may be used in other fields.",
                      "The maximum life of a particle, the time a particle will be displayed given in 1/60sec steps, eg.  max life = 60 will show a particle for 1 second and then reset. This should be an integer (or a function/expression returning one). The alias 'max_life' may be used in other fields.",
                      "Path to the texture used by the particle. If the texture is square it will be used as a static frame, else it will be cut in square frames and used as an animation. The source texture will be cut and merged with other textures and saved in the particle file. Check the readme for more information. ",
                      "The particle emitters can be turned on and off, click to toggle. The current Node can be changed using the arrow buttons.",
                      "The path where the particle file will be saved. This is relative to the editor. If the extension is omitted .wfx will be added automagically. Click 'Write file' to write the file, 'Generate' only generates the particle data.",
                      "You can delete the last particle generated (or even all of them). Type in how many particles (counting from the end) to delete and click 'Remove Last'."]


        #show the setup screen
        self.show_setup()

        #values are stored here
        self.values={}
        self.last_error=""

        self.fx=Wfx()
        #set the size of the texture atlas here
        self.tex_combine=TextureCombiner(frame_size=128, num_frames=16)

        self.gui.popup("This editor is not functional yet. Clicking 'generate' twice will make it explode, node menagement is broken, can't remove generated stuff")

    def exe(self, command, locals=None, expect_vec3=False, expect_int=False, expect_float=False):
        #make sure we can pinpoint 'self' somhow for functions from outside
        glob=globals()
        glob['app']=self
        try:
            r=eval(command, glob, locals)
            if expect_vec3:
                if isinstance(r,LVecBase3f) or isinstance(r,LVecBase3d):
                    return r
                elif (isinstance(r,tuple) or isinstance(r,list)) and len(r)==3:
                    return Vec3(r[0],r[1],r[2])
                else:
                    raise TypeError('Expected a 3-component vector, got: '+str(r))
            elif expect_int:
                if isinstance(r, int):
                    return r
                else:
                    raise TypeError('Expected an int')
            elif expect_float:
                if isinstance(r, float):
                    return r
                else:
                    raise TypeError('Expected a float')
            else:
                return r
        except NameError as e:
            print "Cmd:'",str(command),"' error:",e
            self.last_error = str(command)+': '+str(e)
            if expect_vec3 or expect_int or expect_float:
                return None
            return str(command)
        except Exception as e:
            #print "Command error!"
            #print e
            self.last_error = str(command)+': '+str(e)

    def find_power_of_two_size(self, size):
        x=2
        y=2
        n=1
        while x*y<size:
            if n%2 == 0:
                x*=2
            else:
                y*=2
            n+=1
        return (x,y)

    def set_force(self, force_txt):
        if force_txt =='':
            # this fires for a'focus out' event
            force_txt=self.panel_entry_force.get()
        force=self.exe(force_txt, expect_vec3=True)
        if force is None:
            self.gui.popup("The force must be a vector.\n"+self.last_error)
            return
        self.fx.set_emitter_force(self.current_node, force)

    def next_node(self):
        if self.current_node < len(self.node):
            self.current_node+=1
        self.panel_txt_node_id['text']=str(self.current_node)
        self.panel_txt_active['text']=str(self.active[self.current_node])

    def prev_node(self):
        if self.current_node > 0:
            self.current_node-=1
        self.panel_txt_node_id['text']=str(self.current_node)
        self.panel_txt_active['text']=str(self.active[self.current_node])

    def change_blend_mode(self):
        self.additive_blend = not self.additive_blend
        if self.additive_blend:
            self.panel_txt_blend['text']="additive"
            self.panel_txt_number['text']=str(self.values['particle_left'][1])
        else:
            self.panel_txt_blend['text']="modulate (dual)"
            self.panel_txt_number['text']=str(self.values['particle_left'][0])

    def change_active(self):
        self.active[self.current_node]= not self.active[self.current_node]
        self.panel_txt_active['text']=str(self.active[self.current_node])
        self.fx.set_emitter_active(self.current_node, self.active[self.current_node])

    def generate(self):
        #print "generate"
        #we need
        #zero_pos #position at time =0
        #one_pos #position at time =1
        #start_life #life value at time=0
        #max_life
        #emitter_id
        #mass
        #size
        #offset
        #texture
        #number_of_textures
        #number_of_frames
        #values are packed so:
        #pos_0=Vec4(0.0, 0.0, 0.0, start_life)
        #pos_1=Vec4(0.0, 0.0, 0.0, start_life+1.0)
        #zero_pos=Vec4(x1, y1, z1, emitter_id)
        #one_pos=Vec4(x2, y2, z2, max_life)
        #mass=Vec4(sin_offset, frequency, scale, offset)
        #size=Vec4(sin_offset, frequency, scale, offset)
        # +U = (1.0/number_of_textures)*(tex_offset_id-1)
        #offset=Vec4(+U,+V, 1.0/number_of_textures, number_of_frames)


        number=self.exe(self.panel_entry_repeat.get(), expect_int=True)
        if number is None or number < 1:
            self.gui.popup("'Repeat' must be a positive integer\n"+self.last_error)
            return
        if self.additive_blend:
            particle_left= self.values['particle_left'][1]
        else:
            particle_left= self.values['particle_left'][0]
        if number > particle_left:
            self.gui.popup("Can't generate "+str(number)+" particles, You only have "+str(particle_left)+" particles left!")
            return

        #texture magic
        number_of_frames=self.tex_combine.num_frames
        #we need to know if a new texture was added or an old one is reused
        #first see what we had
        old_tex_num=len(self.tex_combine.known_columns)
        #add the new texture or get an index to something already there
        try:
            tex_offset_id=self.tex_combine.add(self.panel_entry_tex.get())
            num_tex=len(self.tex_combine.known_columns)
            #did we add something? yes? move all the indexes in the old offset tex
            if num_tex > 1 and num_tex > old_tex_num:
                for i in range(self.offset_pfm.num_added):
                    v=self.offset_pfm.get(i)
                    #print v,
                    if v[0]!= 0.0:
                        old_index=round(1.0/float(v[0])-1.0)
                    else:
                        old_index=0.0
                    v[0]=old_index*1.0/float(num_tex)
                    v[2]=1.0/float(num_tex)
                    #print v
                    self.offset_pfm.set(i, v)
                for i in range(self.offset_pfm.num_added_offset):
                    v=self.offset_pfm.get(i+self.offset_pfm.offset)
                    #print v,
                    if v[0]!= 0.0:
                        old_index=round(1.0/float(v[0])-1.0)
                    else:
                        old_index=0.0
                    v[0]=old_index*1.0/float(num_tex)
                    v[2]=1.0/float(num_tex)
                    #print v
                    self.offset_pfm.set(i+self.offset_pfm.offset, v)
        except BaseException as e:
            self.gui.popup('Texture error: '+str(e))
            #print e
            return
        #print 'tex_offset_id', tex_offset_id, 'num_tex',num_tex
        offset=Vec4((1.0/num_tex)*(tex_offset_id-1),0.0, 1.0/num_tex, 16.0)
        #print offset

        emitter_id=self.current_node
        mass=Vec4(self.values['mass_offset'],self.values['mass_freq'],self.values['mass_multi'],self.values['mass_x_offset'])
        size=Vec4(self.values['size_offset'],self.values['size_freq'],self.values['size_multi'],self.values['size_x_offset'])

        #current blending mode, things got mixed up somewhere...
        use_offset=not self.additive_blend


        loop_locals={'number':number}

        for n in range(1, number+1):
            #get the values and check if they are valid
            loop_locals['n']=n
            zero_pos=self.exe(self.panel_entry_pos.get(), loop_locals, expect_vec3=True)
            if zero_pos is None:
                self.gui.popup("'Start Pos' must be a vector.\n"+self.last_error)
                return
            loop_locals['pos']=zero_pos
            vec=self.exe(self.panel_entry_vec.get(), loop_locals, expect_vec3=True)
            if vec is None:
                self.gui.popup("'Start Vec' must be a vector.\n"+self.last_error)
                return
            loop_locals['vec']=vec
            one_pos=zero_pos+vec
            start_life=self.exe(self.panel_entry_life.get(), loop_locals, expect_int=True)
            if start_life is None:
                self.gui.popup("'Life' must be an int.\n"+self.last_error)
                return
            loop_locals['life']=start_life
            max_life=self.exe(self.panel_entry_max_life.get(), loop_locals, expect_int=True)
            if max_life is None:
                self.gui.popup("'Max Life' must be an int.\n"+self.last_error)
                return
            loop_locals['max_life']=max_life
            #write the values
            #print 'pos_0'
            self.pos_0_pfm.add(0.0, 0.0, 0.0, start_life, offset=use_offset)
            #print 'pos_1'
            self.pos_1_pfm.add(0.0, 0.0, 0.0, start_life+1.0, offset=use_offset)
            #print 'zero_pos'
            self.zero_pos_pfm.add(zero_pos, self.current_node, offset=use_offset)
            #print 'one_pos'
            self.one_pos_pfm.add(one_pos,max_life, offset=use_offset)
            #print 'mass'
            self.mass_pfm.add(mass, offset=use_offset)
            #print 'size'
            self.size_pfm.add(size, offset=use_offset)
            #print 'offset'
            self.offset_pfm.add(offset, offset=use_offset)

        data={'num_emitters':len(self.node)+1,
                'status':self.active,
                'blend_index':self.values['blending_pool']}
        self.fx.load(pos_0=self.pos_0_pfm.to_texture(),
                    pos_1=self.pos_1_pfm.to_texture(),
                    mass=self.mass_pfm.to_texture(),
                    size=self.size_pfm.to_texture(),
                    one_pos=self.one_pos_pfm.to_texture(),
                    zero_pos=self.zero_pos_pfm.to_texture(),
                    data=data,
                    texture=self.tex_combine.to_texture(),
                    offset=self.offset_pfm.to_texture()
                    )

        for i, node in enumerate(self.node):
            print i+1, node
            self.fx.set_emitter_node(i+1, node)
        self.fx.start()

        #particle left
        if self.additive_blend:
            id=1
        else:
            id=0
        self.values['particle_left'][id]-=n # 'n' is used not 'number', the actual loop count
        self.panel_txt_number['text']=str(self.values['particle_left'][id])

        self.panel_entry_del.set(str(n))

    def write_file(self):
        #print "write_file"
        write_to=self.panel_entry_save.get()
        #write the pfm do hd
        self.pos_0_pfm.write('pos_0.pfm')
        self.pos_1_pfm.write('pos_1.pfm')
        self.one_pos_pfm.write('one_pos.pfm')
        self.zero_pos_pfm.write('zero_pos.pfm')
        self.mass_pfm.write('mass.pfm')
        self.size_pfm.write('size.pfm')
        self.offset_pfm.write('offset.pfm')
        self.tex_combine.write('texture.png')

        #pack the pfm to a multifile
        mf = Multifile()
        mf.openWrite(write_to)

        fn=Filename('pos_0.pfm')
        fn.setBinary()
        mf.addSubfile('pos_0.pfm', fn, 9)

        fn=Filename('pos_1.pfm')
        fn.setBinary()
        mf.addSubfile('pos_1.pfm', fn, 9)

        fn=Filename('one_pos.pfm')
        fn.setBinary()
        mf.addSubfile('one_pos.pfm', fn, 9)

        fn=Filename('zero_pos.pfm')
        fn.setBinary()
        mf.addSubfile('zero_pos.pfm', fn, 9)

        fn=Filename('mass.pfm')
        fn.setBinary()
        mf.addSubfile('mass.pfm', fn, 9)

        fn=Filename('size.pfm')
        fn.setBinary()
        mf.addSubfile('size.pfm', fn, 9)

        fn=Filename('offset.pfm')
        fn.setBinary()
        mf.addSubfile('offset.pfm', fn, 9)

        fn=Filename('texture.png')
        fn.setBinary()
        mf.addSubfile('texture.png', fn, 0)

        #write some config vars to the mf
        data=json.dumps({'num_emitters':len(self.node)+1, 'status':self.active, 'blend_index':self.values['blending_pool']})
        #print data
        data_ss=StringStream()
        data_ss.setData(data)
        mf.addSubfile('data.txt', data_ss, 9)

        mf.flush()
        #remove the temp pfms
        os.remove('pos_0.pfm')
        os.remove('pos_1.pfm')
        os.remove('one_pos.pfm')
        os.remove('zero_pos.pfm')
        os.remove('mass.pfm')
        os.remove('size.pfm')
        os.remove('offset.pfm')
        os.remove('texture.png')



    def del_particles(self):
        numer_to_delete=self.exe(self.panel_entry_del.get(), expect_int=True)
        if numer_to_delete is None:
            self.gui.popup("To delete particles you must provide a valid number of particles to delete. "+self.last_error)
            return
        use_offset=not self.additive_blend
        self.pos_0_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.pos_1_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.one_pos_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.zero_pos_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.mass_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.size_pfm.remove_last(numer_to_delete, offset=use_offset)
        self.offset_pfm.remove_last(numer_to_delete, offset=use_offset)


        data={'num_emitters':len(self.node)+1,
                'status':self.active,
                'blend_index':self.values['blending_pool']}
        self.fx.load(pos_0=self.pos_0_pfm.to_texture(),
                    pos_1=self.pos_1_pfm.to_texture(),
                    mass=self.mass_pfm.to_texture(),
                    size=self.size_pfm.to_texture(),
                    one_pos=self.one_pos_pfm.to_texture(),
                    zero_pos=self.zero_pos_pfm.to_texture(),
                    data=data,
                    texture=self.tex_combine.to_texture(),
                    offset=self.offset_pfm.to_texture()
                    )

        if self.additive_blend:
            id=1
        else:
            id=0
        self.values['particle_left'][id]+=numer_to_delete
        self.panel_txt_number['text']=str(self.values['particle_left'][id])
        self.panel_entry_del.set('0')

    def freq_plus(self):
        self.graph_freq_entry.set(str(self.graph.inputs['freq']+0.05))
        self.update_graph()

    def freq_minus(self):
        self.graph_freq_entry.set(str(self.graph.inputs['freq']-0.05))
        self.update_graph()

    def offset_plus(self):
        self.graph_offset_entry.set(str(self.graph.inputs['offset']+0.05))
        self.update_graph()

    def offset_minus(self):
        self.graph_offset_entry.set(str(self.graph.inputs['offset']-0.05))
        self.update_graph()

    def xoffset_plus(self):
        self.graph_xoffset_entry.set(str(self.graph.inputs['x_offset']+0.05))
        self.update_graph()

    def xoffset_minus(self):
        self.graph_xoffset_entry.set(str(self.graph.inputs['x_offset']-0.05))
        self.update_graph()

    def multi_plus(self):
        self.graph_multi_entry.set(str(self.graph.inputs['multi']+0.05))
        self.update_graph()

    def multi_minus(self):
        self.graph_multi_entry.set(str(self.graph.inputs['multi']-0.05))
        self.update_graph()

    def update_graph(self, vale=None):
        #get the values
        freq=self.graph_freq_entry.get()
        offset=self.graph_offset_entry.get()
        multi=self.graph_multi_entry.get()
        x_offset=self.graph_xoffset_entry.get()
        self.graph.set_inputs(offset, freq, multi, x_offset)
        #these values are safe, float and what is actualy used
        start=math.sin(self.graph.inputs['offset']*math.pi*self.graph.inputs['freq'])*self.graph.inputs['multi'] + self.graph.inputs['x_offset']
        mid=math.sin((0.5+self.graph.inputs['offset'])*math.pi*self.graph.inputs['freq'])*self.graph.inputs['multi'] + self.graph.inputs['x_offset']
        end=math.sin((1.0+self.graph.inputs['offset'])*math.pi*self.graph.inputs['freq'])*self.graph.inputs['multi'] + self.graph.inputs['x_offset']
        self.graph_txt_start['text']=str(round(start, 10))
        self.graph_txt_mid['text']=str(round(mid, 10))
        self.graph_txt_end['text']=str(round(end, 10))


    def hide_graph_editor(self):
        self.graph_frame.hide()
        self.show_panel()
        self.values[self.graph_mode+'_offset']=self.graph.inputs['offset']
        self.values[self.graph_mode+'_freq']=self.graph.inputs['freq']
        self.values[self.graph_mode+'_multi']=self.graph.inputs['multi']
        self.values[self.graph_mode+'_x_offset']=self.graph.inputs['x_offset']

    def show_graph_editor(self):
        self.graph_frame=self.gui.frame('editor/ui/graph_panel.png', (520,8), self.gui.top_left)
        self.graph=self.gui.graph_frame((512, 512), (-512,0), self.graph_frame, offset=0.0, freq=0.5, multi=4.0, x_offset=-1.0)
        #buttons
        self.graph_freq_plus=self.gui.button('editor/ui/highlight_3.png', (218, 32), self.graph_frame, self.freq_plus, repeat=0.2)
        self.graph_freq_minus=self.gui.button('editor/ui/highlight_3.png', (218, 48), self.graph_frame, self.freq_minus, repeat=0.2)

        self.graph_offset_plus=self.gui.button('editor/ui/highlight_3.png', (218, 96), self.graph_frame, self.offset_plus, repeat=0.2)
        self.graph_offset_minus=self.gui.button('editor/ui/highlight_3.png', (218, 112), self.graph_frame, self.offset_minus, repeat=0.2)

        self.graph_multi_plus=self.gui.button('editor/ui/highlight_3.png', (218, 160), self.graph_frame, self.multi_plus, repeat=0.2)
        self.graph_multi_minus=self.gui.button('editor/ui/highlight_3.png', (218, 176), self.graph_frame, self.multi_minus, repeat=0.2)

        self.graph_xoffset_plus=self.gui.button('editor/ui/highlight_3.png', (218, 224), self.graph_frame, self.xoffset_plus, repeat=0.2)
        self.graph_xoffset_minus=self.gui.button('editor/ui/highlight_3.png', (218, 240), self.graph_frame, self.xoffset_minus, repeat=0.2)
        self.graph_done_button=self.gui.button('editor/ui/highlight_2.png', (96, 464), self.graph_frame, self.hide_graph_editor)
        #entries
        self.graph_freq_entry=self.gui.entry('0.5', (210, 32), (7,32), self.graph_frame, command=self.update_graph)
        self.graph_offset_entry=self.gui.entry('0.0', (210, 32), (7,96), self.graph_frame, command=self.update_graph)
        self.graph_multi_entry=self.gui.entry('1.0', (210, 32), (7,160), self.graph_frame, command=self.update_graph)
        self.graph_xoffset_entry=self.gui.entry('0.0', (210, 32), (7,224), self.graph_frame,command=self.update_graph)
        #text
        self.graph_txt_start=self.gui.txt("0", (96, 288),self.graph_frame)
        self.graph_txt_mid=self.gui.txt("0", (96, 320),self.graph_frame)
        self.graph_txt_end=self.gui.txt("0", (96, 352),self.graph_frame)


        self.update_graph()

    def show_mass_editor(self):
        self.graph_mode='mass'
        self.panel_frame.hide()
        try:
            self.graph_frame.show()
        except AttributeError:
            self.show_graph_editor()
        self.graph_freq_entry.set(str(self.values[self.graph_mode+'_freq']))
        self.graph_offset_entry.set(str(self.values[self.graph_mode+'_offset']))
        self.graph_multi_entry.set(str(self.values[self.graph_mode+'_multi']))
        self.graph_xoffset_entry.set(str(self.values[self.graph_mode+'_x_offset']))
        self.update_graph()

    def show_size_editor(self):
        self.graph_mode='size'
        self.panel_frame.hide()
        try:
            self.graph_frame.show()
        except AttributeError:
            self.show_graph_editor()
        self.graph_freq_entry.set(str(self.values[self.graph_mode+'_freq']))
        self.graph_offset_entry.set(str(self.values[self.graph_mode+'_offset']))
        self.graph_multi_entry.set(str(self.values[self.graph_mode+'_multi']))
        self.graph_xoffset_entry.set(str(self.values[self.graph_mode+'_x_offset']))
        self.update_graph()

    def apply_setup(self):
        error_msg=''
        try:
            #alt blending, number
            blending_pool=self.exe(self.setup_blend_entry.get())
            if not isinstance(blending_pool, float) and not isinstance(blending_pool, int):
                error_msg+='Alt. Blending is not a valid number!\n'
            #Alt. Blending must be a positive number
            if blending_pool<0:
                error_msg+='Alt. Blending must be a positive number\n'
            #particle pool, must be a number
            particle_pool=self.exe(self.setup_res_entry.get())
            if isinstance(particle_pool, float) or isinstance(particle_pool, int):
                buff_size=self.find_power_of_two_size(particle_pool)
                self.values['particle_pool']=buff_size[0]*buff_size[1]
            else:
                error_msg+='Particle Pool is not a valid number!\n'
            #Alt. Blending can't be larger then Particle Pool!
            if blending_pool>self.values['particle_pool']:
                error_msg+="Alt. Blending can't be larger then Particle Pool!\n"
            #store blending pool
            self.values['blending_pool']=blending_pool

            #background
            if error_msg=='':
                background=self.exe(self.setup_background_entry.get())
                try:
                    self.background=loader.loadModel(background)
                    self.background.reparentTo(render)
                except Exception as e:
                    error_msg+=str(e)
                #nodes
                self.node=[]
                for node in self.nodes:
                    try:
                        model=self.exe(node['model_entry'].get())
                        node_model=loader.loadModel(model)
                        node_model.reparentTo(render)
                        self.node.append(node_model)
                        self.exe(node['cmd_entry'].get(), {'node':self.node[-1]})
                    except Exception as e:
                        error_msg+=str(e)
        except:
            pass
        #show the main panel and init all the toys
        if error_msg=='':
            self.setup_frame.hide()
            self.show_panel()
            self.values['particle_left']=[self.values['particle_pool']-self.values['blending_pool'], self.values['blending_pool']]
            self.values['mass_offset']=0.0
            self.values['mass_freq']=-0.5
            self.values['mass_multi']=0.5
            self.values['mass_x_offset']= 0.05
            self.values['size_offset']=-0.4
            self.values['size_freq']=0.8
            self.values['size_multi']=2.0
            self.values['size_x_offset']=2.05

            self.panel_txt_number['text']=str(self.values['particle_left'][0])
            #setup all the pfm generators
            self.pos_0_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.pos_1_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.one_pos_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.zero_pos_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.mass_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.size_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            self.offset_pfm=PfmGen(buff_size[0], buff_size[1], self.values['blending_pool'])
            #print self.values
        else:
            self.gui.popup(error_msg)

    def show_panel(self):
        try:
            self.panel_frame.show()
        except AttributeError:
            #background
            self.panel_frame=self.gui.frame('editor/ui/panel_background.png', (0,0), self.gui.top_left)

            #help buttons
            self.panel_help_number=self.gui.button('editor/ui/highlight_1.png', (480, 0), self.panel_frame, self.gui.popup, [self.help_txt[5]])
            self.panel_help_blend=self.gui.button('editor/ui/highlight_1.png', (992, 0), self.panel_frame, self.gui.popup, [self.help_txt[6]])
            self.panel_help_repeat=self.gui.button('editor/ui/highlight_1.png', (992, 32), self.panel_frame, self.gui.popup, [self.help_txt[7]])
            self.panel_help_pos=self.gui.button('editor/ui/highlight_1.png', (992, 64), self.panel_frame, self.gui.popup, [self.help_txt[8]])
            self.panel_help_vec=self.gui.button('editor/ui/highlight_1.png', (992, 96), self.panel_frame, self.gui.popup, [self.help_txt[9]])
            self.panel_help_life=self.gui.button('editor/ui/highlight_1.png', (992,128), self.panel_frame, self.gui.popup, [self.help_txt[10]])
            self.panel_help_max_life=self.gui.button('editor/ui/highlight_1.png', (992,160), self.panel_frame, self.gui.popup, [self.help_txt[11]])
            self.panel_help_texture=self.gui.button('editor/ui/highlight_1.png', (992, 192), self.panel_frame, self.gui.popup, [self.help_txt[12]])
            self.panel_help_active=self.gui.button('editor/ui/highlight_1.png', (992, 256), self.panel_frame, self.gui.popup, [self.help_txt[13]])
            self.panel_help_save=self.gui.button('editor/ui/highlight_1.png', (992, 288), self.panel_frame, self.gui.popup, [self.help_txt[14]])
            self.panel_help_del=self.gui.button('editor/ui/highlight_1.png', (992, 224), self.panel_frame, self.gui.popup, [self.help_txt[15]])

            #entries
            self.panel_entry_repeat=self.gui.entry('2048', (864, 32), (128,32), self.panel_frame)
            self.panel_entry_pos=self.gui.entry('Vec3(0.0, 0.0, 0.0)', (832, 32), (160,64), self.panel_frame)
            self.panel_entry_vec=self.gui.entry('Vec3(uniform(-0.1, 0.1), uniform(-0.1, 0.1), 0.0)', (832, 32), (160,96), self.panel_frame)
            self.panel_entry_life=self.gui.entry('randint(-512, 0)', (827, 32), (165,128), self.panel_frame)
            self.panel_entry_max_life=self.gui.entry('randint(10.0, 50.0)', (832, 32), (160,160), self.panel_frame)
            self.panel_entry_tex=self.gui.entry('tex/fire2.png', (864, 32), (128,192), self.panel_frame)
            self.panel_entry_save=self.gui.entry('default.wfx', (384, 32), (608,288), self.panel_frame)
            self.panel_entry_del=self.gui.entry('0', (160, 32), (780,224), self.panel_frame)
            self.panel_entry_force=self.gui.entry('Vec3(0.0, 0.0,-1.0)', (408, 32), (355,256), self.panel_frame, command=self.set_force)

            #buttons
            self.panel_button_blend=self.gui.button('editor/ui/highlight_7.png', (517, 0), self.panel_frame, self.change_blend_mode)
            self.panel_button_mass=self.gui.button('editor/ui/highlight_6.png', (0, 224), self.panel_frame, self.show_mass_editor)
            self.panel_button_size=self.gui.button('editor/ui/highlight_6.png', (256, 224), self.panel_frame, self.show_size_editor)
            self.panel_button_generate=self.gui.button('editor/ui/highlight_6.png', (0, 288), self.panel_frame, self.generate)
            self.panel_button_save=self.gui.button('editor/ui/highlight_6.png', (256, 288), self.panel_frame, self.write_file)
            self.panel_button_active=self.gui.button('editor/ui/highlight_8.png', (768, 256), self.panel_frame, self.change_active)
            self.panel_button_next_id=self.gui.button('editor/ui/highlight_3.png', (224, 256), self.panel_frame, self.next_node, repeat=0.25)
            self.panel_button_prev_id=self.gui.button('editor/ui/highlight_3.png', (224, 272), self.panel_frame, self.prev_node, repeat=0.25)
            self.panel_button_del=self.gui.button('editor/ui/highlight_6.png', (512, 224), self.panel_frame, self.del_particles)


            self.panel_txt_number=self.gui.txt("1000", (224, 0),self.panel_frame)
            self.panel_txt_blend=self.gui.txt("modulate (dual)", (720, 0),self.panel_frame)
            self.panel_txt_node_id=self.gui.txt("0", (160, 256),self.panel_frame)
            self.panel_txt_active=self.gui.txt("True", (896, 256),self.panel_frame)
            self.additive_blend=False
            self.current_node=0
            self.active=[False for x in range(len(self.node)+1)]
            self.active[0]=True

    def show_setup(self):
        #setup frame background
        self.setup_frame=self.gui.frame('editor/ui/config_background.png', (-256,-256), self.gui.center)
        #help
        self.setup_pp_help=self.gui.button('editor/ui/highlight_1.png', (480, 32), self.setup_frame, self.gui.popup, [self.help_txt[0]])
        self.panel_help_blend=self.gui.button('editor/ui/highlight_1.png', (480, 64), self.setup_frame, self.gui.popup, [self.help_txt[1]])
        self.setup_background_help=self.gui.button('editor/ui/highlight_1.png', (480, 96), self.setup_frame, self.gui.popup, [self.help_txt[2]])
        self.setup_add_node_help=self.gui.button('editor/ui/highlight_1.png', (480, 128), self.setup_frame, self.gui.popup, [self.help_txt[3]])
        #entry
        self.setup_res_entry=self.gui.entry('64*64', (256, 32), (224,32), self.setup_frame)
        self.setup_blend_entry=self.gui.entry('64*32', (256, 32), (224,64), self.setup_frame)
        self.setup_background_entry=self.gui.entry('editor/scene/grid1', (320, 32), (160,96), self.setup_frame)
        #adding nodes
        self.nodes_frame=self.gui.scroll_frame((0, 160), (512, 288), (512, 1024),self.setup_frame)
        self.setup_add_node_button=self.gui.button('editor/ui/highlight_4.png', (0, 128), self.setup_frame, self.add_node)
        #node list
        self.nodes=[]

        #done button
        self.setup_done_button=self.gui.button('editor/ui/highlight_2.png', (224, 448), self.setup_frame, self.apply_setup)

    def add_node(self):
        num_nodes=len(self.nodes)
        if num_nodes>15:
            self.gui.popup("Movable nodes are expensive (4x uniform vec4 and a per fragment matrix multiplication), 16 is the maximum number of nodes for this editor. It's for Your own good!")
            return
        node={}
        node['frame']=self.gui.frame('editor/ui/add_node.png', (-500,-1024 +64*num_nodes), self.nodes_frame.getCanvas())
        node['model_entry']=self.gui.entry("choice(['smiley','frowney'])", (352,32), (96, 0), node['frame'])
        node['cmd_entry']=self.gui.entry('move(node,[(0,0,0),(0,0,10)])', (352,32), (96, 32), node['frame'])
        node['help']=self.gui.button('editor/ui/highlight_1.png', (448, 0), node['frame'], self.gui.popup, [self.help_txt[3]])
        node['del']=self.gui.button('editor/ui/highlight_1.png', (448, 32), node['frame'], self.del_node, num_nodes)
        self.nodes.append(node)

    def del_node(self, node_index=0):
        num_nodes=len(self.nodes)
        if num_nodes!=node_index+1:
            self.gui.popup("You can only delete the last (bottommost) Node!")
            return
        #remove the widgets
        self.nodes[node_index]['del'].destroy()
        self.nodes[node_index]['help'].destroy()
        self.nodes[node_index]['cmd_entry'].destroy()
        self.nodes[node_index]['model_entry'].destroy()
        self.nodes[node_index]['frame'].destroy()
        self.nodes.pop()


editor = Editor()
base.run()

