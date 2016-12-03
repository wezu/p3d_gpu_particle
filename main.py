'''Generating particle data by hand and optional saving it to a file'''


from panda3d.core import loadPrcFileData
loadPrcFileData("", "show-frame-rate-meter  1")
loadPrcFileData("", "sync-video 0")
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "textures-power-2 none")
loadPrcFileData("", "show-buffers 0")
#loadPrcFileData("", "undecorated 1")
#loadPrcFileData("", "win-size 640 360")
#loadPrcFileData("", "task-timer-verbose 1")
#loadPrcFileData("", "pstats-tasks 1")
#loadPrcFileData("", "pstats-gpu-timing 1")
#loadPrcFileData("", "want-pstats 1")
from panda3d.core import *
from direct.showbase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *

from random import randrange, randint, choice, shuffle, random, uniform
import math
import json
import os

from editor.pfm_generator import PfmGen
from editor.tex_combine import TextureCombiner
from wfx import Wfx

class Demo(DirectObject):
    def __init__(self):
        base = ShowBase.ShowBase()

        #movable emitter
        #give it something to move around
        axis=render.attachNewNode('axis')
        emitter=loader.loadModel('smiley')
        emitter.reparentTo(axis)
        emitter.setPos(100, 0, 0)
        interval=axis.hprInterval(5, (360, 0, 0), startHpr=(0, 0, 0))
        interval.loop()

        buff_size=[64, 64]

        self.fx=Wfx()
        #set the size of the texture atlas here
        self.tex_combine=TextureCombiner(frame_size=128, num_frames=16)
        #the pfm generators
        self.pos_0_pfm=PfmGen(buff_size[0], buff_size[1])
        self.pos_1_pfm=PfmGen(buff_size[0], buff_size[1])
        self.one_pos_pfm=PfmGen(buff_size[0], buff_size[1])
        self.zero_pos_pfm=PfmGen(buff_size[0], buff_size[1])
        self.mass_pfm=PfmGen(buff_size[0], buff_size[1])
        self.size_pfm=PfmGen(buff_size[0], buff_size[1])
        self.offset_pfm=PfmGen(buff_size[0], buff_size[1])

        data={'num_emitters':2,'status':[1,1],'blend_index':64*32}

        tex_offset_id=self.tex_combine.add('tex/fire3.png')
        self.current_node=0.0
        mass=Vec4(0.0, 0.5, -2.0, 0.5)
        size=Vec4(-0.4,1.2,10.0,10.05)
        #size=Vec4(0.0, 0.0, 1.0, 16.0)
        num_tex=len(self.tex_combine.known_columns)
        offset=Vec4((1.0/num_tex)*(tex_offset_id-1),0.0, 1.0/num_tex, 16.0)
        zero_pos=Vec3(0.0, 0.0, 0.0)

        for i in range(64*32):
            start_life=float(randint(-200, 0))
            #start_life=0.0
            max_life=uniform(50.0, 100.0)
            #max_life=100.0
            one_pos=Vec3(uniform(-0.5, 0.5), uniform(-0.5, 0.5), 0.0)
            #zero_pos=Vec3(i*0.1, 0.0, 0.0)
            #one_pos=Vec3(i*0.1, 0, 0.1)
            self.pos_0_pfm.add(0.0, 0.0, 0.0, start_life)
            self.pos_1_pfm.add(0.0, 0.0, 0.0, start_life+1.0)

            self.zero_pos_pfm.add(zero_pos, self.current_node)
            self.one_pos_pfm.add(one_pos,max_life)
            self.mass_pfm.add(mass)
            self.size_pfm.add(size)
            self.offset_pfm.add(offset)

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


        tex_offset_id=self.tex_combine.add('tex/smoke3.png')
        num_tex=len(self.tex_combine.known_columns)

        #fix the offsets
        #print self.offset_pfm.num_added
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


        offset=Vec4((1.0/num_tex)*(tex_offset_id-1),0.0, 1.0/num_tex, 16.0)
        size=Vec4(-1.0,0.5,100.0,80.0)
        mass=Vec4(0.0, 0.5, -1.5, 0.0)
        for i in range(64*32):
            start_life=float(randint(-200, 0))
            #start_life=0.0
            max_life=uniform(90.0, 130.0)
            #max_life=100.0
            one_pos=Vec3(uniform(-0.6, 0.6), uniform(-0.6, 0.6), 0.0)
            #zero_pos=Vec3(i*0.1, 0.0, 0.0)
            #one_pos=Vec3(i*0.1, 0, 0.1)
            self.pos_0_pfm.add(0.0, 0.0, 0.0, start_life)
            self.pos_1_pfm.add(0.0, 0.0, 0.0, start_life+1.0)

            self.zero_pos_pfm.add(zero_pos, 0.0)
            self.one_pos_pfm.add(one_pos,max_life)
            self.mass_pfm.add(mass)
            self.size_pfm.add(size)
            self.offset_pfm.add(offset)

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
        #self.fx.set_emitter_off(0)
        #self.fx.set_emitter_on(1)
        #self.fx.set_emitter_node(1, emitter)
        self.fx.start()


        self.accept("space",self.fx.set_pause)
        self.write_file('default.wfx')

    def write_file(self, write_to):
        print "write_file"
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
        data=json.dumps({'num_emitters':1,'status':[1],'blend_index':64*32})
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

d=Demo()
base.run()
