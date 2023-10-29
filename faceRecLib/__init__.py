from . import datasets
from . import config
from .utils import *
from . import models
from .callbacks import callbacks
from . import inference


import os
import json
import shutil
import numpy as np
import pickle
from tensorflow.keras import Model,layers
import tensorflow as tf

def set_config(image_size):
    
    config.image_size=image_size

def config_to_dict():

    config_dict=dict()
    config_dict["emb_size"]=config.emb_size
    config_dict["model_type"]=config.model_type
    config_dict["image_size"]=config.image_size
    return config_dict

def config_from_dict(config_dict):

    config.emb_size=config_dict["emb_size"]
    config.model_type=config_dict["model_type"]
    config.image_size=config_dict["image_size"]
   

def save(export_dir,model):

    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)
    
    with open(export_dir+"config.json","w") as f:
        json.dump(config_to_dict(),f)
    basic_model=Model(model.input,model.get_layer("feature_vector").output)
    basic_model.compile()
    basic_model.save(export_dir+"model.h5")
    return export_dir


def load_model(model_dir):
    with open(model_dir+"config.json",'rb') as f:
        config_from_dict(json.load(f))
   
    # check if it has preprocessing_layer
    model = tf.keras.models.load_model(model_dir+"model.h5", compile=False)

    if(model.layers[1].name!="preprocessing_layer"):
        print("\n\nNeed to add preprocessing_layer")
        x_input=layers.Input(shape=(config.image_size,config.image_size,3))
        x=layers.Lambda(utils.preprocess_img,name="preprocessing_layer")(x_input)
        model = Model(x_input,model(x))
        model.save(model_dir+"model.h5")
        print("\n\nsaved updated model at :",model_dir+"model.h5")

    face_recognizer = inference.Recognizer(model)
    return face_recognizer

def load_model_from_weights(model_dir):

    with open(model_dir+"config.json",'rb') as f:
        config_from_dict(json.load(f))
    
    model = models.get_feature_extractor_model(emb_size=config.emb_size,model_type=config.model_type)

    model.load_weights(model_dir+"model.h5")
    face_recognizer = inference.Recognizer(model)

    return face_recognizer