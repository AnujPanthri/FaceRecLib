from typing import Optional

import PIL
import xml.etree.ElementTree as ET
import shutil
import os
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
import importlib
import recogniser

from PIL import ImageOps
from glob import glob
from recogniser import config
from tensorflow.keras import backend as K


class Recogniser:
  _distance_modes = (
    'avg',
    'best',
  )
  _recognition_modes = (
    'repeat',
    'no-repeat',
  )

  @staticmethod
  def _validate_distance_and_recognition_mode(
    distance_mode: str,
    recognition_mode: str,
  ) -> bool:
    if not distance_mode in Recogniser._distance_modes:
      raise ValueError(f'"distance_mode" not in {Recogniser._distance_modes}')
    if not recognition_mode in Recogniser._recognition_modes:
      raise ValueError(
        f'"recognition_mode" not in {Recogniser._recognition_modes}'
      )

  def __init__(
    self,
    /,
    *,
    model: tf.keras.Model,
    model_configs: dict,
    threshold: Optional[float] = None,
    min_aligner_confidence: Optional[float] = recogniser.MIN_ALIGNER_CONFIDENCE,
    distance_mode: Optional[str] = 'avg',
    recognition_mode: Optional[str] = 'repeat',
  ):
    self.model_configs = model_configs

    if threshold:
      self.threshold = threshold
    else:
      if 'threshold' in self.model_configs:
        self.threshold = self.model_configs.threshold
      else:
        raise AttributeError(
          f'{self.model_configs.__class__.__name__} does not define "threshold"'
        )

    self.aligner = recogniser.Aligner(
      min_detection_confidence=min_aligner_confidence
    )
    self.feature_extractor = model

    self._validate_distance_and_recognition_mode(
      distance_mode, recognition_mode
    )
    self.distance_mode = distance_mode
    self.recognition_mode = recognition_mode

  def forward(
    self, img: np.ndarray, tree: ET, mode: Optional[str] = 'repeat'
  ) -> ET:
    root = tree.getroot()
    self.distance = {}

    size = root.find('size')
    w, h = int(size.find('width').text), int(size.find('height').text)

    for o in root.findall('object'):
      bndbox = o.find('bndbox')

      xmin = float(o.find('bndbox').find('xmin').text)
      xmax = float(o.find('bndbox').find('xmax').text)
      ymin = float(o.find('bndbox').find('ymin').text)
      ymax = float(o.find('bndbox').find('ymax').text)

      crop = img[ymin:ymax, xmin:xmax]
      crop = cv2.resize(crop, [self.model_configs.input_size] * 2)
      crop = self.aligner.align((crop, ))

      if crop:
        self.distance[o] = np.array(
          self.calculate_distance(
            crop, self.db_faces_features, mode=self.distance_mode
          )
        )

    if mode == 'repeat':
      face_idx_to_obj_dict = self.repeat_allowed_face_recognition(
        self.distance
      )
    else:
      face_idx_to_obj_dict = self.no_repeat_allowed_face_recognition(
        self.distance
      )
    return tree

  def predict(self, img: np.ndarray, tree: ET) -> ET:
    if not hasattr(self, 'distance_mode') or hasattr(self, 'recognition_mode'):
      raise AttributeError(
        (
          f'{self.__class__.__name__} does not define "distance_mode" and "recognition_mode".'
          ' Call set_face_db_and_mode() method first.'
        )
      )
    return self.forward(img, tree, mode=self.recognition_mode)

  # def euclidean_distance(self,vectors):
  #   squared_sum=np.sum(np.square(vectors[0]-vectors[1]),axis=-1,keepdims=True)
  #   return np.sqrt(np.maximum(squared_sum,1e-7))

  def new_distance(self, vectors):
    ''' this distance metric is -1 to 1 
        and it gives values close to 1 when matching 
        and values close to -1 when not matching
    '''
    return (vectors[0] * vectors[1]).sum(-1)

  def _calculate_distance(
    self, crop: np.ndarray, db_faces_features, mode: Optional[str] = 'avg'
  ):
    pass

  def calculate_distance(self, crop_img, db_faces_features, mode='avg'):
    """
    mode= 'avg' or 'best'
    """
    if mode not in ['avg', 'best']:
      raise ValueError(
        f"Unknown mode:{mode} \nMode should be one of these:{['avg','best']}"
      )
    crop_img_features = self.feature_extractor.predict(
      crop_img[None, :, :, :], verbose=0
    )
    all_distances = [
    ]  # distance of this particular crop with all faces in database
    for face_idx in range(len(self.faces)):
      if mode == 'avg':
        db_face_features = db_faces_features[face_idx].mean(
          axis=0, keepdims=True
        )  # avg method
        new_crop_img_features = crop_img_features.copy()
      else:
        db_face_features = db_faces_features[face_idx]  # best method
        new_crop_img_features = np.tile(
          crop_img_features, [db_face_features.shape[0], 1]
        )
      try:
        assert (db_face_features.shape == new_crop_img_features.shape)
      except:
        raise AssertionError(
          f"db_face_features shape{db_face_features.shape} does not match crop_img_features shape{new_crop_img_features.shape}"
        )

      distance = np.max(
        self.new_distance([db_face_features, new_crop_img_features]), axis=0
      )

      if distance > self.thres:
        all_distances.append(
          distance
        )  # obj distance wrt to all faces in database
      else:
        all_distances.append(
          self.model_config.large_distance
        )  # not the person guaranteed
    return all_distances

  def repeat_allowed_face_recognition(self, distance_dict):
    faceidx_to_obj_dict = dict()
    for obj in distance_dict.keys():
      distances = np.array(distance_dict[obj])
      min_distance, min_distance_idx = distances.max(), distances.argmax()
      if min_distance > self.thres:
        obj.find('name').text = self.faces[min_distance_idx]
        distance_tag = ET.Element("distance")
        distance_tag.text = "{:.2f}".format(min_distance)
        obj.append(distance_tag)
    return faceidx_to_obj_dict

  def no_repeat_allowed_face_recognition(self, distance_dict):
    def assign_face_label(obj):

      # find min and argmin
      min_distance, min_distance_idx = distance_dict[obj].max(
      ), distance_dict[obj].argmax()
      # base condition
      if min_distance < self.thres:
        # print("end");
        return
      elif min_distance_idx not in faceidx_to_obj_dict:
        faceidx_to_obj_dict[min_distance_idx] = (
          obj, min_distance
        )  # stores obj and distance
      else:

        if (
          min_distance < faceidx_to_obj_dict[min_distance_idx][1]
        ):  # current is less matching
          distance_dict[obj][min_distance_idx] = self.model_config.large_distance
          assign_face_label(obj)
        else:  # current is more matching
          temp_obj, temp_min_distance = faceidx_to_obj_dict[min_distance_idx]
          faceidx_to_obj_dict[min_distance_idx] = (
            obj, min_distance
          )  # stores obj and distance
          distance_dict[temp_obj][min_distance_idx
                                  ] = self.model_config.large_distance
          assign_face_label(temp_obj)

    faceidx_to_obj_dict = dict()
    for obj in distance_dict.keys():
      assign_face_label(obj)

    for idx, (obj, distance) in faceidx_to_obj_dict.items():
      obj.find('name').text = self.faces[idx]
      distance_tag = ET.Element("distance")
      distance_tag.text = "{:.2f}".format(distance)
      obj.append(distance_tag)
      # print(obj.find("distance").text)

    return faceidx_to_obj_dict

  def set_face_db_and_mode(
    self,
    faces,
    db_faces_features,
    distance_mode="avg",
    recognition_mode="repeat"
  ):

    if distance_mode not in ['avg', 'best']:
      raise ValueError(
        f"Unknown mode:{distance_mode} \nMode should be one of these:{['avg','best']}"
      )
    if recognition_mode not in ['repeat', 'no-repeat']:
      raise ValueError(
        f"Unknown mode:{recognition_mode} \nMode should be one of these:{['repeat','no-repeat']}"
      )
    self.distance_mode = distance_mode
    self.recognition_mode = recognition_mode

    self.faces = faces
    self.db_faces_features = db_faces_features


