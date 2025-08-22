from flask import current_app

def send_sms(to_number, message):
    """
    Placeholder function for sending SMS.
    In a real application, this would integrate with a third-party SMS API (e.g., Twilio).
    """
    if not to_number:
        current_app.logger.warning("Attempted to send SMS to empty number.")
        return False

    try:
        # Simulate SMS sending
        current_app.logger.info(f"SMS sent to {to_number}: {message}")
        # In a real app:
        # client = TwilioClient(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
        # message = client.messages.create(
        #     to=to_number,
        #     from_=current_app.config['TWILIO_PHONE_NUMBER'],
        #     body=message
        # )
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send SMS to {to_number}: {e}")
        return False