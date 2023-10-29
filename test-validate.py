import yolov2keras as yod 
import faceRecLib as frl
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np






# fr_model_path="output/v1/"
fr_model_path="output/mobilenet/"
# fr_model_path="output/mobile_pretrained/"

face_recognizer=frl.load_model(fr_model_path)
# face_recognizer=frl.load_model_from_weights(fr_model_path)

face_recognizer.set_config(thres=0.7,min_aligner_confidence=0.6)

face_recognizer.model.summary()
validator = frl.callbacks.validate_model(["lfw.bin"],bs=256)
validator(face_recognizer.model)
