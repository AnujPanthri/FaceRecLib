import os
import tensorflow as tf
from tensorflow.keras import Model,layers
from face_detection.config import class_names

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# custom layer for reshaping last layer
class yolo_reshape(tf.keras.layers.Layer):

  def __init__(self,num_anchors,last_item, **kwargs):
    super(yolo_reshape, self).__init__(**kwargs)    
    self.last_item=last_item
    self.num_anchors=num_anchors

  def call(self,output_layer):
    shape = [tf.shape(output_layer)[k] for k in range(4)]
    return tf.reshape(output_layer,[shape[0],shape[1],shape[2],self.num_anchors,self.last_item])
  
  def compute_output_shape(self, input_shape):
    return (input_shape[0],input_shape[1],input_shape[2],num_anchors,self.last_item, self.num_anchors,self.last_item)

  
  def get_config(self):
    config = super(yolo_reshape, self).get_config()
    config.update(
        {
            "last_item": self.last_item,
            "num_anchors": self.num_anchors
        }
    )
    return config
    
  @classmethod
  def from_config(cls, config):
    return cls(**config)
  

def load_model(path):
    model=tf.keras.models.load_model(path,compile=False,custom_objects={"yolo_reshape":yolo_reshape})
    return model
