import PIL
from PIL import ImageOps
import xml.etree.ElementTree as ET
import shutil
import os
import numpy as np
from glob import glob
import tensorflow as tf
from tensorflow.keras import backend as K
import cv2
import matplotlib.pyplot as plt
import importlib



from app.face_recognition import config
from app.face_recognition.aligner import  aligner



class face_recognition:
  def __init__(self,model_path,thres=None,min_aligner_confidence=None):
    config_file_path='.'.join(model_path.split("/"))+".config"
    # print(config_file_path)
    self.model_config= importlib.import_module(config_file_path)
    # print(self.model_config)
    self.thres=thres if thres is not None else self.model_config.thres
    self.aligner=aligner(min_aligner_confidence)  if min_aligner_confidence is not None else aligner(config.min_aligner_confidence)
    self.feature_extractor=tf.keras.models.load_model(model_path+"/model.h5",compile=False)
    
    

  def euclidean_distance(self,vectors):
    squared_sum=np.sum(np.square(vectors[0]-vectors[1]),axis=-1,keepdims=True)
    return np.sqrt(np.maximum(squared_sum,1e-7))



  def calculate_distance(self,crop_img,db_faces_features,mode='avg'):
    """
    mode= 'avg' or 'best'
    """
    if mode not in ['avg','best']:  raise ValueError(f"Unknown mode:{mode} \nMode should be one of these:{['avg','best']}")
    crop_img_features=self.feature_extractor.predict(crop_img[None,:,:,:],verbose=0)
    all_distances=[] # distance of this particular crop with all faces in database
    for face_idx in range(len(self.faces)):
      if mode=='avg':
        db_face_features=db_faces_features[face_idx].mean(axis=0,keepdims=True) # avg method
        new_crop_img_features=crop_img_features.copy()
      else:
        db_face_features=db_faces_features[face_idx] # best method
        new_crop_img_features=np.tile(crop_img_features,[db_face_features.shape[0],1])
      try:
        assert(db_face_features.shape==new_crop_img_features.shape)
      except:
        raise AssertionError(f"db_face_features shape{db_face_features.shape} does not match crop_img_features shape{new_crop_img_features.shape}")
      
      distance=np.min(self.euclidean_distance([db_face_features,new_crop_img_features]),axis=0)[0]
      
      if distance<=self.thres:
        all_distances.append(distance) # obj distance wrt to all faces in database
      else:
        all_distances.append(self.model_config.large_distance) # not the person garruntied
    return all_distances



  def repeat_allowed_face_recognition(self,distance_dict):
    faceidx_to_obj_dict=dict()
    for obj in distance_dict.keys():
      distances=np.array(distance_dict[obj])
      min_distance,min_distance_idx = distances.min(),distances.argmin()
      if min_distance<=self.thres:
        obj.find('name').text = self.faces[min_distance_idx]
        distance_tag=ET.Element("distance")
        distance_tag.text="{:.2f}".format(min_distance)
        obj.append(distance_tag)
    return faceidx_to_obj_dict


  def assign_face_label(self,obj):
      
      # find min and argmin
      min_distance,min_distance_idx = self.distance_dict[obj].min(),self.distance_dict[obj].argmin()
      # base condition
      if min_distance>=self.thres:
        # print("end");
        return;
      if min_distance_idx not in self.faceidx_to_obj_dict:
        self.faceidx_to_obj_dict[min_distance_idx]=(obj,min_distance)  # stores obj and distance
      else:

        if(min_distance>self.faceidx_to_obj_dict[min_distance_idx][1]):
          self.distance_dict[obj][min_distance_idx]=self.model_config.large_distance
          self.assign_face_label(obj)
        else:
          temp_obj,temp_min_distance=self.faceidx_to_obj_dict[min_distance_idx]
          self.faceidx_to_obj_dict[min_distance_idx]=(obj,min_distance)  # stores obj and distance
          self.distance_dict[temp_obj][min_distance_idx]=self.model_config.large_distance
          self.assign_face_label(temp_obj)


  def no_repeat_allowed_face_recognition(self,distance_dict):
    
    self.faceidx_to_obj_dict=dict()
    for obj in distance_dict.keys():
      self.assign_face_label(obj)
      
    for idx,(obj,distance) in self.faceidx_to_obj_dict.items():
      obj.find('name').text = self.faces[idx]
      distance_tag=ET.Element("distance")
      distance_tag.text="{:.2f}".format(distance)
      obj.append(distance_tag)
      # print(obj.find("distance").text)
    
    return self.faceidx_to_obj_dict
    

  def forward_pass(self,img,tree,mode="repeat"):
      '''mode : "repeat" or "no-repeat" '''
      root=tree.getroot()
      self.distance_dict=dict()
      
      size=root.find('size')
      w,h=int(size.find("width").text),int(size.find("height").text)
      
      for i,obj in enumerate(root.findall("object")):
        bndbox=obj.find("bndbox")
        
        xmin,ymin , xmax,ymax=int(bndbox.find('xmin').text),int(bndbox.find('ymin').text),int(bndbox.find('xmax').text),int(bndbox.find('ymax').text)

        crop_img=img[ymin:ymax,xmin:xmax]
        crop_img=cv2.resize(crop_img,[self.model_config.input_size,self.model_config.input_size])
        crop_img=self.aligner.align_image(crop_img)
        
        
        if crop_img is not None:
          self.distance_dict[obj]=np.array(self.calculate_distance(crop_img,self.db_faces_features,mode=self.distance_mode))

      # print(distance_dict)

      if mode=="repeat":
        faceidx_to_obj_dict=self.repeat_allowed_face_recognition(self.distance_dict)
      elif mode=="no-repeat":
        faceidx_to_obj_dict=self.no_repeat_allowed_face_recognition(self.distance_dict)
      return tree
      
  def predict(self,img,tree):
    if (not hasattr(self,"distance_mode")) or (not hasattr(self,"recognition_mode")): raise ValueError(f"Call set_face_db_and_mode method first!")
    tree=self.forward_pass(img,tree,mode=self.recognition_mode)
    return tree

  def set_face_db_and_mode(self,faces,db_faces_features,distance_mode="avg",recognition_mode="repeat"):

    if distance_mode not in ['avg','best']:  raise ValueError(f"Unknown mode:{distance_mode} \nMode should be one of these:{['avg','best']}")
    if recognition_mode not in ['repeat','no-repeat']:  raise ValueError(f"Unknown mode:{recognition_mode} \nMode should be one of these:{['repeat','no-repeat']}")
    self.distance_mode=distance_mode
    self.recognition_mode=recognition_mode

    self.faces=faces
    self.db_faces_features=db_faces_features