# print(face_features)
# for xml_file in ["/content/images - Copy/IMG20221124131734.xml"]:

if __name__ == "__main__":

  from helper import *

  img_dir = config.img_dir
  save_dir = config.save_dir

  _, faces, _ = next(os.walk(config.db_dir))
  db_faces_features = [
    np.loadtxt(f"{config.db_dir}/{face_dir}/features.npy", ndmin=2)
    for face_dir in faces
  ]

  for i in range(len(faces)):
    print(faces[i], ":", db_faces_features[i].shape)

  if os.path.exists(save_dir):
    shutil.rmtree(save_dir)
  os.mkdir(save_dir)

  fr = face_recognition("face_recognition/Models/v1")
  # fr=face_recognition(thres=0.3)
  # fr.set_face_db_and_mode(faces,db_faces_features,distance_mode="best",recognition_mode="repeat")
  fr.set_face_db_and_mode(
    faces,
    db_faces_features,
    distance_mode="best",
    recognition_mode="no-repeat"
  )

  for xml_file in glob(f"{img_dir}/*.xml"):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    img_name = img_dir + '/' + root.find("filename").text
    img = PIL.Image.open(img_name).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img = np.array(img)

    tree = fr.predict(img, tree)

    img = show_pred_image(tree, img)
    # plot examples
    # plt.figure(figsize=(10,10))
    # plt.axis("off")
    # plt.title("Labeled images")
    # plt.imshow(img)
    # plt.show()
    print(xml_to_objs_found(tree))

    cv2.imwrite(
      save_dir + "/" + root.find("filename").text,
      cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    )
