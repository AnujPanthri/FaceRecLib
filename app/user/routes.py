from flask import render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from app.user import bp, session_expiring_time, settings
from app.helper import generate_random_id, access_database_as_admin, image_to_base64, base64_to_image, add_row_user_table, read_row_user_table, read_user_table, remove_person_from_user_table
from datetime import datetime, timedelta
from PIL import ImageOps
from copy import deepcopy
from PIL import Image
import os
import numpy as np
from app import face_detector, face_recognizer, aligner_obj, fd_get_crops, fr_helper, fd, fr
from config import user_config


@bp.before_request
def make_session_permanent():
  session.permanent = True


@bp.route("/register/")
def registeration_page():
  return render_template("user/registeration.html")


@bp.route('/is_username_available/', methods=["GET"])
def is_username_available():

  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  cursor.execute("select username from users where username=%s",
                 [request.args['username']])
  db_username = cursor.fetchone()
  dataBase.close()

  if None == db_username:
    return jsonify({"available": True})
  else:
    return jsonify({"available": False})


@bp.route("/add_account/", methods=["POST"])
def add_account():

  password_hash = generate_password_hash(request.form['password'])

  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  cursor.execute(
      "insert into users(username,password,request_message) values(%s,%s,%s)",
      (request.form['username'], password_hash,
       request.form['request_message'][:200]))
  dataBase.commit()
  dataBase.close()

  return redirect("/user/login/")


@bp.route("/login/")
def login_page():
  return render_template("user/login.html")


@bp.route("/login/<message>")
def login_page_message(message):
  return render_template("user/login.html",
                         message_class='active',
                         message=message)


def get_random_unique_id():
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()

  while (True):
    random_id = generate_random_id()
    cursor.execute("select username from session_table where session_token=%s",
                   [random_id])
    if cursor.fetchone() is None:
      break
  dataBase.close()
  return random_id


@bp.route("/authenticate/", methods=["POST"])
def authenticate():
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  cursor.execute("select password from users where username=%s",
                 [request.form['username']])
  db_password_hash = cursor.fetchone()
  dataBase.close()

  # print(db_password_hash)
  if None == db_password_hash:
    # username doesn't exists
    return redirect(
        url_for('user.login_page_message', message="username doesn't exists"))

  elif (check_password_hash(db_password_hash[0], request.form['password'])):
    # set session and login
    session.permanent = True

    session['user'] = {'token': get_random_unique_id()}
    session['user']['username'] = request.form['username']
    # session['user_token']=get_random_unique_id()

    expiring_time = (datetime.now() +
                     session_expiring_time).strftime('%Y-%m-%d %H:%M:%S')

    dataBase = access_database_as_admin()
    cursor = dataBase.cursor()
    cursor.execute(
        "insert into session_table(username,session_token,expiring_time) values(%s,%s,%s)",
        (request.form['username'], session['user']['token'], expiring_time))
    dataBase.commit()
    dataBase.close()

    return redirect("/user/")
  else:
    # incorrect password
    return redirect(
        url_for('user.login_page_message', message="Incorrect password"))


def is_auth(func):

  def wrapper_func(*args, **kwargs):
    if "user" not in session:
      return redirect(
          url_for('user.login_page_message', message="login in first"))
    elif 'token' not in session["user"]:
      return redirect(
          url_for('user.login_page_message', message="login in first"))
    else:
      dataBase = access_database_as_admin()
      cursor = dataBase.cursor()
      # delete expired sessions
      curr_time = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
      cursor.execute("delete from session_table where expiring_time<%s",
                     [curr_time])
      dataBase.commit()
      # check current session
      cursor.execute(
          "select username from session_table where session_token=%s",
          [session['user']['token']])
      if cursor.fetchone() is None:
        # no such session in db records
        dataBase.close()
        return redirect(
            url_for('user.login_page_message', message="session expired"))
      else:
        dataBase.close()
        return func(*args, **kwargs)

  # Renaming the function name:
  wrapper_func.__name__ = func.__name__
  return wrapper_func


@bp.route("/")
@is_auth
def user_dashboard():
  # return session["user_token"]
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()

  cursor.execute(
      "select username,request_message,access_key from users where username=%s",
      [session['user']['username']])

  data = cursor.fetchone()
  data_dict = dict(zip(cursor.column_names, data))
  dataBase.close()

  print(data_dict)
  return render_template("user/dashboard.html", data_dict=data_dict)


def get_random_unique_access_key():
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()

  while (True):
    random_access_key = generate_random_id()
    cursor.execute("select username from users where access_key=%s",
                   [random_access_key])
    if cursor.fetchone() is None:
      break
  dataBase.close()
  return random_access_key


