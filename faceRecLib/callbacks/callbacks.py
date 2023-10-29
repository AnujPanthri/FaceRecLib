import numpy as np
from sklearn.preprocessing import normalize
import tensorflow as tf
from tensorflow.keras import Model


class validate_model:
  def __init__(self,bins_list,bs=128):
    self.bins_list=bins_list
    self.ds_list=[]
    self.issame_list=[]

    _imread = lambda xx: tf.cast(tf.image.decode_image(xx, channels=3), "float32")

    for bin_file in self.bins_list:
      bin,issamelist=np.load(bin_file,allow_pickle=True,encoding="bytes")
      print(len(bin),len(issamelist))
      dataset=tf.data.Dataset.from_tensor_slices(bin)
      dataset=dataset.map(_imread).batch(bs)
      self.ds_list.append(dataset)
      self.issame_list.append(np.array(issamelist,dtype='bool'))

  def get_embeddings(self,model,ds):
    return model.predict(ds);


  def __call__(self,model):
    all_acc=[]
    for i,ds in enumerate(self.ds_list):
      test_issame=self.issame_list[i]
      bin_file_name=self.bins_list[i]
      embs=self.get_embeddings(model,ds)
      embs=normalize(embs)

      embs_a = embs[::2]
      embs_b = embs[1::2]
      dists = (embs_a * embs_b).sum(1)

      tt = np.sort(dists[test_issame[: dists.shape[0]]])
      ff = np.sort(dists[np.logical_not(test_issame[: dists.shape[0]])])

      t_steps = int(0.1 * ff.shape[0])
      acc_count = np.array([(tt > vv).sum() + (ff <= vv).sum() for vv in ff[-t_steps:]])
      acc_max_indx = np.argmax(acc_count)
      acc_max = acc_count[acc_max_indx] / dists.shape[0]
      acc_thresh = ff[acc_max_indx - t_steps]
      print("{}: Acc: {:.5f} at threshold: {:.6f}".format(bin_file_name,acc_max,acc_thresh))
      all_acc.append(acc_max)

    return all_acc




class ValidateCallback(tf.keras.callbacks.Callback):
    def __init__(self,validator):
      self.validator=validator
      self.best_acc=0.0
      self.best_model_path="best_acc_model.h5"


    def on_epoch_end(self, epoch, logs=None):
        # keys = list(logs.keys())
        # print("End epoch {} of training; got log keys: {}".format(epoch, keys))
          basic_model=Model(self.model.input,self.model.get_layer("feature_vector").output)
          acc_list=self.validator(basic_model)

          curr_acc=acc_list[0]
          tf.print("\ncurr acc:",curr_acc)
          if curr_acc>self.best_acc:
            self.best_acc=curr_acc
            tf.print(f"Saving Model {self.best_model_path}")
            basic_model.save(self.best_model_path, overwrite=True)
