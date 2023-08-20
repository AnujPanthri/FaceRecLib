import tensorflow as tf
from face_recognition import config
import cv2
from glob import glob
import os
import numpy as np

feature_extractor = tf.keras.models.load_model(
    "face_recognition/feature_extractor.h5", compile=False)
# feature_extractor.summary()

extensions = ['.jpg', '.jpeg', '.png', '.svg', '.webp']

db_dir = config.db_dir
_, sub_folders, _ = next(os.walk(db_dir))
print(sub_folders)
for sub_folder in sub_folders:
  image_paths = []
  [
      image_paths.extend(glob(db_dir + "\\" + sub_folder + "\\*" + extension))
      for extension in extensions
  ]

  all_img_features = []
  for image_path in image_paths:
    print(image_path)
    img = cv2.resize(cv2.imread(image_path),
                     [config.input_size, config.input_size])
    all_img_features.append(
        feature_extractor.predict(img[None, :, :, ::-1], verbose=0)[0])

  np.savetxt(db_dir + "\\" + sub_folder + "\\features.npy", all_img_features)

# "aligned_all"
