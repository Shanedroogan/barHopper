from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

#app declarations for integrating flask libraries
app = Flask(__name__)

#Config class from Config.py assigned to app.config attribute
app.config.from_object(Config)

#Allows app to interact with db through SQLAlchemy ORM
db = SQLAlchemy(app)

#reflect existing table metadata from db tables made outside of app context
db.Model.metadata.reflect(db.engine)

#migration engine used to add source control to database versions
migrate = Migrate(app, db)

#flask-login manages user login functionality
login = LoginManager(app)
login.login_view = 'login'

#flask-mail handles app to email_server interaction
mail = Mail(app)

#Moment used to time localization for users
moment = Moment(app)

#If in production mode, send emails to admin when errors happen
#Not necessary for class but it's nice to have in a real environment
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Test Failure',
            credentials=auth,secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    #write logs information for bug tracing
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/test.log', maxBytes = 10240,
                                        backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Test startup')

#circular import needed for current app architecture
from app import routes, models, errors, utils
