import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """Fetches environmental variables from secure .env file"""

    #Secret key used for hashing
    SECRET_KEY = os.environ.get('SECRET_KEY')

    #Allows app to interact with db without exposing engine connection information
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #Pagination variable
    POSTS_PER_PAGE = 3

    #MAIL SERVER INFO
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['nybarhopper@gmail.com', 'shanedroogan@gmail.com']


    #GOOGLE MAPS API KEY
    GEO_KEY = os.environ.get('GEO_KEY')
