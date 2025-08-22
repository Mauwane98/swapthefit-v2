from app.services.email_service import send_email
from app.services.sms_service import send_sms
from app.models.users import User # Import User model to get preferences

def send_user_alert(user_id, subject, email_template, sms_message, **kwargs):
    """
    Sends an alert (email or SMS) to a user based on their notification preferences.
    """
    user = User.objects(id=user_id).first()
    if not user:
        return

    # Send Email
    if user.receive_email_notifications and user.email:
        try:
            send_email(user.email, subject, email_template, user=user, **kwargs)
        except Exception as e:
            print(f"Error sending email alert to {user.email}: {e}")

    # Send SMS
    if user.receive_sms_notifications and user.phone_number:
        try:
            send_sms(user.phone_number, sms_message)
        except Exception as e:
            print(f"Error sending SMS alert to {user.phone_number}: {e}")