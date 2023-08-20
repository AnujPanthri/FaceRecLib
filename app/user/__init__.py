from flask import Blueprint
from datetime import timedelta

bp = Blueprint("user", __name__)
session_expiring_time = timedelta(minutes=45)
settings = dict()

from app.user import routes
