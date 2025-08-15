from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
from threading import Thread

def send_async_email(app, msg):
    """Background email sending function."""
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    """
    Sends an email to a recipient.
    Renders a template and sends the email in a background thread.
    """
    app = current_app._get_current_object()
    msg = Message(
        subject,
        recipients=[to],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    msg.body = render_template(template + '.txt', **kwargs)
    # Send email in a background thread to avoid blocking the request
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
