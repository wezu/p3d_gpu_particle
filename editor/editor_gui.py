from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *

#Helper functions
def _pos2d(x,y):
    return Point3(x,0,-y)

def _rec2d(width, height):
    return (-width, 0, 0, height)

def _resetPivot(frame):
    size=frame['frameSize']
    frame.setPos(-size[0], 0, -size[3])
    frame.flattenLight()


class SinGraphFrame():
    def __init__(self, size, pos, parent, offset=0.0, freq=1.0, multi=1.0, x_offset=0.0):
        tex=loader.loadTexture('editor/ui/graph_line.png')

        self.frame=DirectFrame(frameSize=_rec2d(size[0],size[1]),
                                frameTexture=tex,
                                parent=parent)
        _resetPivot(self.frame)
        self.frame.setPos(_pos2d(pos[0],pos[1]))
        self.frame.setTransparency(TransparencyAttrib.MAlpha)
        self.frame.setShader(Shader.load(Shader.SLGLSL, 'editor/shaders/sin_v.glsl', 'editor/shaders/sin_f.glsl'))
        self.inputs = None
        self.set_inputs(offset, freq, multi, x_offset)

    def set_inputs(self, offset=None, freq=None, multi=None, x_offset=None):
        try:
            offset=float(offset)
        except:
            if self.inputs:
                offset=self.inputs['offset']
            else:
                offset=0.0
        try:
            freq=float(freq)
        except:
            if self.inputs:
                freq=self.inputs['freq']
            else:
               freq=1.0
        try:
            multi=float(multi)
        except:
            if self.inputs:
                multi=self.inputs['multi']
            else:
               multi=1.0
        try:
            x_offset=float(x_offset)
        except:
            if self.inputs:
                x_offset=self.inputs['x_offset']
            else:
               x_offset=0.0
        self.frame.setShaderInput('offset',offset)
        self.frame.setShaderInput('freq',freq)
        self.frame.setShaderInput('multi',multi)
        self.frame.setShaderInput('x_offset',x_offset)

        self.inputs = {'offset':offset, 'freq':freq, 'multi':multi, 'x_offset':x_offset}

