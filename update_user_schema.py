# update_user_schema.py
from app import create_app
from app.models.users import User
from app.extensions import db

app = create_app()

with app.app_context():
    print("Starting user schema update...")
    users = User.objects()
    updated_count = 0
    for user in users:
        # Check if the fields exist, if not, add them with default values
        if not hasattr(user, 'show_my_listings_on_dashboard'):
            user.show_my_listings_on_dashboard = True
        if not hasattr(user, 'show_swap_activity_on_dashboard'):
            user.show_swap_activity_on_dashboard = True
        if not hasattr(user, 'show_account_summary_on_dashboard'):
            user.show_account_summary_on_dashboard = True
        if not hasattr(user, 'show_activity_feed_on_dashboard'):
            user.show_activity_feed_on_dashboard = True
        
        # Also ensure phone_number and email/sms notification preferences are set
        if not hasattr(user, 'phone_number'):
            user.phone_number = None
        if not hasattr(user, 'receive_email_notifications'):
            user.receive_email_notifications = True
        if not hasattr(user, 'receive_sms_notifications'):
            user.receive_sms_notifications = False

        try:
            user.save()
            updated_count += 1
        except Exception as e:
            print(f"Error updating user {user.id}: {e}")
    print(f"Finished user schema update. Updated {updated_count} users.")