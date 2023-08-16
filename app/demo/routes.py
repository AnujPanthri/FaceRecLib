from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import os
from glob import glob
import shutil
import io
import base64
import uuid
from flask import render_template,request,send_from_directory,session,jsonify,json
from app import helper
from PIL import ImageOps
from app.helper import generate_random_id,image_to_base64,base64_to_image
from app.demo import bp
import copy
from config import demo_config





from app import face_detector,face_recognizer,aligner_obj,fd_get_crops,fr_helper,fd,fr

# @bp.before_app_first_request
# def create_temp_path():
#     if not os.path.exists(temp_path):os.mkdir(temp_path)

# @bp.route(f"/{temp_path}/<subfolder>/<filename>")
# def upload(filename,subfolder):
#     return send_from_directory(temp_path+f"/{subfolder}/", filename)

@bp.route("/")
def index():
    return render_template('demo/index.html')

def load_settings(func):
    def wrapper_func(*args,**kwargs):
        # set face detector settings
        face_detector.p_thres=session["demo"]['settings']['p_thres']
        face_detector.nms_thres=session["demo"]['settings']['nms_thres']
        # we will set image_size inside routes

        # set face aligner settings
        aligner_obj.min_detection_confidence=session["demo"]['settings']['a_thres']

        # set face recognizer settings
        face_recognizer.thres=session["demo"]['settings']['d_thres']
        
        return func(*args,**kwargs)
    # Renaming the function name:
    wrapper_func.__name__ = func.__name__
    return wrapper_func

def get_image_size(mode):
    if mode=='small':
        return [session["demo"]['settings']['small_size']]
    elif mode=='large':
        return [session["demo"]['settings']['large_size']]
    elif mode=='both':
        return [session["demo"]['settings']['small_size'],session["demo"]['settings']['large_size']]
    else:
        raise("Error")
    

@bp.route("/add_crops/",methods=["POST"])
@load_settings
def set_crops():
    # set session
    if not "demo_token" in session:
        session["demo_token"]=helper.generate_random_id()

    
    # exit();
    # cursor.execute("insert into demo_sessions",[request.form['username']])

    print(request.form)
    file = request.files['image']
    print(file)
    fname = secure_filename(file.filename)

    image=Image.open(file.stream).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image=np.array(image)
    
    # do your deep learning work
    face_detector.image_size=get_image_size(session["demo"]['settings']['db_mode'])
    print(face_detector.image_size)

    objs_found=face_detector.predict(image)
    print(image.shape)
    all_aligned_crops=fd_get_crops(image,objs_found,aligner_obj,resize=(face_recognizer.model_config.input_size,face_recognizer.model_config.input_size))
    all_aligned_crops_base64=[]
    all_aligned_crops_names=[]

    for i,aligned_crop in enumerate(all_aligned_crops):
        all_aligned_crops_base64.append(helper.image_to_base64(aligned_crop))

    if (len(all_aligned_crops_base64)!=0):
        image=fd.pred_image(image,objs_found)       
    
    img_base64=helper.image_to_base64(image)
    print(img_base64[:10])
    
    return jsonify({"message":"successful","image":img_base64,"image_name":fname,"crops":all_aligned_crops_base64})


@bp.route("/update_crops_labels/",methods=["POST"])
@load_settings
def update_crops_labels():
    print(request.form.keys())
    
    imgs_base64=request.form['faces'].split(",")
    print(len(imgs_base64))
    all_img_features=[]
    for img_base64 in imgs_base64:
        img=cv2.resize(base64_to_image(img_base64),[face_recognizer.model_config.input_size,face_recognizer.model_config.input_size])
        all_img_features.append(face_recognizer.feature_extractor.predict(img[None,...],verbose=0)[0])
        all_img_features[-1]=all_img_features[-1].astype("float32").tobytes().decode("latin-1")
    
    print(all_img_features.__len__())    
    # for decoding numpy array
    # print(all_img_features[0])    
    # print(np.frombuffer(all_img_features[0].encode("latin-1"),dtype="float32"))    

    return jsonify({"message":"success","features":all_img_features})

@bp.route("/face_recognition/",methods=["POST"])
@load_settings
def face_recognition():
    
    file = request.files['image']
    # print(file)
    
    image=Image.open(file.stream).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image=np.array(image)
    db_images=json.loads(request.form['db_images'])
    
    db_faces_features=[]
    names=[]
    for name in db_images:
        names.append(name)
        person_features=[]
        for decoded_features in db_images[name]:
            person_features.append(np.frombuffer(decoded_features.encode("latin-1"),dtype="float32"))
        person_features=np.array(person_features)
        db_faces_features.append(person_features)
     
    for i in range(len(names)):
        print(names[i],":",db_faces_features[i].shape)
    
    # face_recognizer.set_face_db_and_mode(faces=names,db_faces_features=db_faces_features,distance_mode="avg",recognition_mode="repeat")
    face_recognizer.set_face_db_and_mode(faces=names,db_faces_features=db_faces_features,distance_mode="best",recognition_mode="repeat")
    
    face_detector.image_size=get_image_size(session["demo"]['settings']['fr_mode'])
    
    objs_found=face_detector.predict(image)
    h,w=image.shape[:2]
    
    tree=fr_helper.objs_found_to_xml("test.jpg",w,h,objs_found)

    tree=face_recognizer.predict(image,tree)

    pred_img=fr_helper.show_pred_image(tree,image)
    pred_img=helper.image_to_base64(pred_img)

    return jsonify({"message":"success",'image':pred_img})  


def get_default_settings():
    settings_dict={}
    #p_thres,nms_thres,small_size,large_size,d_thres,a_thres,db_mode,fr_mode
        
    #p_thres,nms_thres
    settings_dict['p_thres']=face_detector.model_config.p_thres
    settings_dict['nms_thres']=face_detector.model_config.nms_thres
    # d_thres
    settings_dict['d_thres']=face_recognizer.model_config.d_thres

    #small_size,large_size,a_thres,db_mode,fr_mode
    settings_dict.update(demo_config)
    
    return settings_dict

@bp.route("/get_settings/",methods=['GET'])
def get_settings():
    session.permanent=True
    if "demo" not in session:
        
        session["demo"]={'settings':dict()}
        session["demo"]['settings']=get_default_settings()
        

        
        
        

    return session["demo"]['settings']

@bp.route("/reset_settings/",methods=['GET'])
def reset_settings():
    del session["demo"]
    session["demo"]={'settings':dict()}
    session["demo"]['settings']=get_default_settings()

    return {"message":"success",**session["demo"]['settings']}

@bp.route("/update_settings/",methods=['POST'])
def update_settings():
    json_data=request.get_json()

    if "demo" not in session:
        session["demo"]={'settings':dict()}
    # print(json_data)
    session["demo"]['settings']['p_thres']=float(json_data['p_thres'])
    session["demo"]['settings']['nms_thres']=float(json_data['nms_thres'])
    session["demo"]['settings']['large_size']=int(json_data['large_size'])
    session["demo"]['settings']['small_size']=int(json_data['small_size'])
    session["demo"]['settings']['d_thres']=float(json_data['d_thres'])
    session["demo"]['settings']['a_thres']=float(json_data['a_thres'])
    session["demo"]['settings']['db_mode']=json_data['db_mode']
    session["demo"]['settings']['fr_mode']=json_data['fr_mode']

    return {"message":"success"}