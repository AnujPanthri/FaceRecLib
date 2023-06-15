import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import copy




def tiler(img,image_size,tiles=2,pad=0,):
    # pad is 0 to 0.9%
    h,w=img.shape[:2]

    tile_h=(h//tiles)
    tile_w=(w//tiles)
    
    pad=int(tile_h*pad)
    
    crops=[]
    coordinates=[]
    for i in range(tiles):
        for j in range(tiles):
            ymin=tile_h*i
            xmin=tile_w*j
        
            if i!=0:ymin=ymin-pad
            if j!=0:xmin=xmin-pad

            ymax=min(ymin+tile_h+pad,h)
            xmax=min(xmin+tile_w+pad,w)

            # crops.append(img[ymin:ymax,xmin:xmax])
            crops.append(cv2.resize(img[ymin:ymax,xmin:xmax],[image_size,image_size]))
            coordinates.append((xmin,ymin,xmax,ymax))
            # print(crops[-1].shape)
    return coordinates,np.array(crops)
    
class square_crop:
    def __call__(self,img):
        h,w=img.shape[:2]
        self.w_removed,self.h_removed=0,0
        if w>h:
            self.w_removed=(w-h)//2
            img=img[:,self.w_removed:w-self.w_removed]
        elif h>w:
            self.h_removed=(h-w)//2
            img=img[self.h_removed:h-self.h_removed,:]
        
        h,w=img.shape[:2]
        self.w_removed,self.h_removed=self.w_removed/w,self.h_removed/h
        return img
    def rescale(self,objs_found):
        raise NotImplementedError

class square_pad:
    def __init__(self,color=(0,0,0)):
        self.color=color
    def __call__(self,img):
        h,w=img.shape[:2]
        self.w_added,self.h_added=0,0
        if h>w:
            self.w_added=int((h-w)/2)
            padding=(np.ones([h,self.w_added,3])*np.array(self.color)[None,None,:]).astype("uint8")
            img=np.concatenate([padding,img,padding],axis=1)
        elif w>h:
            self.h_added=int((w-h)/2)
            padding=(np.ones([self.h_added,w,3])*np.array(self.color)[None,None,:]).astype("uint8")
            img=np.concatenate([padding,img,padding],axis=0)
        h,w=img.shape[:2]
        
        self.w_added,self.h_added=self.w_added/w,self.h_added/h
        
        return img
    def rescale(self,objs_found):
        
        for i in range(len(objs_found)):
            objs_found[i]['xywh'][0]=(objs_found[i]['xywh'][0]-self.w_added)/(1-2*self.w_added)
            objs_found[i]['xywh'][1]=(objs_found[i]['xywh'][1]-self.h_added)/(1-2*self.h_added)
            objs_found[i]['xywh'][2]=(objs_found[i]['xywh'][2])/(1-2*self.w_added)
            objs_found[i]['xywh'][3]=(objs_found[i]['xywh'][3])/(1-2*self.h_added)
        return objs_found


class face_detection:
    def __init__(self,model_path):
        ################### set num_anchors & tf_anchors ###################
        anchor_boxes=np.loadtxt(model_path+"/anchors.txt")
        num_anchors=anchor_boxes.shape[0]
        tf_anchors=K.reshape(K.variable(anchor_boxes),[1, 1, 1, num_anchors, 2])
        load_model_lib.num_anchors=num_anchors
        decode_model_lib.tf_anchors=tf_anchors
        ####################################################################
        
        self.model=load_model(model_path+"/model.h5")
        
        self.modes_available=["tiled","sized"]
        self.square_preprocessing=square_crop

    def invoke_model(self,img,p=0.2,iou_threshold=0.3,batch_size=4):
        all_objs_found=[]
        
        for i in range(math.ceil(img.shape[0]/batch_size)):

            y_pred=self.model.predict(img[int(i*batch_size):int((i+1)*batch_size)].astype('float32'),verbose=0)
            # print(y_pred.shape)
            
            for i in range(y_pred.shape[0]):
                objs_found=get_objects(y_pred[i],p=p)
                objs_found=nms(objs_found,iou_threshold=iou_threshold)
                all_objs_found.append(objs_found)
        
        return all_objs_found
    def get_tiled_output(self,img,p_thres,nms_thres,tiles,pad,image_size,save_tiles=None,batch_size=4): 
        # pad is 0 to 0.5%
        # pad=0.05       
        img=cv2.resize(img,[image_size*tiles,image_size*tiles])
    
        coordinates,crops=tiler(img,tiles=tiles,pad=pad,image_size=image_size)
        
        all_objs_found=self.invoke_model(crops,p_thres,nms_thres,batch_size)

        if save_tiles:
            fig=plt.figure(figsize=(3*tiles,3*tiles))
            plt.axis("off")
            plt.title(f"pad:{pad}")

            for i in range(int(tiles*tiles)): 
                fig.add_subplot(tiles,tiles,i+1)
                plt.axis("off")
                plt.imshow(pred_image(crops[i],all_objs_found[i]))
            # plt.show(block=False)
            plt.savefig(save_tiles+f"_{tiles}.jpg")
            plt.close()
        
        all_objs_found_joined=[]
        for i in range(int(tiles*tiles)): 
            xmin,ymin,xmax,ymax=coordinates[i]
            w,h=xmax-xmin,ymax-ymin
            for j in range(all_objs_found[i].__len__()):
                # all_objs_found[i][j]['xywh']=np.array(all_objs_found[i][j]['xywh'])/image_size
                all_objs_found[i][j]['xywh']=np.array(all_objs_found[i][j]['xywh'])*w
                all_objs_found[i][j]['xywh'][0]+=xmin
                all_objs_found[i][j]['xywh'][1]+=ymin
                all_objs_found[i][j]['xywh']=(all_objs_found[i][j]['xywh']/(image_size*tiles)).tolist()
            all_objs_found_joined.extend(all_objs_found[i])

        all_objs_found_joined=sorted(all_objs_found_joined,reverse=True,key=lambda x:x["p"]) # This was very important
        all_objs_found_joined=nms(all_objs_found_joined,nms_thres)
        

        return all_objs_found_joined


    def set_mode(self,p_thres,nms_thres,batch_size=4,mode="tiled",**kwargs):
        # mode : tiled or sized
        
        self.p_thres=p_thres
        self.nms_thres=nms_thres
        self.batch_size=batch_size

        if mode=="tiled":
            try:
                self.image_size=kwargs['image_size']
                if "tiles" not in kwargs:
                    self.tiles=[1]
                    self.pad=0
                else:
                    self.tiles=kwargs['tiles'] if(type(kwargs['tiles'])==type(list([1])) or type(kwargs['tiles'])==type(np.zeros([]))) else [kwargs['tiles']]
                    self.pad=kwargs['pad']
            except:
                
                raise ValueError(f"Not all tiled mode parameters passed.")
            
            self.save_tiles=kwargs["save_tiles"] if ("save_tiles" in kwargs) else None
            
        elif mode=="sized":
            try:
                # self.image_size=kwargs['image_size']
                self.image_size=kwargs['image_size'] if(type(kwargs['image_size'])==type(list([1])) or type(kwargs['image_size'])==type(np.zeros([]))) else [kwargs['image_size']]
                self.batch_size=1
            except:
                raise ValueError(f"Not all Sized mode parameters passed.")
        else:
            raise ValueError(f"Unavailable mode={mode} \nmode can only be one of:{self.modes_available}")
        
        self.mode=mode
        

    def predict_once(self,img):
        
        if (type(img)==str):
            img=cv2.cvtColor(cv2.imread(img),cv2.COLOR_BGR2RGB)
        elif (type(img)!=type(np.zeros([]))):
            raise TypeError(f"Inappropriate type of image={type(img)}")
        
        # if img.shape[0]!=img.shape[1]:  raise ValueError(f"The image should be squared")
        
    
        if  not hasattr(self,'mode'): raise ValueError(f"First call set_mode function to set mode using one of the following mode :{self.modes_available}")

        if self.mode=='tiled':
            if type(self.tiles)==type(list([1])) or type(self.tiles)==type(np.zeros([])):   raise TypeError("use advanced_predict function for inference on multiple tiles")
            objs_found=self.get_tiled_output(img,p_thres=self.p_thres,nms_thres=self.nms_thres,tiles=self.tiles,pad=self.pad,image_size=self.image_size,save_tiles=self.save_tiles)
        elif self.mode=='sized':
            if type(self.image_size)==type(list([1])) or type(self.image_size)==type(np.zeros([])):   raise TypeError("use advanced_predict function for inference on multiple sizes")
            resized_img=cv2.resize(img,[self.image_size,self.image_size])
            objs_found=self.invoke_model(resized_img[None,:,:,:],self.p_thres,self.nms_thres,batch_size=1)[0]

        return img,objs_found

    def predict(self,img):

        if (type(img)==str):
            img=cv2.cvtColor(cv2.imread(img),cv2.COLOR_BGR2RGB)
        elif (type(img)!=type(np.zeros([]))):
            raise TypeError(f"Inappropriate type of image={type(img)}")
        
        if img.shape[0]!=img.shape[1]:  img=self.square_preprocessing(img)

        if  not hasattr(self,'mode'): raise ValueError(f"First call set_mode function to set mode using one of the following mode :{self.modes_available}")

        if self.mode=="tiled":
            all_objs_found=[]
            all_tiles=copy.deepcopy(self.tiles)
            for tiles in all_tiles:
                self.tiles=tiles
                _,objs_found=self.predict_once(img)
                all_objs_found.extend(objs_found)
            self.tiles=all_tiles

        elif self.mode=="sized":
            all_objs_found=[]
            all_image_size=copy.deepcopy(self.image_size)
            for image_size in all_image_size:
                self.image_size=image_size
                _,objs_found=self.predict_once(img)
                all_objs_found.extend(objs_found)
            self.image_size=all_image_size
        all_objs_found=sorted(all_objs_found,reverse=True,key=lambda x:x["p"]) # This was very important
        all_objs_found=nms(all_objs_found,self.nms_thres)

        return img,all_objs_found





if __name__=="__main__":
    import create_load_model as load_model_lib
    import decode_yolo_v2 as decode_model_lib
    from create_load_model import *
    from decode_yolo_v2 import *
    

    face_detector=face_detection("face_detection/Models/v1/")
    
    # test_img="C:\\Users\\Home\\Downloads\\WhatsApp Image 2023-01-04 at 6.58.40 PM.jpeg"
    test_img="C:\\Users\\Home\\Downloads\\family-52.jpg"

    p_thres=0.5
    nms_thres=0.3
    tiles=3
    pad=0

    # face_detector.set_mode(p_thres,nms_thres,mode="tiled",tiles=[1,2],pad=pad,image_size=416,save_tiles="tile")
    # face_detector.set_mode(p_thres=p_thres,nms_thres=nms_thres,image_size=608)
    # face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=256)
    # face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=352)
    # face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=608)
    face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=1024)
    # face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=[608,1024])
    img,objs_found=face_detector.predict(test_img)
    # img,objs_found=face_detector.advanced_predict(test_img)
    pred_img=pred_image(img,objs_found)
    plt.figure()
    plt.imshow(pred_img)
    plt.show()
    # cv2.imwrite("test_output.jpg",pred_img[:,:,::-1])
else:
    import app.face_detection.create_load_model as load_model_lib
    import app.face_detection.decode_yolo_v2 as decode_model_lib
    from app.face_detection.create_load_model import *
    from app.face_detection.decode_yolo_v2 import *