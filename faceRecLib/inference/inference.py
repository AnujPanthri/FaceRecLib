from .aligner import Aligner

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
from sklearn.preprocessing import normalize


from faceRecLib import config


class Recognizer:
    def __init__(self, model, min_aligner_confidence=0.6):
        self.model = (
            tf.keras.models.load_model(model, compile=False)
            if isinstance(model, str)
            else model
        )
        self.aligner = Aligner(min_aligner_confidence)
        self.low_similarity = -5

    def set_config(self, thres=0.4, min_aligner_confidence=0.6):
        self.thres = thres
        self.aligner.min_detection_confidence = min_aligner_confidence

    def similarity_func(self, vectors):
        """this similarity metric is -1 to 1
        and it gives values close to 1 when matching
        and values close to -1 when not matching
        """
        return (vectors[0] * vectors[1]).sum(-1)

    def get_features(self,crops):
    
        crops_features=self.model.predict(np.array(crops),batch_size=32,verbose=0)
        return normalize(crops_features)
    
    def set_face_db_and_mode(
        self, faces, db_faces_features, recognition_mode="repeat"
    ):
       
        if recognition_mode not in ["repeat", "no-repeat"]:
            raise ValueError(
                f"Unknown mode:{recognition_mode} \nMode should be one of these:{['repeat','no-repeat']}"
            )
    
        self.recognition_mode = recognition_mode

        self.faces = faces
        self.db_faces_features = db_faces_features

    def calculate_similarities(
        self,
        crop_img,
        db_faces_features,
    ):
        
        crop_img_features = self.get_features(crop_img[None])

        # similarities of this particular crop with all faces in database
        all_similarities = dict()
        for db_face_idx in range(len(self.faces)):
            db_face_features = db_faces_features[db_face_idx]  # best method
            new_crop_img_features = np.tile(
                crop_img_features, [db_face_features.shape[0], 1]
            )
            try:
                assert db_face_features.shape == new_crop_img_features.shape
            except:
                raise AssertionError(
                    f"db_face_features shape{db_face_features.shape} does not match crop_img_features shape{new_crop_img_features.shape}"
                )

            similarity = np.max(
                self.similarity_func([db_face_features, new_crop_img_features]), axis=0
            )

            if similarity > self.thres:
                all_similarities[db_face_idx]=similarity
                

        return all_similarities

    def repeat_allowed_face_recognition(self, all_similarities: list):
        """
        all_similarities: [ {db_face_idx:similarity,...},... ]
        list of len of crop_imgs

        repeating db_face to multiple crops is allowed

        returns recognitions : [[similarity,face_name],None,None,...]
        None means no db_face assigned to that crop
        """
        recognitions = [None] * len(all_similarities)

        for idx in range(len(all_similarities)):
            similarities_dict = all_similarities[idx]
            if len(similarities_dict)==0: continue
            max_similarity_idx , max_similarity = max(similarities_dict.items(), key=lambda x: x[1])
            
            if max_similarity >= self.thres:
                recognitions[idx] = [max_similarity, self.faces[max_similarity_idx]]

        return recognitions

    def no_repeat_allowed_face_recognition(self, all_similarities: list):
        """
        all_similarities: [ {db_face_idx:similarity,...},... ]
        list of len of crop_imgs

        doesn't allows repeating db_face

        returns recognitions : [[similarity,face_name],None,None,...]
        None means no db_face assigned to that crop
        """

        recognitions = [None] * len(all_similarities)

        def assign_face_label(face_idx):
            
            if(len(all_similarities[face_idx])==0):  return

            max_similarity_idx,max_similarity = max(all_similarities[face_idx], key=lambda x: x[1])
            
            # base condition
            if max_similarity < self.thres:
                # print("end");
                return
            
            elif max_similarity_idx not in dbfaceidx_to_faceidx_dict:
                # if crop is unassigned assign to this db_face
                dbfaceidx_to_faceidx_dict[max_similarity_idx] = (
                    max_similarity,
                    face_idx,
                )  
            else:
                if max_similarity < dbfaceidx_to_faceidx_dict[max_similarity_idx][0]:
                    # current is less matching
                    all_similarities[face_idx][max_similarity_idx] = self.low_similarity
                    assign_face_label(face_idx)
                else:
                    # current is more matching
                    old_max_similarity,old_faceidx = dbfaceidx_to_faceidx_dict[max_similarity_idx]
                    # stores obj and distance
                    dbfaceidx_to_faceidx_dict[max_similarity_idx] = (max_similarity,face_idx)  
                    all_similarities[old_faceidx][
                        max_similarity_idx
                    ] = self.low_similarity
                    assign_face_label(face_idx)

        dbfaceidx_to_faceidx_dict = dict()
        for face_idx in range(len(all_similarities)):
            assign_face_label(face_idx)

        for db_face_idx, (similarity,face_idx) in dbfaceidx_to_faceidx_dict.items():
            recognitions[face_idx] = [similarity, self.faces[db_face_idx]]

        return recognitions

    def forward_pass(self, crops):
        all_similarities=[]
        for i, crop in enumerate(crops):
           
            crop_img = cv2.resize(
                crop, [config.image_size, config.image_size]
            )
            crop_img = self.aligner.align((crop_img,))[0]

            if crop_img is not None:
                all_similarities.append(
                    self.calculate_similarities(
                        crop_img, self.db_faces_features
                    )
                )
            else:
                all_similarities.append(dict())

        # print(all_similarities)

        if self.recognition_mode == "repeat":
            recognitions = self.repeat_allowed_face_recognition(
                all_similarities
            )
        elif self.recognition_mode == "no-repeat":
            recognitions = self.no_repeat_allowed_face_recognition(
                all_similarities
            )
        return recognitions

    def predict(self, crops:list):
        if (
            not hasattr(self, "recognition_mode")
        ):
            raise ValueError(f"Call set_face_db_and_mode method first!")
        
        recognitions = self.forward_pass(crops)
        return recognitions
