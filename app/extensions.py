from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_login import LoginManager
from flask_moment import Moment

# Instantiate extensions
mongo = PyMongo()
jwt = JWTManager()
mail = Mail()
login_manager = LoginManager()
moment = Moment()
