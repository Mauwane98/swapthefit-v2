from flask_mail import Message
from app.extensions import mail
from flask import current_app, render_template
from threading import Thread # For asynchronous email sending

def send_async_email(app, msg):
    """
    Helper function to send email asynchronously.
    This prevents the web request from being blocked while the email is sent.
    """
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {msg.recipients[0]}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {msg.recipients[0]}: {e}")

def send_password_reset_email(user_email, token):
    """
    Sends a password reset email to the specified user.
    """
    # Create a new Flask application context for sending the email
    # This is necessary because mail.send() requires an active application context.
    app = current_app._get_current_object()
    
    # Retrieve the user object to get username for the template
    # Note: In a real scenario, you might pass the user object directly
    # or fetch minimal user info to avoid unnecessary database queries if not needed.
    from app.models.users import User # Import here to avoid circular dependency
    user = User.objects(email=user_email).first()

    if not user:
        current_app.logger.warning(f"Attempted to send password reset to non-existent user: {user_email}")
        return

    # Construct the email subject
    subject = "SwapTheFit - Reset Your Password"
    
    # Render the HTML and plain text email bodies using Jinja2 templates
    # The _external=True ensures that url_for generates a full URL including domain
    html_body = render_template(
        'emails/password_reset.html',
        user=user,
        token=token
    )
    text_body = render_template(
        'emails/password_reset.txt',
        user=user,
        token=token
    )

    # Create the Flask-Mail Message object
    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user_email]
    )
    msg.body = text_body
    msg.html = html_body

    # Send the email in a separate thread to avoid blocking the main application
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    current_app.logger.info(f"Password reset email queued for {user_email}")


def send_welcome_email(user_email, username):
    """
    Sends a welcome email to a new user after registration.
    """
    app = current_app._get_current_object()
    
    # Retrieve the user object to get username for the template
    # Note: In a real scenario, you might pass the user object directly
    # or fetch minimal user info to avoid unnecessary database queries if not needed.
    from app.models.users import User # Import here to avoid circular dependency
    user = User.objects(email=user_email).first()

    if not user:
        current_app.logger.warning(f"Attempted to send welcome email to non-existent user: {user_email}")
        return

    subject = "Welcome to SwapTheFit!"
    html_body = render_template(
        'emails/welcome.html', # Assuming you'll create an HTML welcome template later
        user=user
    )
    text_body = render_template(
        'emails/welcome_txt',
        user=user
    )

    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user_email]
    )
    msg.body = text_body
    msg.html = html_body # Set HTML body (even if it's just plain text for now)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    current_app.logger.info(f"Welcome email queued for {user_email}")
