from panda3d.core import *
import glob
import re

class TextureCombiner():
    def __init__(self,frame_size=128, num_frames=16):
        self.frame_size=frame_size
        self.num_frames=num_frames

        self.image=None
        self.known_columns={}

    def sort_nicely(self,  l):
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        l.sort( key=alphanum_key )
        return l

    def add_column(self, column):
        if self.image is None:
            self.image=PNMImage(self.frame_size, self.frame_size*self.num_frames, 4)
            self.image.copyFrom(column)
        else:
            old_size_x=self.image.getReadXSize()
            new_size_x=old_size_x+self.frame_size
            new_image=PNMImage(new_size_x, self.frame_size*self.num_frames, 4)
            new_image.copySubImage(self.image, 0, 0, 0, 0)
            new_image.copySubImage(column, old_size_x, 0, 0, 0)
            self.image=new_image

    def resize_frame(self, frame):
        new_img=PNMImage(self.frame_size, self.frame_size, 4)
        new_img.gaussianFilterFrom(1.0, frame)
        return new_img

    def resize_column(self, column):
        new_img=PNMImage(self.frame_size, self.frame_size*self.num_frames, 4)
        new_img.gaussianFilterFrom(1.0, column)
        return new_img

    def fit_column_to_frames(self, column):
        frame_size=column.getReadXSize()
        num_frames=column.getReadYSize()/column.getReadXSize()
        new_img=PNMImage(frame_size, frame_size*self.num_frames, 4)

        old_frames=[]
        for i in range(num_frames):
            frame=PNMImage(frame_size, frame_size, 4)
            frame.copySubImage(column, 0, 0, 0, i*frame_size, frame_size,frame_size)
            old_frames.append(frame)
        ratio=float(num_frames)/float(self.num_frames)
        for i in range(self.num_frames):
            index=int(i*ratio)
            blend=(i*ratio)-int(i*ratio)
            index2=index+1
            if index2>=num_frames:
                index2=num_frames-1
            sub_frame1=PNMImage(frame_size, frame_size, 4)
            sub_frame1.copyFrom(old_frames[index])
            sub_frame2=PNMImage(frame_size, frame_size, 4)
            sub_frame2.copyFrom(old_frames[index2])
            final_frame=sub_frame1*(1.0-blend)+sub_frame2*blend
            new_img.copySubImage(final_frame, 0,frame_size*i, 0,0)
        return new_img

    def frame_to_column(self, frame):
        new_img=PNMImage(self.frame_size, self.frame_size*self.num_frames, 4)
        for i in range(self.num_frames):
            new_img.copySubImage(frame, 0, i*self.frame_size, 0, 0)
        return new_img


    def load_files_into_image(self, path):
        files_to_load=[]
        #the path may have multiple filenames
        #the filenames can be separated by ',' or ', ' or ' , or ';' or '; ' or ' ; '
        new_path=[x.strip() for x in path.replace(';',',').split(',')]
        #the filenames can also use wildcard so we glob'em
        for name in new_path:
            files_to_load+=self.sort_nicely(glob.glob(name))
        #load all the files into PNMImage
        #print files_to_load
        img=[]
        img_size=set()
        for name in files_to_load:
            image=PNMImage()
            image.read(name)
            img.append(image)
            img_size.add((image.getReadXSize(), image.getReadYSize()))
        #if it's just one image, we're done
        if len(img)==1:
            return img[0]
        #if all the images are the same size, we just glue'em
        all_equal=True
        for size in img_size:
            if size[0] != size[1]:
                all_equal=False

        if len(img_size)==1 and all_equal:
            size=list(img_size)[0][0]
            final_img=PNMImage(size, size*len(img), 4)
            for i, image in enumerate(img):
                final_img.copySubImage(image, 0, size*i, 0,0)
            return final_img
        #if all the images are square, but of different sizes
        #we resize them and glue them into one
        if len(img_size)>1 and all_equal:
            final_img=PNMImage(self.frame_size, self.frame_size*len(img), 4)
            for i, image in enumerate(img):
                resized=self.resize_frame(image)
                final_img.copySubImage(resized, 0,self.frame_size*i, 0,0)
            return final_img
        #images are of different size and not square... I have no idea here
        raise RuntimeError("Can't load or combine image(s): "+str(path))

    def add(self, path):
        if path in self.known_columns:
            return self.known_columns[path]
        self.known_columns[path]=len(self.known_columns)
        #image=PNMImage()
        #image.read(path)
        image=self.load_files_into_image(path)
        x=image.getReadXSize()
        y=image.getReadYSize()

        if x==y:#just one frame
            if x == self.frame_size:
                self.add_column(self.frame_to_column(image))
            else:
                self.add_column(self.frame_to_column(self.resize_frame(image)))
        elif x == self.frame_size and y == self.num_frames*self.frame_size: #good column
            self.add_column(image)
        elif y == self.num_frames*x: # good number of frames, bad size
            self.add_column(self.resize_column(image))
        elif x == self.frame_size and y != self.num_frames*self.frame_size: #good size, bad numer of frames
            self.add_column(self.fit_column_to_frames(image))
        else: #bad size, bad numer of frames
            self.add_column(self.resize_column(self.fit_column_to_frames(image)))
        return len(self.known_columns)

    def to_texture(self):
        tex=Texture()
        if self.image is not None:
            tex.load(self.image)
        return tex

    def write(self, name):
        self.image.write(name)
