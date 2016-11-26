from direct.interval.IntervalGlobal import *
from panda3d.core import *
import random
import math

#some helper functions in global scope
#if you need custom functions add them here
#use camelCase, it's shorter then snake_case and the input filds are short
#The global name 'app' can be used as a pointer to the main editor instance
#eg. app.gui.popup('hello world!')

def loop(node, center=(0,0,0), radius=10, loop_time=5.0):
    axis=render.attachNewNode('axis')
    axis.setPos(center)
    node.reparentTo(axis)
    node.setPos(radius, 0, 0)
    interval=axis.hprInterval(loop_time, (360, 0, 0), startHpr=(0, 0, 0))
    interval.loop()

def move(node, waypoints=[], reverse=True, speed=10.0):
    dummy1=render.attachNewNode('dummy1')
    dummy2=render.attachNewNode('dummy2')
    if reverse:
        waypoints+=waypoints[1::-1]
    seq=Sequence()
    dummy2.setPos(Vec3(waypoints[0][0], waypoints[0][1], waypoints[0][2]))
    for wp in waypoints:
        wp_vec=Vec3(wp[0], wp[1], wp[2])
        dummy1.setPos(wp_vec)
        distance=dummy1.getDistance(dummy2)
        interval=node.posInterval(distance/speed, wp_vec, startPos=dummy2.getPos())
        seq.append(interval)
        dummy2.setPos(dummy1.getPos())
    dummy1.removeNode()
    dummy2.removeNode()
    seq.loop()

def getPos(index):
    pass

def getVec(index):
    pass

def getLife(index):
    pass

def getMaxLife(index):
    pass
