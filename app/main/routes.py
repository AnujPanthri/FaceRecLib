from flask import redirect
from app.main import bp

@bp.route("/")
def index():
    return redirect("/demo/")