# print(face_features)
# for xml_file in ["/content/images - Copy/IMG20221124131734.xml"]:

if __name__=="__main__":
  
  from helper import *

  img_dir=config.img_dir
  save_dir=config.save_dir

  

  _,faces,_=next(os.walk(config.db_dir))
  db_faces_features=[np.loadtxt(f"{config.db_dir}/{face_dir}/features.npy",ndmin=2) for face_dir in faces]

  for i in range(len(faces)):
    print(faces[i],":",db_faces_features[i].shape)


  if os.path.exists(save_dir):shutil.rmtree(save_dir)
  os.mkdir(save_dir)


  fr=face_recognition("face_recognition/Models/v1")
  # fr=face_recognition(thres=0.3)
  # fr.set_face_db_and_mode(faces,db_faces_features,distance_mode="best",recognition_mode="repeat")
  fr.set_face_db_and_mode(faces,db_faces_features,distance_mode="best",recognition_mode="no-repeat")

  for xml_file in glob(f"{img_dir}/*.xml"):
    tree=ET.parse(xml_file)
    root=tree.getroot()
    img_name=img_dir+'/'+root.find("filename").text
    img=PIL.Image.open(img_name).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img=np.array(img)
    
    tree=fr.predict(img,tree)

    img=show_pred_image(tree,img)
    # plot examples
    # plt.figure(figsize=(10,10))
    # plt.axis("off")
    # plt.title("Labeled images")
    # plt.imshow(img)
    # plt.show()
    print(xml_to_objs_found(tree))

    cv2.imwrite(save_dir+"/"+root.find("filename").text,cv2.cvtColor(img,cv2.COLOR_RGB2BGR))

