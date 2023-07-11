import tensorflow as tf
import numpy as np
import cv2

def euclidean_distance(vectors):
    squared_sum=np.sum(np.square(vectors[0]-vectors[1]),axis=-1,keepdims=True)
    return np.sqrt(np.maximum(squared_sum,1e-7))

def new_distance(vectors):
    return (vectors[0]*vectors[1]).sum(-1)

path="face_recognition/Models/mobilenet_basic_lfw/mobilenet_basic_lfw_model.h5"
# path="face_recognition/Models/keras_mobilenet_emore_adamw/keras_mobilenet_emore_adamw.h5"

model=tf.keras.models.load_model(path,compile=False)

x_input=tf.keras.layers.Input(shape=(112,112,3))
x_preprocess=tf.keras.layers.Lambda(lambda x:(x - 127.5) * 0.0078125)(x_input)
x=model(x_preprocess,training=False)
x=tf.keras.layers.Lambda(lambda x:tf.math.l2_normalize(x, axis=-1))(x)
model2=tf.keras.Model(x_input,x)
# model2.summary()
# model.save(path.rsplit("/",1)[0]+"/model.h5")
# print("model save to :\t",path.rsplit("/",1)[0]+"/model.h5")



img1=cv2.resize(cv2.imread("C:/Users/Home/Desktop/college stuff/vasu_dataset/all/priyanshi/7.jpg")[:,:,::-1],[112,112])[None]
img2=cv2.resize(cv2.imread("C:/Users/Home/Desktop/college stuff/vasu_dataset/all/shivansh/12.jpg")[:,:,::-1],[112,112])[None]
v1=(model.predict(img1,verbose=0))
v2=(model.predict(img2,verbose=0))


print("euclidean_distance:",euclidean_distance([v1,v2]))
print("new_distance:",new_distance([v1,v2]))
if(new_distance([v1,v2])[0]>0.2830035090446472):
    print("matching")
else:
    print("not matching")