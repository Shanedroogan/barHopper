from flask_mail import Message
from app import mail
from flask import render_template
from app import app
from threading import Thread

# SOURCE Miguel Grinberg method for sending emails asynchronously, so that
# site does not slow down on request

def send_email(subject, sender, recipients, text_body, html_body):
    """
    Populates email template with relevant information to reset password,
    calls the asynchronous send function
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    """Generates secure token and calls send_email function"""
    token = user.get_reset_password_token()
    send_email('[BarHopper] Reset Your Password',
                sender=app.config['ADMINS'][0],
                recipients=[user.email],
                text_body=render_template('email/reset_password.txt',
                                           user=user, token=token),
                html_body=render_template('email/reset_password.html',
                                           user=user, token=token))


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
