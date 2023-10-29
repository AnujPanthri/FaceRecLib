import yolov2keras as yod
from faceRecLib.inference import Aligner
import os
import shutil
from glob import glob
import cv2
import numpy as np



images_dir="images/"
crops_dir="crops/"
aligner_obj=Aligner()

img_paths=glob(images_dir+"*")
print(img_paths)
if os.path.exists(crops_dir):
    shutil.rmtree(crops_dir)
os.makedirs(crops_dir)

model_path="face_detection_models/v3/"
object_detector = yod.load_model_from_weights(model_path)
# object_detector.set_config(p_thres=0.5,nms_thres=0.3,image_size=[1024,2080])
object_detector.set_config(p_thres=0.5,nms_thres=0.3,image_size=[608,1024])


for img_idx,img_path in enumerate(img_paths):
    img=cv2.imread(img_path)[:,:,::-1]
    img_h,img_w,_=img.shape
    detections = object_detector.predict(img)
    for crop_idx,detection in enumerate(detections):
    # [p,class_name,xmin,ymin,w,h]

        _,_,xmin,ymin,w,h=detection
        xmin , w = int(xmin*img_w) , int(w*img_w) 
        ymin , h = int(ymin*img_h) , int(h*img_h) 
        xmax , ymax = xmin+w , ymin+h
        crop=img[ymin:ymax,xmin:xmax]

        # align if you want

        # save crops
        cv2.imwrite(crops_dir+f"{img_idx}_{crop_idx}.jpg",crop[:,:,::-1])
