from flask import request,jsonify,g,session
from app.api import bp
from app.helper import generate_random_id,access_database_as_admin,image_to_base64,base64_to_image,add_row_user_table,read_row_user_table,read_user_table,remove_person_from_user_table
from PIL import ImageOps,Image
import numpy as np

from app import face_detector,face_recognizer,aligner_obj,fd_get_crops,fr_helper

from config import demo_config


##################################################################settings#######################################################################

def set_image_size(settings,mode):
    if mode=='small':
        face_detector.image_size=[settings['small_size']]
    elif mode=='large':
        face_detector.image_size=[settings['large_size']]
    elif mode=='both':
        face_detector.image_size=[settings['small_size'],settings['large_size']]
    else:
        raise("Error")
    
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

def get_settings(username):
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    cursor.execute("select * from user_settings where username=%s",[username])
    settings=cursor.fetchone()
    columns=cursor.column_names

    if settings is None:
        # get default settings and insert a row in user_settings
        cursor.execute("select p_thres,nms_thres,small_size,large_size,d_thres,a_thres,db_mode,fr_mode from default_settings where page='user'")
        settings=cursor.fetchone()
        columns=cursor.column_names
        cursor.execute(f"insert into user_settings(username,{','.join(columns)}) values(%s,{','.join(map(lambda x:'%s',columns))})",(session['user']['username'],)+settings)
    
    
    settings= dict(zip(columns, settings))
    # Disconnecting from the server
    dataBase.commit()
    dataBase.close()
    return settings

def load_settings(settings):
    

    # set face detector settings
    face_detector.p_thres=settings['p_thres']
    face_detector.nms_thres=settings['nms_thres']
    # we will set image_size inside routes

    # set face aligner settings
    aligner_obj.face_mesh_images.min_detection_confidence=settings['a_thres']

    # set face recognizer settings
    face_recognizer.thres=settings['d_thres']

    return settings

############################################################settings_end#########################################################################

def is_auth(func):
    def wrapper_func(*args,**kwargs):
        if "access_key" not in request.form: return jsonify({"message":"send access key too"})
        else:
            dataBase = access_database_as_admin()
            cursor=dataBase.cursor()
            cursor.execute("select username from users where access_key=%s",[request.form["access_key"]])
            data=cursor.fetchone()
            if data is None:
                dataBase.close()
                return jsonify({"message":"no such access key in database"})
            else:
                dataBase.close()
                return func(data[0],*args,**kwargs)
    # Renaming the function name:
    wrapper_func.__name__ = func.__name__
    return wrapper_func


#################################################################change_db############################################################################
@bp.route("/add_person/",methods=["POST"])
@is_auth
def add_person(username):

    # print(request.form)
    json_data=request.get_json()
    person_name=json_data['person_name']
    remarks=json_data['remarks']
    group_id=json_data["group_id"] if "group_id" in json_data else None
    print(person_name)
    all_remarks=[]
    all_remarks_features=[]
    for remark in remarks.keys():
        all_img_features=[]
        for img_base64 in remarks[remark]:
            img=base64_to_image(img_base64)
            # print(remark,img.shape)
            
            all_img_features.append(face_recognizer.feature_extractor.predict(img[None,:,:,::-1],verbose=0)[0])
        all_img_features=np.array(all_img_features)
        all_remarks_features.append(all_img_features.mean(axis=0))
        all_remarks.append(remark)
        
    all_remarks_features=np.array(all_remarks_features)

    print(all_remarks_features.shape)
    print(all_remarks)
    print(username)

    add_row_user_table(username=username,person_id=person_name,face_vectors=all_remarks_features.astype("float64"),remarks=",".join(all_remarks),group_id=group_id)
    read_row_user_table(username)
    
        
    
    return jsonify({"message":"success"})


@bp.route("/remove_person/",methods=["POST"])
@is_auth
def remove_person(username):

    print(username)
    remove_person_from_user_table(username,request.get_json()["person_id"])

    return jsonify({"message":"success"})
    # return jsonify({"message":"success",'image':pred_img})

#################################################################change_db_end############################################################################

@bp.route("/get_crops/",methods=["POST"])
@is_auth
def get_crops(username):

    settings=get_settings(username)

    for setting in settings.keys():
        if setting in request.form:
            settings[setting]=request.form[setting]

    load_settings(settings)

    set_image_size(settings,settings["db_mode"])
    if "image_size" in request.form: face_detector.image_size=list(map(lambda x:int(x),request.form["image_size"].split(",")))
    print(face_detector.image_size)

    file = request.files['image']
    
    image=Image.open(file.stream).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image=np.array(image)
    print(image.shape)

    image,objs_found=face_detector.predict(image)
    print(objs_found)
      
    all_aligned_crops=fd_get_crops(image,objs_found,aligner_obj,resize=(face_recognizer.model_config.input_size,face_recognizer.model_config.input_size))
    all_aligned_crops_base64=[]

    for i,aligned_crop in enumerate(all_aligned_crops):
        all_aligned_crops_base64.append(image_to_base64(aligned_crop))

    return jsonify({"message":"success","crops":all_aligned_crops_base64})






@bp.route("/face_recognize/",methods=["POST"])
@is_auth
def face_recognition(username):

    settings=get_settings(username)

    for setting in settings.keys():
        if setting in request.form:
            settings[setting]=request.form[setting]

    load_settings(settings)
    set_image_size(settings,settings["fr_mode"])
    if "image_size" in request.form: face_detector.image_size=list(map(lambda x:int(x),request.form["image_size"].split(",")))
    print(face_detector.image_size)

    # print(request.form)
    file = request.files['image']
    
    image=Image.open(file.stream).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image=np.array(image)
    print(image.shape)

    print(username)
    data=read_user_table(username) if "group_id" not in request.form else read_user_table(username,request.form["group_id"])
    faces=data['person_id']
    db_faces_features=data['face_vectors']

    for i in range(len(faces)):
        print(faces[i],":",db_faces_features[i].shape)
    
    
    img,objs_found=face_detector.predict(image)
    h,w=img.shape[:2]
    tree=fr_helper.objs_found_to_xml("test.jpg",w,h,objs_found)

    # face_recognizer.set_face_db_and_mode(faces=faces,db_faces_features=db_faces_features,distance_mode="avg",recognition_mode="repeat")
    face_recognizer.set_face_db_and_mode(faces=faces,db_faces_features=db_faces_features,distance_mode="best",recognition_mode="repeat")

    if len(faces)>0:
        tree=face_recognizer.predict(img,tree)
        
        
    # print(objs_found[0])
    

    pred_img=fr_helper.show_pred_image(tree,img)
    pred_img=image_to_base64(pred_img)
    objs_found=fr_helper.xml_to_objs_found(tree) # everything is okay till here
    
    objs_found=face_detector.square_preprocessing.rescale(objs_found)   #rescale coordinates to original image's resolution
    # print(objs_found[0])

    all_crops=fd_get_crops(image,objs_found)
    all_crops_base64=[]

    for i,aligned_crop in enumerate(all_crops):
        all_crops_base64.append(image_to_base64(aligned_crop))
    
    person_ids=[obj_found['class'] for obj_found in objs_found]

    return jsonify({"message":"success","pred_image":pred_img,"person_ids":person_ids,"crops":all_crops_base64,"objs_found":objs_found})