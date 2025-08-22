from flask_mail import Mail, Message
from flask import current_app, render_template

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_email(to, subject, template, **kwargs):
    """
    Sends an email to the specified recipient.

    Args:
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        template (str): The name of the HTML template to render for the email body.
        **kwargs: Additional keyword arguments to pass to the template.
    """
    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to]
    )
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
        print(f"Email sent to {to} with subject: {subject}")
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")
