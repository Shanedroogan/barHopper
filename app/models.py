from datetime import datetime
from app import app, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt

#password generation, storage, and recovery based on Miguel Grinberg's flask implementation
class User(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    crawls = db.relationship('Crawl', backref='author', lazy = 'dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
        {'reset_password' : self.id, 'exp' : time() + expires_in},
        app.config['SECRET_KEY'], algorithm="HS256").decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                                algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Bar_MasterList(db.Model):
    __table__ = db.Model.metadata.tables['Bar_MasterList']
    __table_args__ = {'extend_existing': True}
    deals = db.relationship('Deal', backref='bar', lazy='dynamic')
    def __repr__(self):
        return self.name


class Crawl(db.Model):
    __table_args__ = {'extend_existing' : True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    bar_1 = db.Column(db.Integer, db.ForeignKey('Bar_MasterList.bar_id'))
    bar_2 = db.Column(db.Integer, db.ForeignKey('Bar_MasterList.bar_id'))
    bar_3 = db.Column(db.Integer, db.ForeignKey('Bar_MasterList.bar_id'))
    bar_4 = db.Column(db.Integer, db.ForeignKey('Bar_MasterList.bar_id'))
    bar_5 = db.Column(db.Integer, db.ForeignKey('Bar_MasterList.bar_id'))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Crawl {}>'.format(self.body)


class Deal(db.Model):
    __table__ = db.Model.metadata.tables['Deal']
    __table_args__ = {'extend_existing' : True}

    def __repr__(self):
        return self.deal_name


@login.user_loader
def load_user(id):
    return User.query.get(int(id))