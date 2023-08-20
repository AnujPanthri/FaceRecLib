from flask import Blueprint

bp = Blueprint("demo", __name__)

from app.demo import routes
