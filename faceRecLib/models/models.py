import tensorflow as tf
from tensorflow.keras import layers,Model
from faceRecLib import config
from faceRecLib.utils import *

def get_MobileNetV2(weights="imagenet"):
  return tf.keras.applications.MobileNetV2(input_shape=(config.image_size,config.image_size,3),include_top=False,weights=weights)
def get_MobileNet(weights="imagenet"):
  return tf.keras.applications.MobileNet(input_shape=(config.image_size,config.image_size,3),include_top=False,weights=weights)


def get_base_model(model_type:str="mobilenet")->tf.keras.Model:
    model=None
    model_type=model_type.lower()
    if model_type=="mobilenet":
        model=get_MobileNet()
    elif model_type=="mobilenetv2":
        model=get_MobileNetV2()
    elif model_type=="resnet50":
        model=tf.keras.applications.ResNet50(input_shape=(config.image_size,config.image_size,3),include_top=False,weights="imagenet")

    return model


def get_feature_extractor_model(emb_size=128,model_type="mobilenet",frozen=False,d=0):
    
    config.emb_size=emb_size
    config.model_type=model_type

    x_input=layers.Input(shape=(config.image_size,config.image_size,3),name="input_layer")
    x=layers.Lambda(preprocess_img,name="preprocessing_layer")(x_input)

    base_model=get_base_model(model_type)
    
    if frozen:  base_model.trainable=False

    x=base_model(x)

    x=layers.BatchNormalization()(x)
    if d > 0 and d < 1:
        x=layers.Dropout(d)(x)
    x=layers.Flatten()(x)



    x = layers.Dense(emb_size,use_bias=False, kernel_initializer="glorot_normal",name="pre_embedding")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("linear", dtype="float32", name="feature_vector")(x)


    return Model(inputs=x_input,outputs=x,name="Feature_extractor_model")


def add_softmax(model):
  if model.layers[-1].name=="softmax_layer": return model
  print("addin softmax layer")
  x=layers.Dense(config.num_classes,activation="softmax",name="softmax_layer", use_bias=False)(model.get_layer("feature_vector").output)
  return Model(model.input,x,name="softmax_model")
