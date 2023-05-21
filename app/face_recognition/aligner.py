import cv2
import itertools
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
import PIL
import os
import shutil



class aligner:
    def __init__(self,min_aligner_confidence):        
        mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh_images = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                                min_detection_confidence=min_aligner_confidence)

        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        LEFT_EYE_INDEXES = list(set(itertools.chain(*mp_face_mesh.FACEMESH_LEFT_EYE)))
        RIGHT_EYE_INDEXES = list(set(itertools.chain(*mp_face_mesh.FACEMESH_RIGHT_EYE)))
        
        self.LEFT_EYE_INDEX=LEFT_EYE_INDEXES[7]  # eye point index
        self.RIGHT_EYE_INDEX=RIGHT_EYE_INDEXES[4]  # eye point index

    def align_image(self,img):
        
        # start work
        face_mesh_results = self.face_mesh_images.process(img)
        if face_mesh_results.multi_face_landmarks!=None:
            face_landmarks=face_mesh_results.multi_face_landmarks[0]

            h,w,_=img.shape

            points=[]

            
            x_coord=int(np.clip(face_landmarks.landmark[self.LEFT_EYE_INDEX].x*w,0,w))
            y_coord=int(np.clip(face_landmarks.landmark[self.LEFT_EYE_INDEX].y*h,0,h))
            points.append((x_coord,y_coord))

            
            x_coord=int(np.clip(face_landmarks.landmark[self.RIGHT_EYE_INDEX].x*w,0,w))
            y_coord=int(np.clip(face_landmarks.landmark[self.RIGHT_EYE_INDEX].y*h,0,h))
            points.append((x_coord,y_coord))

            p0=np.array(points[0],dtype='float64')
            p1=np.array(points[1],dtype='float64')


            h=abs(p0[1]-p1[1])
            w=abs(p0[0]-p1[0])

            theta=np.arctan(h/w)

            angle=(theta * 180) / np.pi

            def get_direction(p0,p1):
                if p0[0]<p1[0]:
                    if p0[1]<p1[1]:
                        direction=1
                    else:
                        direction=-1
                else:
                    if p1[1]<p0[1]:
                        direction=1
                    else:
                        direction=-1
                return direction

            direction=get_direction(p0,p1)
            angle=direction*angle
            # print("rotated anticlockwise by :",angle,"angle")
            new_img = PIL.Image.fromarray(img)
            new_img = new_img.rotate(angle)
            
            return np.array(new_img)
        else:
            return None