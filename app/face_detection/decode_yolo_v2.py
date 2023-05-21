import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import copy
import tensorflow.keras.backend as K
import cv2
from app.face_detection.config import cell_size,idx_to_class,class_to_idx,class_colors



def get_objects(y_pred,p=0.5,decode_preds=True,idx=None):
  global tf_anchors
  output_size=y_pred.shape[1]
  image_size=cell_size*output_size
  
  y_pred=copy.deepcopy(y_pred)
  if decode_preds:
    y_pred[...,0]=K.sigmoid(y_pred[...,0])
    y_pred[...,3:5]=np.clip((K.exp(y_pred[...,3:5])*tf_anchors).numpy(),0,output_size)
  # y_pred[...,3:5]=np.clip(y_pred[...,3:5],0,output_size)
  objs_found=[]
  idxs=np.where(y_pred[...,0]>=p)
  if np.size(idxs):
    for i,obj in enumerate(y_pred[idxs[0],idxs[1],idxs[2],:]):
      # obj (p,x,y,w,h,c_1,c_2,c_3,c_4,c_5.......c_n)
      if decode_preds:
        obj[1:3]=K.sigmoid(obj[1:3]) # x,y
    
      prob=obj[0]
      obj=obj[1:]
      
      obj[4]=np.argmax(obj[4:])
      obj=obj[:5]      

      obj[0]=idxs[1][i]+obj[0]  # center x
      obj[1]=idxs[0][i]+obj[1]  # center y

      obj[0]=np.clip(obj[0]-(obj[2]/2),0,output_size)  # xmin
      obj[1]=np.clip(obj[1]-(obj[3]/2),0,output_size)  # ymin
      
      
      obj_name=idx_to_class[obj[4]]
      
      
      obj_details={'p':prob,'xywh':list(obj[:-1]/output_size),'class_idx':int(obj[4]),'class':obj_name}  # xywh are scaled 0 to 1
      if idx is not None:obj_details['idx']=idx
      objs_found.append(obj_details)
  objs_found=sorted(objs_found,key=lambda x:x['p'],reverse=True)
  return objs_found

def list_get_iou(bboxes1, bboxes2):

    bboxes1 = [bboxes1[0],bboxes1[1],bboxes1[0]+bboxes1[2],bboxes1[1]+bboxes1[3]]
    bboxes2 = [bboxes2[0],bboxes2[1],bboxes2[0]+bboxes2[2],bboxes2[1]+bboxes2[3]]

    xA = max(bboxes1[0], bboxes2[0])
    yA = max(bboxes1[1], bboxes2[1])
    xB = min(bboxes1[2], bboxes2[2])
    yB = min(bboxes1[3], bboxes2[3])

    intersection_area = max(0, xB - xA ) * max(0, yB - yA )

    box1_area = (bboxes1[2] - bboxes1[0] ) * (bboxes1[3] - bboxes1[1] )
    box2_area = (bboxes2[2] - bboxes2[0] ) * (bboxes2[3] - bboxes2[1] )

    iou = intersection_area / float(box1_area + box2_area - intersection_area+1e-6)

    return iou

def nms(objs_found,iou_threshold=0.2):
  objs_found=np.array(copy.deepcopy(objs_found))
  best_boxes=[]
  while len(objs_found)>0:
    obj=objs_found[0]
    objs_found=objs_found[1:]

    delete_idx=[]
    for b_idx,b in enumerate(objs_found):

      if obj['class_idx']==b['class_idx']:
        iou=list_get_iou(obj['xywh'],b['xywh'])
        if iou>= iou_threshold:
          delete_idx.append(b_idx)
    objs_found=np.delete(objs_found,delete_idx)
    best_boxes.append(obj)
  return best_boxes

def show_objects(img,objs_found,return_img=False):
  plt.imshow(img)
  for i in range(len(objs_found)):  
    p=objs_found[i]['p']
    obj=objs_found[i]['xywh']
    obj_name=objs_found[i]['class']
    plt.gca().add_patch(Rectangle((obj[0],obj[1]),(obj[2]),(obj[3]),linewidth=4,edgecolor=class_colors[obj_name],facecolor='none'))
    plt.text(obj[0],obj[1],obj_name)



def pred_image(img,objs_found,font_scale=2,thickness=4):
  for i in range(len(objs_found)):  
    p=objs_found[i]['p']
    obj=np.array(objs_found[i]['xywh'])*img.shape[0]
    obj_name=objs_found[i]['class']
    
    img=cv2.rectangle(img,(int(obj[0]),int(obj[1])),(int(obj[0]+obj[2]),int(obj[1]+obj[3])),(class_colors[obj_name]*255),thickness)
    img=cv2.putText(img,obj_name,(int(obj[0]),int(obj[1])),cv2.FONT_HERSHEY_SIMPLEX,font_scale, (0,0,0), thickness, lineType=cv2.LINE_AA)
    # draw_text(img, "world", font_scale=4, pos=(10, 20 + h), text_color_bg=(255, 0, 0))
  return img