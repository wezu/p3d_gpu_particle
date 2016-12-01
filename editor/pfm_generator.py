from panda3d.core import *

class PfmGen():
    def __init__(self, x_size, y_size, offset=0, fill=None):
        #max size
        self.x_size=x_size
        self.y_size=y_size
        #current coords
        self.x=0
        self.y=0
        self.offset=offset
        self.x_offset, self.y_offset=self._index2xy(offset)
        self.num_added=0
        self.num_added_offset=0
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

    def set_offset(self, offset):
        self.offset=offset
        self.x_offset, self.y_offset=self._index2xy(offset)

    def add(self, value, y_value=None, z_value=None, w_value=None, offset=False):
        if offset:
            x=self.x_offset
            y=self.y_offset
        else:
            x=self.x
            y=self.y
        if y>=self.y_size:
            raise IndexError
        #if y,z and w are given then value must be x
        if y_value is not None and z_value is not None and w_value is not None:
            value=Vec4(value, y_value, z_value, w_value)
        #if just y is given then value is a vec3 and y is the 4th component of a vec4
        if y_value is not None and z_value is None and w_value is None:
            value=Vec4(value[0],value[1],value[2], y_value)
        self.pfm.setPoint4(x, y, value)
        #print self.x, self.y, value
        if offset:
            self.x_offset+=1
            if self.x_offset>=self.x_size:
                self.y_offset+=1
                self.x_offset=0
            self.num_added_offset+=1
        else:
            self.x+=1
            if self.x>=self.x_size:
                self.y+=1
                self.x=0
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


