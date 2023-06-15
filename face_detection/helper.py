import cv2
import numpy as np
from face_detection.inference import square_pad


# square_maker=square_pad(color=(255,255,255))
square_maker=square_pad(color=(0,0,0))
def get_crops(img,objs_found,aligner=None,resize:tuple=None):
    img_h,img_w,_=img.shape
    all_crops=[]
    for obj_found in objs_found:
        xmin,ymin=obj_found['xywh'][0],obj_found['xywh'][1]
        xmax,ymax=xmin+obj_found['xywh'][2],ymin+obj_found['xywh'][3]
        # rescale them
        xmin,ymin=int(xmin*img_w),int(ymin*img_h)
        xmax,ymax=int(xmax*img_w),int(ymax*img_h)

        crop=img[ymin:ymax,xmin:xmax]
        if aligner is not None:
            crop=aligner.align_image(crop)
            if crop is None: continue
        if resize is not None:
            crop=square_maker(crop)
            crop=cv2.resize(crop,resize)
        all_crops.append(crop)
    
    return all_crops