@bp.route("/update_key/")
@is_auth
def update_key():
  # return session["user_token"]
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  cursor.execute(
      "select access_key from users where access_key is not null and access_key!='rejected' and username=%s",
      [session['user']['username']])
  data = cursor.fetchone()
  print(data)
  if data is not None:
    newkey = get_random_unique_access_key()
    cursor.execute("update users set access_key=%s where username=%s",
                   [newkey, session['user']['username']])
    dataBase.commit()
    dataBase.close()
    return {"message": "success", "key": newkey}
  else:
    dataBase.close()
    return {"message": "you are a hacker"}


#################################################################################################################################################
def load_settings(func):

  def wrapper_func(*args, **kwargs):
    # set face detector settings
    face_detector.p_thres = settings['p_thres']
    face_detector.nms_thres = settings['nms_thres']
    # we will set image_size inside routes

    # set face aligner settings
    aligner_obj.face_mesh_images.min_detection_confidence = settings['a_thres']

    # set face recognizer settings
    face_recognizer.thres = settings['d_thres']

    return func(*args, **kwargs)

  # Renaming the function name:
  wrapper_func.__name__ = func.__name__
  return wrapper_func


def get_image_size(mode):
  if mode == 'small':
    return [settings['small_size']]
  elif mode == 'large':
    return [settings['large_size']]
  elif mode == 'both':
    return [settings['small_size'], settings['large_size']]
  else:
    raise ("Error")


def get_default_settings():
  settings_dict = {}
  #p_thres,nms_thres,small_size,large_size,d_thres,a_thres,db_mode,fr_mode

  #p_thres,nms_thres
  settings_dict['p_thres'] = face_detector.model_config.p_thres
  settings_dict['nms_thres'] = face_detector.model_config.nms_thres
  # d_thres
  settings_dict['d_thres'] = face_recognizer.model_config.d_thres

  #small_size,large_size,a_thres,db_mode,fr_mode
  settings_dict.update(user_config)

  return settings_dict


@bp.route("/get_settings/", methods=['GET'])
def get_settings():
  global settings

  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  cursor.execute("select * from user_settings where username=%s",
                 [session['user']['username']])
  settings = cursor.fetchone()
  columns = cursor.column_names

  if settings is None:
    # get default settings and insert a row in user_settings

    settings = get_default_settings()
    columns = [
        "p_thres", "nms_thres", "small_size", "large_size", "d_thres",
        "a_thres", "db_mode", "fr_mode"
    ]

    cursor.execute(
        f"insert into user_settings(username,{','.join(columns)}) values(%s,{','.join(map(lambda x:'%s',columns))})",
        [session['user']['username']] + [settings[col] for col in columns])

  else:
    settings = dict(zip(columns, settings))

  # Disconnecting from the server
  dataBase.commit()
  dataBase.close()

  print("\n\nsee:", settings['p_thres'], "\n\n")

  return settings


@bp.route("/reset_settings/", methods=['GET'])
def reset_settings():
  global settings

  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()

  settings = get_default_settings()
  columns = [
      "p_thres", "nms_thres", "small_size", "large_size", "d_thres", "a_thres",
      "db_mode", "fr_mode"
  ]

  print(settings)
  cursor.execute(
      f"update user_settings set {','.join(list(map(lambda x:x+'=%s',columns)))} where username=%s;",
      [settings[col] for col in columns] + [session['user']['username']])

  # Disconnecting from the server
  dataBase.commit()
  dataBase.close()

  return {"message": "success", **settings}


@bp.route("/update_settings/", methods=['POST'])
def update_settings():
  json_data = request.get_json()

  # print(json_data)
  settings['p_thres'] = float(json_data['p_thres'])
  settings['nms_thres'] = float(json_data['nms_thres'])
  settings['large_size'] = int(json_data['large_size'])
  settings['small_size'] = int(json_data['small_size'])
  settings['d_thres'] = float(json_data['d_thres'])
  settings['a_thres'] = float(json_data['a_thres'])
  settings['db_mode'] = json_data['db_mode']
  settings['fr_mode'] = json_data['fr_mode']

  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()
  valuess = ', '.join([
      str(data[0]) + ' = \'' + str(data[1]) + '\'' for data in settings.items()
  ])
  cursor.execute(f"update user_settings SET {valuess} where username=%s",
                 (session['user']['username'],))

  # Disconnecting from the server
  dataBase.commit()
  dataBase.close()

  return {"message": "success"}


#################################################################################################################################################


