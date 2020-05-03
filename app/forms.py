from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, InputRequired, Email, EqualTo
from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from datetime import datetime

# WTForms allows us to use easy to implement server-side form validation
# Each variable in class declaration pertains to a unique field or submit button in form
# validator assignment allows us to put restrictions on user input


class CustomizePreferences(FlaskForm):
    date = DateField(default=datetime.now(), validators=[InputRequired()])
    address = StringField('Starting Address', validators=[InputRequired()])
    submit = SubmitField('Get Hoppin!')


class LoginForm(FlaskForm):
    username = StringField('Username', validators = [InputRequired()])
    password = PasswordField('Password', validators = [InputRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[Email(message="Must be a valid email."), InputRequired(message="This field is required.")])
    password = PasswordField('Password', validators=[InputRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    #Support functions for registering user if username or email already taken
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    submit = SubmitField('Request Password Reset')
