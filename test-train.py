import faceRecLib as frl
import tensorflow as tf


train_image_dir="roboflow.voc/train/"
train_annotation_dir="roboflow.voc/train/"

val_image_dir="roboflow.voc/valid/"
val_annotation_dir="roboflow.voc/valid/"

frl.set_config(image_size=112)
save_dir="save/"
# frl.datasets.preprocess.pascal_voc_to_folder(train_image_dir,train_annotation_dir,save_dir)
ds=frl.datasets.get_dataset(save_dir,bs=16)

# for data in ds.take(1):
#     print(data)

print(frl.config.classnames)

model=frl.models.get_feature_extractor_model(emb_size=128,model_type="mobilenet")
# model=frl.models.get_feature_extractor_model(emb_size=128,model_type="resnet50")
model=frl.models.add_softmax(model)
model.summary()

model.compile(optimizer=tf.keras.optimizers.SGD(learning_rate=0.1), loss="categorical_crossentropy",metrics=["acc"])

# validator=frl.callbacks.validate_model(["lfw.bin"],bs=256)


history=model.fit(ds,epochs=10,verbose=1,
                  callbacks=[
                      # tf.keras.callbacks.EarlyStopping(patience=2,verbose=1),
                    #   tf.keras.callbacks.ModelCheckpoint("best_model.h5",save_best_only=True,verbose=1),
                    #   frl.callbacks.ValidateCallback(validator)
                      ]
                  )

frl.save("output/v1/",model)