from editor.tex_combine import TextureCombiner

t=TextureCombiner(frame_size=128, num_frames=16)

t.add('tex/smoke2/*.png')

t.write('smoke2.png')
