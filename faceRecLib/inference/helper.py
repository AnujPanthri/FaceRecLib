import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import transforms

def show_objects(img, objs_found):
    if (type(img) == str):
        img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)
    
    img_h,img_w,_=img.shape

    plt.figure()
    plt.imshow(img)
    for i in range(len(objs_found)):
        # p,c_name,x,y,w,h
        p = objs_found[i][0]
        obj_name = objs_found[i][1]
        _,_,xmin,ymin,w,h=objs_found[i]
        xmin , w = int(xmin*img_w) , int(w*img_w) 
        ymin , h = int(ymin*img_h) , int(h*img_h) 
        xmax , ymax = xmin+w , ymin+h

        color=np.random.rand(3)
        rectangle=Rectangle((xmin, ymin), w,h,
                      linewidth=4,
                      edgecolor=color,
                      facecolor='none')
        
        plt.gca().add_patch(rectangle)
        
        plt.text(xmin, ymin, obj_name,color="white",backgroundcolor=color)
        # ax=plt.gca()
        # plt.text(xmin, ymin, obj_name,color="white",transform=ax.transData)
    plt.axis("off")
    plt.show()



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
