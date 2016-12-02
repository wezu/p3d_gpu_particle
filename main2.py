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

        #movable emitter
        #give it something to move around
        axis=render.attachNewNode('axis')
        self.emitter=loader.loadModel('smiley')
        self.emitter.reparentTo(axis)
        self.emitter.setPos(100, 0, 0)
        interval=axis.hprInterval(5, (360, 0, 0), startHpr=(0, 0, 0))
        interval.loop()
        #emitter.hide()

        #load particles and link them to a moving emitter
        self.particle=Wfx(update_speed=60.0)
        self.particle.load("default.wfx")
        #self.particle.set_emitter_node(emitter_id=0, node=self.emitter)
        self.particle.start()

        #self.particle.set_emitter_force(0, Vec3(0.5, 0, 0))

        #space stops the fx animation
        self.accept("space",self.particle.set_pause)

        taskMgr.add(self.do_wind, 'do_wind')

    def do_wind(self, task):
        v=self.emitter.getPos(render)*0.005
        v[2]=-1
        #print v
        self.particle.set_global_force(v)
        return task.again

d=Demo()
base.run()
