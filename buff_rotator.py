from panda3d.core import *

class BufferRotator():
    def __init__(self, shader, tex0, tex1, shader_inputs={}, emitter=None, bits=32, update_speed=None):
        #upadate speed - how often is the who thing run
        if update_speed:
            self.update_speed=update_speed
        else:
            self.update_speed=1.0/60.0

        self.emitter=render
        if emitter:
            self.emitter=emitter

        self.tex0=tex0
        self.tex1=tex1
        self.texA=Texture()
        self.texB=Texture()
        self.texC=Texture()

        self.buffA, self.quadA = self.makeBuffer(self.texA, shader, shader_inputs, bits)
        self.buffB, self.quadB = self.makeBuffer(self.texB, shader, shader_inputs, bits)
        self.buffC, self.quadC = self.makeBuffer(self.texC, shader, shader_inputs, bits)

        self.output=self.tex1
        self.state=0
        self.time=0

    def flipBuffers(self):
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
        buff=base.win.makeTextureBuffer("buff", x, y, tex, fbp=props)
        buff.setClearValue(GraphicsOutput.RTP_color, (0.0, 0.0, 0.0, 0.0)) #??
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
        ShaderAttrib.make(shader)
        quad.setAttrib(ShaderAttrib.make(shader))
        #pass shader inputs
        for name, value in shader_inputs.items():
            quad.setShaderInput(str(name), value)
        #return the buff and quad
        return buff, quad

    def setShaderInputsDict(self, shader_inputs_dict):
        for name, value in shader_inputs_dict.items():
            self.setShaderInput(name, value)

    def setShaderInput(self, name, value):
        self.quadA.setShaderInput(str(name), value)
        self.quadB.setShaderInput(str(name), value)
        self.quadC.setShaderInput(str(name), value)


    def updateEmitterMatrix(self):
        #for emitter in self.emitters:
        mat=self.emitter.getMat(render)
        #print mat
        emitter_data= PTA_LVecBase4f()
        for i in range(4):
            emitter_data.pushBack(mat.getRow(i))
        self.setShaderInput('emitter_data', emitter_data)

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
