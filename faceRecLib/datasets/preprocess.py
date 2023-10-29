import os
import shutil
from glob import glob
import cv2
import xml.etree.ElementTree as ET
import numpy as np
from tqdm import tqdm
# import mxnet as mx



def mxnet_to_folder(idx_path, rec_path, save_folder_dir):
    '''
    generate Mxnet type dataset to folder structure:
    example :
    "faces_webface_112x112/train.idx","faces_webface_112x112/train.rec" files 
    to folder structure like:-

    folder -
             personA -
                       1.jpg
                       2.jpg
                       3.jpg
             personB -
                       1.jpg
                       2.jpg
                       3.jpg
             personC -
                       1.jpg
                       2.jpg
                       3.jpg
         

    '''
    if os.path.exists(save_folder_dir):
        shutil.rmtree(save_folder_dir)

    imgrec = mx.recordio.MXIndexedRecordIO(
        idx_path, rec_path, "r"
    )
    s = imgrec.read_idx(0)
    header, _ = mx.recordio.unpack(s)
    # print(header.label)

    for ii in tqdm(list(range(1, int(header.label[0])))):
        img_info = imgrec.read_idx(ii)
        header, img = mx.recordio.unpack(img_info)

        # # img_idx = str(int(np.sum(header.label)))
        img_idx = str(
            int(header.label if isinstance(header.label, float) else header.label[0])
        )
        # print(img_idx,img)
        img_save_dir = os.path.join(save_folder_dir, img_idx)
        if not os.path.exists(img_save_dir):
            os.makedirs(img_save_dir)
        with open(os.path.join(img_save_dir, str(ii) + ".jpg"), "wb") as ff:
            ff.write(img)





def _load_xml_label(xml_file,image_dir):

    objs_list=[]
    tree=ET.parse(xml_file)
    root=tree.getroot()
    width,height=int(root.find('size').find('width').text),int(root.find('size').find('height').text)

    filename=image_dir+root.find("filename").text
   
    for member in root.findall("object"):
      bndbox=member.find('bndbox')
      xmin,ymin , xmax,ymax=np.clip(int(bndbox.find('xmin').text),0,width),np.clip(int(bndbox.find('ymin').text),0,height),np.clip(int(bndbox.find('xmax').text),0,width),np.clip(int(bndbox.find('ymax').text),0,height)
      value=(
              member.find('name').text.lower(),
              
              xmin,  # xmin
              ymin,  # ymin

              xmax,  # xmax
              ymax,  # ymax

            )
      objs_list.append(value)
    return filename,objs_list

def _add_slash(path):
    if not path.endswith("/"):
        path+="/"
    return path

def pascal_voc_to_folder(image_dir,annotation_dir,save_dir):
    
    image_dir=_add_slash(image_dir)
    annotation_dir=_add_slash(annotation_dir)
    save_dir=_add_slash(save_dir)
    
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.makedirs(save_dir)

    for xml_path in tqdm(glob(annotation_dir+"*.xml")):
        image_path,objs_list=_load_xml_label(xml_path,image_dir)
        
        img=cv2.imread(image_path)
        for i,obj in enumerate(objs_list):
            #obj [classname,xmin,ymin,xmax,ymax]
            classname=obj[0]
            crop_img=img[obj[2]:obj[4],obj[1]:obj[3]]
            
            if not os.path.exists(save_dir+classname):
                os.mkdir(save_dir+classname)
            cv2.imwrite(save_dir+f"{classname}/{i}.jpg",crop_img)

