from flask import redirect
from app.main import bp


@bp.route("/")
def index():
  # return "<h1>This is the home page of face rec api</h1>"
  return redirect("/demo/")