class GUI(DirectObject):
    def __init__(self):

        #load fonts
        self.font = loader.loadFont('editor/font/DejaVuSansMono.ttf')
        self.font.setPixelsPerUnit(14)
        self.font.setMinfilter(Texture.FTNearest)
        self.font.setMagfilter(Texture.FTNearest)
        self.font.setNativeAntialias(False)

        #set nodes for gui placement
        self.top_left=pixel2d.attachNewNode('TopLeft')
        self.top_right=pixel2d.attachNewNode('TopRight')
        self.bottom_right=pixel2d.attachNewNode('BottomRight')
        self.bottom_left=pixel2d.attachNewNode('BottomLeft')
        self.top=pixel2d.attachNewNode('Top')
        self.bottom=pixel2d.attachNewNode('Bottom')
        self.left=pixel2d.attachNewNode('Left')
        self.right=pixel2d.attachNewNode('Right')
        self.center=pixel2d.attachNewNode('Center')

        #empty texture used for buttons
        self.blank_tex=loader.loadTexture('editor/ui/blank_32.png')
        #timeouts
        self.timeout={}
        self.release={}

        #active popups
        self.last_popup=None
        self.last_popup_button=None

        self.accept( 'window-event', self._on_window_event)

    def close_popup(self):
        if self.last_popup:
            self.last_popup.destroy()
        if self.last_popup_button:
            self.last_popup_button.destroy()
        self.last_popup=None
        self.last_popup_button=None

    def set_tex(self, widget, texture=None):
        if texture is None:
            texture=self.blank_tex
        widget['frameTexture']=texture

    def set_entry_cursor_pos(self, entry, offset=0, event=None):
        m=event.getMouse()
        pixel_pos=entry.getRelativePoint(render2d, Point3(m[0], 0, m[1]))
        pixel_pos=int(pixel_pos[0]+offset)
        new_cursor_pos= max(0, pixel_pos)//8 #each letter with my font is about 8 pixels width at pixel size 14
        entry.guiItem.setCursorPosition(new_cursor_pos)


    #events
    def _on_click(self, button, texture, cmd, args, repeat=0.2, event=None):
        if event=='again' and button in self.release:
            return
        if event!='again':
            if button in self.release:
                del self.release[button]
        time=globalClock.getRealTime ()
        if button in self.timeout:
            if self.timeout[button] > time - 0.1:
                return
            self.timeout[button] = time
        else:
            self.timeout[button] = time

        if  repeat>0.1:
            if button not in self.release:
                Sequence(Wait(repeat), Func(self._on_click, button, texture, cmd, args, repeat, event='again')).start()
        #set the click texture
        button['frameTexture']=texture
        #return to the default (blank) tex after 0.1 sec
        if args:
            Sequence(Wait(0.1), Func(self.set_tex, button), Wait(0.05), Func(cmd, args)).start()
        else:
            Sequence(Wait(0.1), Func(self.set_tex, button), Wait(0.05), Func(cmd)).start()

    def _on_release(self, button, event=None):
        self.release[button]=True

    def _on_submit(self, text, element, command, event=None):
        if command is not None:
            command(text)

    def _on_window_event(self, window=None):
        if window is not None:
            winX = base.win.getXSize()
            winY = base.win.getYSize()
            self.top_left.setPos(_pos2d(0,0))
            self.top_right.setPos(_pos2d(winX,0))
            self.bottom_right.setPos(_pos2d(winX,winY))
            self.bottom_left.setPos(_pos2d(0,winY))
            self.top.setPos(_pos2d(winX/2,0))
            self.bottom.setPos(_pos2d(winX/2,winY))
            self.left.setPos(_pos2d(0,winY/2))
            self.right.setPos(_pos2d(winX,winY/2))
            self.center.setPos(_pos2d(winX/2,winY/2))

    #functions for creating elements
    def graph_frame(self, size, pos, parent, offset=0.0, freq=1.0, multi=1.0, x_offset=0.0):
        return SinGraphFrame(size, pos, parent, offset, freq, multi, x_offset)

    def scroll_frame(self, pos, size, canvas_size, parent):
        scrolled_frame=DirectScrolledFrame(
                                            canvasSize = _rec2d(canvas_size[0],canvas_size[1]),
                                            frameSize = _rec2d(size[0],size[1]),
                                            parent = parent,
                                            frameColor=(1,1,1,0.0),
                                            verticalScroll_manageButtons=False,
                                            verticalScroll_frameColor=(1,1,1,1.0),
                                            verticalScroll_frameSize=_rec2d(16,128),
                                            verticalScroll_frameTexture='editor/ui/line.png',
                                            verticalScroll_relief=DGG.FLAT,
                                            verticalScroll_resizeThumb=False,
                                            verticalScroll_thumb_relief=DGG.FLAT,
                                            verticalScroll_thumb_frameSize=_rec2d(16,64),
                                            verticalScroll_thumb_frameColor=(1,1,1,1.0),
                                            verticalScroll_thumb_frameTexture='editor/ui/thumb.png'
                                            )
        _resetPivot(scrolled_frame)
        scrolled_frame.setPos(_pos2d(pos[0]+size[0],pos[1]+size[1]))
        scrolled_frame.setTransparency(TransparencyAttrib.MAlpha)
        scrolled_frame.verticalScroll.incButton.hide()
        scrolled_frame.verticalScroll.decButton.hide()

        return scrolled_frame

    def frame(self, texture, pos, parent, state='disabled'):
        tex=loader.loadTexture(texture)
        size=(tex.getXSize(), tex.getYSize())
        text_pos=(12-size[0],size[1]-15)
        new_frame=DirectFrame(frameSize=_rec2d(size[0],size[1]),
                                frameColor=(1,1,1,1),
                                frameTexture=tex,
                                state=state,
                                parent=parent,
                                text_font=self.font,
                                text_scale=14,
                                text_fg=(0.5, 0.623, 1.0, 1.0),
                                text_pos=text_pos,
                                text_align=TextNode.ALeft,
                                text_wordwrap=35,
                                text=''
                                )
        _resetPivot(new_frame)
        new_frame.setPos(_pos2d(pos[0],pos[1]))
        new_frame.setTransparency(TransparencyAttrib.MAlpha)
        return new_frame

    def button(self, texture, pos, parent, command, args=[], repeat=0.0):
        new_button=self.frame(texture, pos, parent, state='normal')
        new_button['frameTexture']=self.blank_tex
        click_tex=loader.loadTexture(texture)
        new_button.bind(DGG.B1PRESS, self._on_click, [new_button, click_tex, command, args, repeat])
        new_button.bind(DGG.B1RELEASE, self._on_release, [new_button])
        return new_button

    def entry(self, text, size, pos, parent, command=None):
        new_entry=DirectEntry(text = text,
                            initialText=text,
                            text_font=self.font,
                            frameSize=_rec2d(size[0],size[1]),
                            frameColor=(1,0,0,0.0),
                            text_scale=14,
                            text_pos=(-size[0],-20+size[1]),
                            focus=0,
                            width=size[0]//14,
                            state=DGG.NORMAL,
                            text_fg=(1.0, 1.0, 1.0, 1.0),
                            command=self._on_submit,
                            focusOutCommand=self._on_submit,
                            parent=parent)
        new_entry['extraArgs']=[new_entry, command]
        new_entry['focusOutExtraArgs']=['', new_entry, command]
        new_entry.setPos(_pos2d(pos[0]+size[0],pos[1]+size[1]))
        #new_entry.guiItem.setBlinkRate(2.0)
        #new_entry.guiItem.getCursorDef().setColor(cfg['ui_color1'], 1)
        new_entry.bind(DGG.B1PRESS, self.set_entry_cursor_pos, [new_entry, size[0]])
        return new_entry

    def txt(self, text, pos, parent):
        new_frame=DirectLabel(frameSize=_rec2d(0,20),
                                parent=parent,
                                text_font=self.font,
                                text_scale=14,
                                text_fg=(1.0, 0.0, 0.0, 1.0),
                                text_align=TextNode.ALeft,
                                text_wordwrap=35,
                                text=text
                                )
        _resetPivot(new_frame)
        new_frame.setPos(_pos2d(pos[0],pos[1]))
        new_frame.setTransparency(TransparencyAttrib.MAlpha)
        return new_frame

    def popup(self, text=None):
        self.close_popup()
        self.last_popup=self.frame('editor/ui/popup_window.png', (-256, -64), self.center)
        self.last_popup_button=self.button('editor/ui/highlight_2.png', (224, 96), self.last_popup, self.close_popup)
        self.last_popup['text']=text

