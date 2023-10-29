from sklearn.preprocessing import normalize

def preprocess_img(img):
  return (img - 127.5) * 0.0078125
def unprocess_img(img):
  return (img / 0.0078125) + 127.5

