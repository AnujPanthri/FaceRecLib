import cv2
import numpy as np


def pred_image(img, objs_found, font_scale=2, thickness=4):
    if (type(img) == str):
        img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)
    else:
        img=img.copy()

    img_h,img_w,_=img.shape

    for i in range(len(objs_found)):
        # p,c_name,x,y,w,h
        p = objs_found[i][0]
        obj_name = objs_found[i][1]
        
        _,_,xmin,ymin,w,h=objs_found[i]
        xmin , w = int(xmin*img_w) , int(w*img_w) 
        ymin , h = int(ymin*img_h) , int(h*img_h) 
        xmax , ymax = xmin+w , ymin+h
        
        img = cv2.rectangle(img, (xmin, ymin),
                            (xmax,ymax),
                            np.random.rand(3)*255, thickness)
        
        img = cv2.putText(img,
                          obj_name, (xmin,ymin),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          font_scale, (0, 0, 0),
                          thickness,
                          lineType=cv2.LINE_AA)
        
    return img
