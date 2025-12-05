from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import get_db_connection
from .non_crud_lib.settlement import calculate_settlement

routes = Blueprint("routes", __name__)
