import os
import io
import base64
import uuid
from PIL import Image
import mysql.connector

def generate_random_id():
    return  str(uuid.uuid1())

def image_to_base64(img):
        img=Image.fromarray(img[:,:,:3])
        rawBytes=io.BytesIO()
        img.save(rawBytes,"JPEG")
        rawBytes.seek(0)
        img_base64=base64.b64encode(rawBytes.read()).decode()
        return img_base64

def base64_to_image(img_base64):
        # Assuming base64_str is the string value without 'data:image/jpeg;base64,'
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))
        return np.array(img)

def access_database_as_admin():
    
    return mysql.connector.connect(host="bnadwttldj2i5cq9aymp-mysql.services.clever-cloud.com",
    user="uvfqvcypihhznd2u",
    port=3306,
    password=os.environ["mysql_password"],
    database="bnadwttldj2i5cq9aymp")


def create_user_table(username):
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    query=f"""create table if not exists user_{username}(
            person_id varchar(30) unique not null,
            face_vectors blob not null,
            remarks text not null,
            group_id char(30)
            );"""
    cursor.execute(query)
    dataBase.commit()
    dataBase.close()

def drop_user_table(username):
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    query=f"drop table if exists user_{username};"
    cursor.execute(query)
    dataBase.commit()
    dataBase.close()

def add_row_user_table(username,person_id,face_vectors,remarks,group_id=None):
    """
        person_id:str
        face_vectors:np.array shape:(n,128)
        remarks:np.array shape:(n,)
        group_id:str

    """

    # print(face_vectors.tobytes())
    # print(remarks.tobytes())
    # print(np.frombuffer(remarks.tobytes(), dtype="float64"))
    # pass
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    cursor.execute(f"select person_id from user_{username} where person_id=%s;",[person_id])
    if cursor.fetchone() is None:
        if group_id is not None:
            query=f"insert into user_{username}(person_id,face_vectors,remarks,group_id) values(%s,%s,%s,%s);"
            cursor.execute(query,[person_id,face_vectors.tobytes(),remarks,group_id])
        else:
            query=f"insert into user_{username}(person_id,face_vectors,remarks) values(%s,%s,%s);"
            cursor.execute(query,[person_id,face_vectors.tobytes(),remarks])
    else:
        if group_id is not None:
            query=f"update  user_{username} SET face_vectors=%s,remarks=%s,group_id=%s where person_id=%s;"
            cursor.execute(query,[face_vectors.tobytes(),remarks,group_id,person_id])
        else:
            query=f"update  user_{username} SET face_vectors=%s,remarks=%s where person_id=%s;"
            cursor.execute(query,[face_vectors.tobytes(),remarks,person_id])
    dataBase.commit()
    dataBase.close()

def read_row_user_table(username):
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    query=f"select person_id,face_vectors,remarks,group_id from user_{username};"
    cursor.execute(query)
    data=list(cursor.fetchone())
    data[1]=np.frombuffer(data[1],dtype="float64")
    
    data[2]=data[2].split(",")
    data[1]=data[1].reshape(len(data[2]),-1)
    print(data)
    # dataBase.commit()
    dataBase.close()

def read_user_table(username,split_remarks=True,group_id=None):
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    if group_id is None:
        cursor.execute(f"select person_id,face_vectors,remarks,group_id from user_{username};")
    else:
        cursor.execute(f"select person_id,face_vectors,remarks,group_id from user_{username} where group_id=%s;",[group_id])
    data={column_name:[] for column_name in cursor.column_names}
    for row in cursor.fetchall():
        row=list(row)
        row[1]=np.frombuffer(row[1],dtype="float64")
        row[2]=row[2].split(",")

        data['person_id'].append(row[0])
        data['face_vectors'].append(row[1].reshape(len(row[2]),-1))
        if not split_remarks:
            row[2]=",".join(row[2])
        data['remarks'].append(row[2])
        data['group_id'].append(row[3])
        
    dataBase.close()
    # print(data['person_id'])
    # print(data['face_vectors'])
    return data

def remove_person_from_user_table(username,person_id):
    dataBase=access_database_as_admin()
    cursor=dataBase.cursor()
    query=f"delete from user_{username} where person_id=%s;"
    cursor.execute(query,[person_id])
    dataBase.commit()
    dataBase.close()

import numpy as np 

# add_row_user_table("abc","1",np.array([[2,3],[1,4]],dtype="float64"),"front face,left face,right face",group_id="1")
# read_user_table("abc")
# print(np.fromstring("a,b,c",dtype='S3'))

# drop_user_table("abc")
# create_user_table("abc")