import yolov2keras as yod 
import faceRecLib as frl
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
import numpy as np
from glob import glob



# fr_model_path="output/v1/"
fr_model_path="output/mobilenet/"
face_recognizer=frl.load_model(fr_model_path)
# face_recognizer=frl.load_model_from_weights(fr_model_path)

face_recognizer.set_config(thres=0.4,min_aligner_confidence=0.6)

database_dir="reference_database/"
faces=os.listdir(database_dir)
db_faces_features=[]
for face in faces:
    db_face_paths=glob(database_dir+face+"/"+"*.jpg")
    crops=[]
    for face_path in db_face_paths:
        crop=cv2.imread(face_path)[:,:,::-1]
        crop=cv2.resize(crop,[frl.config.image_size,frl.config.image_size])
        crops.append(crop)
    db_faces_features.append(face_recognizer.get_features(crops))
    print(face,":",db_faces_features[-1].shape)

face_recognizer.set_face_db_and_mode(faces,db_faces_features,recognition_mode="repeat")





model_path="face_detection_models/v3/"

object_detector = yod.load_model_from_weights(model_path)
# object_detector.set_config(p_thres=0.5,nms_thres=0.3,image_size=[1024,2080])
object_detector.set_config(p_thres=0.5,nms_thres=0.3,image_size=[416,608])
# img="C:/Users/panth/OneDrive/Pictures/Camera Roll/WIN_20230815_13_49_11_Pro.jpg"
img="C:/Users/panth/OneDrive/Pictures/Camera Roll/WIN_20231029_12_03_26_Pro.jpg"
# img="D:/New folder/Face_Recognition/roboflow.voc/train/24_jpg.rf.75e6506ea525cec685510dae47417bd7.jpg"
img=cv2.imread(img)[:,:,::-1]
img_h,img_w,_=img.shape
detections = object_detector.predict(img)
# print(detections)

# crops = yod.inference.helper.get_crops(img,detections,aligner=frl.inference.Aligner(),resize=(frl.config.image_size,frl.config.image_size))
crops = yod.inference.helper.get_crops(img,detections)

print(len(crops),"faces detected.")
# plt.imshow(crops[0])
# plt.show()

recognitions=face_recognizer.predict(crops)
print(recognitions)

for idx in range(len(detections)):

    # detection [p,class_name,xmin,ymin,w,h]
    # recognition [similarity,db_name] or None

    if(recognitions[idx]!=None):
        detections[idx][1] = recognitions[idx][1]


frl.inference.helper.show_objects(img,detections)
# plt.show()

# pred_img=frl.inference.helper.pred_image(img,detections,thickness=10,font_scale=4)
# plt.imshow(pred_img)
# plt.show()