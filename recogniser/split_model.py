import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras import Model, layers

model = tf.keras.models.load_model("face_recognization_model.h5", compile=False)
# model.summary()

feature_extractor = Model(model.layers[0].input,
                          model.layers[2](model.layers[0].input),
                          name='feature_extractor')
feature_extractor.summary()
feature_extractor.save("feature_extractor.h5")
