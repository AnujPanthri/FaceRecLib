import os
import mysql.connector
from werkzeug.security import generate_password_hash,check_password_hash


dataBase = mysql.connector.connect(
    host="bnadwttldj2i5cq9aymp-mysql.services.clever-cloud.com",
    user="uvfqvcypihhznd2u",
    port=3306,
    password=os.environ["mysql_password"],
    database="bnadwttldj2i5cq9aymp"
)

# preparing a cursor object
cursorObject = dataBase.cursor()

##################################################################################################################
cursorObject.execute("SELECT table_name FROM information_schema.TABLES WHERE table_schema = SCHEMA();")  
table_names=cursorObject.fetchall()
for table_name in table_names:
    print("Deleting table :",table_name[0])
    cursorObject.execute(f"drop table {table_name[0]}")  
##################################################################################################################


cursorObject.execute("""create table if not exists admins(
    username varchar(30) unique not null,
    password char(150) not null,
    session_token char(40) unique
    );
""")
cursorObject.execute("""create table if not exists users(
    username varchar(30) unique not null,
    password char(150) not null,
    request_message text not null,
    access_key char(50)
    );
""")

cursorObject.execute("""create table if not exists session_table(
    username varchar(30) not null,
    session_token char(40) unique  not null,
    expiring_time timestamp  not null
    );
""")

cursorObject.execute("""drop table if exists default_settings""")
cursorObject.execute("""create table if not exists default_settings(
    page varchar(30) not null unique,
    p_thres float not null,
    nms_thres float not null,
    small_size integer not null default 544,
    large_size integer not null default 2080,
    d_thres float not null,
    a_thres float not null,
    db_mode enum('small','large','both') not null,
    fr_mode enum('small','large','both') not null
    );
""")

cursorObject.execute("""insert into default_settings(page,p_thres,nms_thres,small_size,large_size,d_thres,a_thres,db_mode,fr_mode) values(
                'demo',0.5,0.3,256,1024,0.5,0.6,'small','large');""")

cursorObject.execute("""insert into default_settings(page,p_thres,nms_thres,small_size,large_size,d_thres,a_thres,db_mode,fr_mode) values(
                'user',0.7,0.3,544,2080,0.5,0.6,'small','both');""")


# cursorObject.execute("""drop table if exists user_settings""")
cursorObject.execute("""create table if not exists user_settings(
    username varchar(30) unique not null,
    p_thres float not null,
    nms_thres float not null,
    small_size integer not null,
    large_size integer not null,
    d_thres float not null,
    a_thres float not null,
    db_mode enum('small','large','both') not null,
    fr_mode enum('small','large','both') not null
    );
""")


user_name='anuj'
password='123'
password_hash=generate_password_hash(password)
print("password:",password)
print("password_hash:",password_hash)
# print(check_password_hash(password_hash,password))
cursorObject.execute("insert into admins(username,password) values(%s,%s)",(user_name,password_hash))

cursorObject.execute("SELECT password FROM admins where username=%s",(user_name,))
my_hashed_password = cursorObject.fetchall()[0][0]
print(check_password_hash(my_hashed_password,password))
 
# Disconnecting from the server
dataBase.commit()
dataBase.close()