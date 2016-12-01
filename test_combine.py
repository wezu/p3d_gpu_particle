from editor.tex_combine import TextureCombiner

t=TextureCombiner(frame_size=128, num_frames=16)

t.add('tex/smoke3/*.png')

t.write('smoke3.png')