@bp.route("/get_crops/", methods=["POST"])
@is_auth
@load_settings
def get_crops():

  print(request.form)
  file = request.files['image']

  image = Image.open(file.stream).convert("RGB")
  image = ImageOps.exif_transpose(image)
  image = np.array(image)
  print(image.shape)
  # do your deep learning work
  face_detector.image_size = get_image_size(settings['db_mode'])
  objs_found = face_detector.predict(image)
  print(image.shape)

  all_aligned_crops = fd_get_crops(
      image,
      objs_found,
      aligner_obj,
      resize=(face_recognizer.model_config.input_size,
              face_recognizer.model_config.input_size))
  all_aligned_crops_base64 = []

  for i, aligned_crop in enumerate(all_aligned_crops):
    all_aligned_crops_base64.append(image_to_base64(aligned_crop))

  return jsonify({"message": "successful", "crops": all_aligned_crops_base64})


def get_random_unique_person_id(username):
  dataBase = access_database_as_admin()
  cursor = dataBase.cursor()

  while (True):
    random_id = generate_random_id()
    cursor.execute(f"select person_id from user_{username} where person_id=%s",
                   [random_id])
    if cursor.fetchone() is None:
      break
  dataBase.close()
  return random_id


@bp.route("/set_crops/", methods=["POST"])
@is_auth
@load_settings
def set_crops():

  # print(request.form)
  json_data = request.get_json()
  person_name = json_data['person_name']
  remarks = json_data['remarks']
  print(person_name)
  all_remarks = []
  all_remarks_features = []
  for remark in remarks.keys():
    all_img_features = []
    for img_base64 in remarks[remark]:
      img = base64_to_image(img_base64)
      # print(remark,img.shape)

      all_img_features.append(
          face_recognizer.feature_extractor.predict(img[None, :, :, ::-1],
                                                    verbose=0)[0])
    all_img_features = np.array(all_img_features)
    all_remarks_features.append(all_img_features.mean(axis=0))
    all_remarks.append(remark)

  all_remarks_features = np.array(all_remarks_features)

  print(all_remarks_features.shape)
  print(all_remarks)

  username = session['user']['username']
  print(username)

  add_row_user_table(username=username,
                     person_id=person_name,
                     face_vectors=all_remarks_features.astype("float64"),
                     remarks=",".join(all_remarks),
                     group_id=None)
  read_row_user_table(username)

  return jsonify({"message": "successful"})


@bp.route("/face_recognize/", methods=["POST"])
@is_auth
@load_settings
def face_recognition():

  # print(request.form)
  file = request.files['image']

  image = Image.open(file.stream).convert("RGB")
  image = ImageOps.exif_transpose(image)
  image = np.array(image)
  face_detector.image_size = get_image_size(settings['fr_mode'])

  username = session['user']['username']
  print(username)
  data = read_user_table(username)
  faces = data['person_id']
  db_faces_features = data['face_vectors']

  for i in range(len(faces)):
    print(faces[i], ":", db_faces_features[i].shape)

  # face_recognizer.set_face_db_and_mode(faces=faces,db_faces_features=db_faces_features,distance_mode="avg",recognition_mode="repeat")
  face_recognizer.set_face_db_and_mode(faces=faces,
                                       db_faces_features=db_faces_features,
                                       distance_mode="best",
                                       recognition_mode="repeat")

  objs_found = face_detector.predict(image)
  h, w = image.shape[:2]

  tree = fr_helper.objs_found_to_xml("test.jpg", w, h, objs_found)
  if len(faces) > 0:
    tree = face_recognizer.predict(image, tree)

  pred_img = fr_helper.show_pred_image(tree, image)
  pred_img = image_to_base64(pred_img)

  objs_found = fr_helper.xml_to_objs_found(tree)

  return jsonify({
      "message": "success",
      "pred_image": pred_img,
      "objs_found": objs_found
  })


@bp.route("/get_all_persons_from_db/", methods=["GET"])
@is_auth
def get_all_persons_from_db():

  # print(request.form)

  username = session['user']['username']
  print(username)
  data = read_user_table(username, split_remarks=False)

  return jsonify({
      "message": "success",
      "person_ids": data["person_id"],
      "remarks": data["remarks"]
  })
  # return jsonify({"message":"success",'image':pred_img})


@bp.route("/remove_person_from_db/", methods=["POST"])
@is_auth
def remove_person_from_db():

  username = session['user']['username']
  print(username)
  remove_person_from_user_table(username, request.get_json()["person_id"])

  return jsonify({"message": "success"})
  # return jsonify({"message":"success",'image':pred_img})
