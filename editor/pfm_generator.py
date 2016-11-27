from panda3d.core import *

class PfmGen():
    def __init__(self, x_size, y_size, fill=None):
        #max size
        self.x_size=x_size
        self.y_size=y_size
        #current coords
        self.x=0
        self.y=0
        self.num_added=0
        #the pfm
        self.pfm=PfmFile()
        self.pfm.clear(x_size=x_size, y_size=y_size, num_channels=4)
        if fill:
            self.pfm.fill(fill)

    def debug(self):
        r=[]
        for i in range(self.x_size*self.x_size):
            r.append(self.get(i))
        return r

    def _index2xy(self, index):
        x=index%self.x_size
        y=(index-x)/self.x_size
        if y>=self.y_size:
            raise IndexError
        return x,y

    def get(self, index):
        x,y=self._index2xy(index)
        return self.pfm.modifyPoint4(x,y)

    def set(self, index, value):
        x,y=self._index2xy(index)
        self.pfm.setPoint4(x,y, value)

    def add(self, value, y=None, z=None, w=None):
        if self.y>=self.y_size:
            raise IndexError
        #if y,z and w are given then value must be x
        if y is not None and z is not None and w is not None:
            value=Vec4(value, y, z, w)
        #if just y is given then value is a vec3 and y is the 4th component of a vec4
        if y is not None and z is None and w is None:
            value=Vec4(value[0],value[1],value[2], y)
        self.pfm.setPoint4(self.x, self.y, value)
        self.x+=1
        if self.x>=self.x_size:
            self.y+=1
            self.x=0
        #print self.x, self.y, value
        self.num_added+=1

    def to_texture(self):
        tex=Texture()
        tex.load(self.pfm)
        return tex

    def remove_last(self, n=1):
        for i in range(n):
            self.x-=1
            if self.x<0:
                self.x=self.x_size
                self.y-=0
            if self.y<0:
                self.y=0
                self.x=0
                break
            self.pfm.setPoint4(self.x, self.y, Vec4(0,0,0,0))

    def write(self, path):
        self.pfm.write(path)


