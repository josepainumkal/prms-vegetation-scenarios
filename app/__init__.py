"""
VW Platform Application Package Constructor
"""
from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine

from config import config
from flask.ext.session import Session
from flask.ext.security import Security
from flask_sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore
from flask.ext.security.utils import encrypt_password, verify_password
from flask_jwt import JWT

db = MongoEngine()
session = Session()
security = Security()

userdb = SQLAlchemy()

from .models import User, Role
user_datastore = SQLAlchemyUserDatastore(userdb, User, Role)

# enable cross-origin resource sharing for the REST API
cors = CORS(resources={r'/api/*': {'origins': '*'}})


def authenticate(username, password):
    user = user_datastore.find_user(email=username)
    if user and user.confirmed_at and username == user.email and verify_password(password, user.password):
        return user
    return None



def load_user(payload):
    user = user_datastore.find_user(id=payload['identity'])
    return user

jwt = JWT(app=None, authentication_handler=authenticate,
          identity_handler=load_user)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    cors.init_app(app)

    db.init_app(app)
    userdb.init_app(app)
    security.init_app(app,datastore=user_datastore)
    session.init_app(app)
    jwt.init_app(app)
    # not sure why config part does not work
    app.secret_key = 'many random bytes'
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
