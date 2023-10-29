import tensorflow as tf
from glob import glob
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import random
from faceRecLib import config

image_types = ["jpg", "png", "jpeg", "ppm", "webp"]


def get_dataset(data_dir, bs=16):

    ds = _dataset_from_folder(data_dir)
    # self.ds=self.load_tfrecord_dataset(data)

    ds = ds.batch(bs, drop_remainder=True)
    return ds


def _allowed_extension(path):
    for image_type in image_types:
        if path.endswith(image_type):
            return True
    return False

def _load_image_from_path(path):
    img = tf.io.read_file(path)
    img = tf.image.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, [config.image_size, config.image_size])
    return img


def _dataset_from_folder(folder):
    img_paths = [
        curr_folder + "/" + filename
        for curr_folder, sub_folders, filenames in os.walk(folder)
        for filename in filenames
        if len(filenames) > 0
    ]
    img_paths = list(filter(_allowed_extension, img_paths))
    labels = list(map(lambda x: x.rsplit("/", 2)[-2], img_paths))
    # print(labels)
    config.label_to_idx = {label: i for i, label in enumerate(set(labels))}
    config.idx_to_label = {idx: label for label, idx in config.label_to_idx.items()}

    labels = list(map(lambda x: config.label_to_idx[x], labels))

    config.classnames=list(config.label_to_idx.keys())
    config.num_classes = len(config.classnames)

    dataset = tf.data.Dataset.from_tensor_slices((img_paths, labels))
    dataset = dataset.shuffle(len(labels))

    dataset = dataset.map(
        lambda img, label: (
            _load_image_from_path(img),
            tf.one_hot(label, config.num_classes),
        ),
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    return dataset
