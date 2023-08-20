import numpy as np
import tensorflow.keras.backend as K

cell_size = 32
class_names = ['face']
class_colors = {class_name: np.random.rand(3) for class_name in class_names}

class_to_idx = {class_name: i for i, class_name in enumerate(class_names)}
idx_to_class = {i: class_name for i, class_name in enumerate(class_names)}
