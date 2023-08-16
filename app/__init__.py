from flask import Flask,session,render_template,url_for,json
from datetime import timedelta

from face_detection import inference as fd
from face_detection.helper import get_crops as fd_get_crops
from face_recognition import inference as fr
from face_recognition.aligner import Aligner
from face_recognition import helper as fr_helper



face_detector=fd.face_detection("face_detection/Models/v1")
# face_detector=fd.face_detection("face_detection/Models/mobilenet")
# face_detector=fd.face_detection("face_detection/Models/BestMap")
face_detector.square_preprocessing=fd.square_pad()
# face_recognizer=fr.face_recognition("face_recognition/Models/v1")
# face_recognizer=fr.face_recognition("face_recognition/Models/mobilenet_basic_lfw")
face_recognizer=fr.face_recognition("face_recognition/Models/keras_mobilenet_emore_adamw")
aligner_obj=Aligner()

# image_size=544
# p_thres=0.7
# nms_thres=0.3
# batch_size=1
# face_detector.set_mode(p_thres,nms_thres,mode="sized",image_size=image_size,batch_size=batch_size)
face_detector.mode="sized"


# def create_app(config_class=Config):
def create_app():
    app=Flask(__name__)
    # app.config.from_object(config_class)
    # app.permanent_session_lifetime = timedelta(seconds=5)

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.demo import bp as demo_bp
    app.register_blueprint(demo_bp,url_prefix="/demo")

    from app.user import bp as user_bp
    app.register_blueprint(user_bp,url_prefix='/user')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp,url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp,url_prefix='/api')

    app.secret_key='asdasr34r'

    @app.route("/test/")
    def test_page():
        return "<h1>This is a test page</h1>"
    
    @app.route("/api/docs/json/",methods=["GET"])
    def get_docs_json():
        return json.load(open("app/static/docs/data.json","r"))

    @app.route("/api/docs/")
    def api_docs():
        return render_template("docs/index.html")

    return app