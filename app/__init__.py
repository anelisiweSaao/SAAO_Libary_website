from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
import os

''' This file creates application object of Flask and initializes the applications 
and also brings together all the various components of an application'''

app = Flask(__name__)
Bootstrap(app)
app.debug=True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.config.from_object('config')
#app.config['TESTING'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

dirpath=os.getcwd()
UPLOAD_FOLDER = dirpath
ALLOWED_EXTENSIONS = set(['txt'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


'''import views which contains  handlers that responds to requests from the web browsers.It is imported here at the 
end to avoid circular import error'''
from app import views
