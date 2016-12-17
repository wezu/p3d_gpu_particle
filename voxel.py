from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type none')
from panda3d.core import *
from panda3d.bullet import *
from direct.showbase.ShowBase import ShowBase
from timeit import default_timer as timer
from random import random

def mul3(p1, p2):
    return Point3(p1[0]*p2[0], p1[1]*p2[1], p1[2]*p2[2])

def div3(p1, p2):
    return Point3(p1[0]/p2[0], p1[1]/p2[1], p1[2]/p2[2])

def int_clamp3(v, low, hi):
    r=[]
    for i in range(3):
        r.append(int(max(low[i], min(hi[i], v[i]))))
    return r

class Voxelize():
    def __init__(self, scene, resolution=(128,128,128), world_size=(200, 200, 200) ):

        self.scene=scene
        self.resolution=Point3(*resolution)
        self.world_size=Point3(*world_size)

        #bullet init
        self.world_node = render.attachNewNode('World')
        self.world = BulletWorld()

        #load the scene
        start = timer()
        self.scene=loader.loadModel(scene)
        self.scene.reparentTo(render)

        #make it into a bullet collidable thing
        triMeshData = BulletTriangleMesh()
        for np in self.scene.findAllMatches("**/+GeomNode"):
            geomNode=np.node()
        for i in range(geomNode.getNumGeoms()):
            geom=geomNode.getGeom(i)
            triMeshData.addGeom(geom)

        shape = BulletTriangleMeshShape(triMeshData, dynamic=False)
        geometry = self.world_node.attachNewNode(BulletRigidBodyNode('scene'))
        geometry.node().addShape(shape)
        geometry.node().setMass(0.0)
        self.world.attachRigidBody(geometry.node())
        end = timer()
        print 'Mesh loaded in:', end - start

        #pfm files to render the voxel into
        self.pfm=[]
        for z in range(resolution[2]):
            pfm=PfmFile()
            pfm.clear(x_size=resolution[0], y_size=resolution[1], num_channels=4)
            pfm.fill(Point4(0,0,0,0))
            self.pfm.append(pfm)

        #current position of the collisin ray
        self.world_pos=-self.world_size*0.5

        grid_unit=[]
        for i in range(3):
            grid_unit.append(self.world_size[i]/self.resolution[i])
        self.grid_unit=Point3(*grid_unit)

    def pack_txo(self, filename):
        start = timer()
        tex=Texture()
        tex.setup3dTexture(int(self.resolution[0]), int(self.resolution[1]), int(self.resolution[2]),
                          Texture.T_float, Texture.F_rgba32)
        tex.setFormat(Texture.F_rgba32)
        for z, pfm in enumerate(self.pfm):
            tex.load(pfm, z, 0)
        tex.write(filename, z=0, n=0, write_pages=True, write_mipmaps=False)
        tex.setFormat(Texture.F_rgba32)
        end = timer()
        print 'Texture setup/write:', end - start

    def run_ray_test(self):
        start = timer()
        for i in range(int(self.resolution[0]*self.resolution[1])):
            self.ray_test(Vec3(1, 0, 0))

        self.world_pos=-self.world_size*0.5
        for i in range(int(self.resolution[0]*self.resolution[2])):
            self.ray_test(Vec3(0, 1, 0))

        self.world_pos=-self.world_size*0.5
        for i in range(int(self.resolution[1]*self.resolution[2])):
            self.ray_test(Vec3(0, 0, 1))
        end = timer()
        print 'Collisions run for:', end - start

    def write_to_tex3d(self, world_pos, value):
        u,v,w=self.world2uvw(world_pos)
        #print value
        #old_value=self.pfm[w].getPoint4(u,v)
        #if old_value != Vec4(0,0,0,0):
        #    new_value=Vec3(value[0]+old_value[0], value[1]+old_value[1], value[2]+old_value[2])
        #    new_value.normalize()
        #    value=Vec4(new_value, value[3])
        #value=Vec4(0,0,1, 1)#test value
        self.pfm[w].setPoint4(u,v, value)

    def world2uvw(self, pos):
        uvw=div3(pos+(self.world_size[0]/2),self.grid_unit)
        return int_clamp3(uvw, (0,0,0), self.resolution-Point3(1,1,1))

    def ray_test(self, vec):
        #magic here, just trust in the force!
        i,j = 1,1
        if vec[0]==0:
            i=0
        if vec[2]==0:
            j=2
        from_point=Vec3(self.world_pos)
        to_point=from_point+mul3(vec,self.world_size)
        from_point+=self.grid_unit/2.0
        to_point+=self.grid_unit/2.0

        self.world_pos[i]+=self.grid_unit[i]
        if self.world_pos[i]>=self.world_size[i]*0.5:
            self.world_pos[i]=-self.world_size[i]*0.5
            self.world_pos[j]+=self.grid_unit[j]

        result = self.world.rayTestAll(from_point, to_point)
        for hit in result.getHits():
            #print hit.getNode()
            world_pos= hit.getHitPos()
            normal=hit.getHitNormal()
            self.write_to_tex3d(world_pos, Vec4(normal, 1.0))

        result = self.world.rayTestAll(to_point,from_point)
        for hit in result.getHits():
            world_pos= hit.getHitPos()
            normal=hit.getHitNormal()
            self.write_to_tex3d(world_pos, Vec4(normal, 1.0))


base = ShowBase()
v = Voxelize('editor/scene/vol_shp', resolution=(128,128,128))
v.run_ray_test()
v.pack_txo('vol_shp.txo')

#base.run()
