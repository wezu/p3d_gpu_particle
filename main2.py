'''Loading paricles system from file'''

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
import random

from wfx import Wfx

class Demo(DirectObject):
    def __init__(self):
        base = ShowBase.ShowBase()

        scene=loader.loadModel('editor/scene/vol_shp')
        scene.reparentTo(render)

        #movable emitter
        #give it something to move around
        axis=render.attachNewNode('axis')
        self.emitter=loader.loadModel('smiley')
        self.emitter.reparentTo(axis)
        self.emitter.setPos(100, 0, 0)
        interval=axis.hprInterval(15, (360, 0, 0), startHpr=(0, 0, 0))
        interval.loop()
        #emitter.hide()
        #scene.reparentTo(axis)

        #load particles and link them to a moving emitter
        self.particle=Wfx(vector_field='vol_shp.txo', velocity_constant=0.005)
        #self.particle=Wfx(update_speed=60.0, heightmap_resolution=1024, world_size=200.0, velocity_constant=0.005)
        self.particle.load("snow2.wfx")
        #self.particle.set_emitter_node(emitter_id=0, node=self.emitter)
        self.particle.start()

        #self.particle.set_emitter_force(0, Vec3(0.1, 0, 0))

        #space stops the fx animation

        self.active=1

        self.accept("space",self.particle.set_pause)

        taskMgr.add(self.do_wind, 'do_wind')

    def flip_active(self):
        if self.active == 1:
            self.active=0
        else:
            self.active=1
        self.particle.set_emitter_active(0, self.active)

    def do_wind(self, task):
        v=self.emitter.getPos(render)*0.004
        v[2]=-1
        #print v
        self.particle.set_emitter_force(0, v)
        return task.again

d=Demo()
base.run()
