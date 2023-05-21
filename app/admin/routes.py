from flask import render_template,request,jsonify,redirect,url_for,session
import mysql.connector
from werkzeug.security import generate_password_hash,check_password_hash
from app.admin import bp
from app.helper import generate_random_id,access_database_as_admin,create_user_table,drop_user_table


@bp.route("/login/")
def login_page():
    return render_template("admin/login.html")

@bp.route("/login/<message>")
def login_page_message(message):
    return render_template("admin/login.html",message_class='active',message=message)

def get_random_unique_id():
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    
    while(True):
        random_id=generate_random_id()
        cursor.execute("select username from admins where session_token=%s",[random_id])
        if cursor.fetchone() is None: break
    dataBase.close()
    return random_id
    


@bp.route("/authenticate/",methods=["POST"])
def authenticate():
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    cursor.execute("select password from admins where username=%s",[request.form['username']])
    db_password_hash=cursor.fetchone()
    dataBase.close()
    
    # print(db_password_hash)
    if None==db_password_hash:
        # username doesn't exists
        return redirect(url_for('admin.login_page_message', message = "username doesn't exists"))

    elif(check_password_hash(db_password_hash[0],request.form['password'])):
        # set session and login
        session.permanent = True
        
        session['admin_token']=get_random_unique_id()
        
        dataBase = access_database_as_admin()
        cursor=dataBase.cursor()
        cursor.execute("update admins set session_token=%s where username=%s",(session['admin_token'],request.form['username']))
        dataBase.commit()
        dataBase.close()
        
        return redirect("/admin/")
    else:
        # incorrect password 
        return redirect(url_for('admin.login_page_message', message = "Incorrect password"))




def is_auth(func):
    def wrapper_func(*args,**kwargs):
        if "admin_token" not in session:
            return redirect(url_for('admin.login_page_message', message = "login in first"))
        else:
            dataBase = access_database_as_admin()
            cursor=dataBase.cursor()
            cursor.execute("select username from admins where session_token=%s",[session['admin_token']])
            if cursor.fetchone() is None:
                # no such session in db records
                dataBase.close()
                return redirect(url_for('admin.login_page_message', message = "no such session in db"))
            else:
                dataBase.close()
                return func(*args,**kwargs)
    # Renaming the function name:
    wrapper_func.__name__ = func.__name__
    return wrapper_func
    
    
@bp.route("/")
@is_auth
def user_dashboard():
    return render_template("admin/dashboard.html")

@bp.route("/get_all_requests/", methods=["GET"])
@is_auth
def get_all_requests():
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    cursor.execute("select username,request_message,access_key from users where access_key is null or access_key!='rejected';")
    data=cursor.fetchall()
    dataBase.close()
    print(data)
    data_dict=dict()
    for one_row in data:
        for i,column_name in enumerate(cursor.column_names):
            data_dict[column_name]=[one_row[i]] if column_name not in data_dict else data_dict[column_name]+[one_row[i]]

    print(data_dict)
    return jsonify(data_dict)


def get_random_unique_access_key():
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    
    while(True):
        random_access_key=generate_random_id()
        cursor.execute("select username from users where access_key=%s",[random_access_key])
        if cursor.fetchone() is None: break
    dataBase.close()
    return random_access_key


@bp.route("/update_requests/",methods=["POST"])
@is_auth
def update_requests():
    print(request.form)
    dataBase = access_database_as_admin()
    cursor=dataBase.cursor()
    if request.form['mode']=="accept":
        cursor.execute("update users set access_key=%s where username=%s",[get_random_unique_access_key(),request.form['username']])
        create_user_table(request.form['username']) # also add a table for this user

    elif request.form['mode']=="reject":
        cursor.execute("update users set access_key=%s where username=%s",["rejected",request.form['username']])
        drop_user_table(request.form['username'])   # Drop table for this user

    elif request.form['mode']=="revoke":
        cursor.execute("update users set access_key=NULL where username=%s",[request.form['username']])
        
    dataBase.commit()
    dataBase.close()
    return jsonify({"message":"success"})