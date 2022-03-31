from flask import Flask, session, jsonify, request
from functools import wraps
from flask_mail import Mail,Message
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import redis##session
from flask_session import Session##session


db = SQLAlchemy()
sess = Session()##need to type redis-server to be able to connect to server, check redis-cli KEYS*
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "VdJeu8dSmW-55Zwk"##hash session data
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
  
    db.init_app(app)
    
    
    app.config.from_pyfile('mailconfig.cfg')
    with app.app_context():
        mail=Mail(app)
    
    app.config['SESSION_TYPE'] = "redis"#session
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True 
    app.config['SESSION_REDIS'] = redis.from_url("redis:///127.0.0.1:6379")# redis-server "D:\redis\redis.windows.conf"

    sess.init_app(app)
    
    from .views import views
    from .auth import auth

    app.register_blueprint(views,url_prefix="/")
    app.register_blueprint(auth,url_prefix="/")
    
    from.models import User,Borroweditem, Inventory
    
    create_database(app)

    ##setup login LoginManager, if user not logged in it redirects them to login page
    login_manager=LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader##uses session to store id of ppl logged in
    def load_user(id):
        return User.query.get(int(id))
   
    return app
##create database and check if it already exists
def create_database(app):
    if not path.exists("website/"+ DB_NAME):##if databse dont exists itll create it
        db.create_all(app=app)##passes the app
        print("Created database!")


