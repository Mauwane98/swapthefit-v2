from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired

class NotificationSettingsForm(FlaskForm):
    notify_new_message = BooleanField('New Messages')
    notify_listing_update = BooleanField('Updates on My Listings')
    notify_swap_request = BooleanField('New Swap Requests')
    notify_forum_reply = BooleanField('Replies to My Forum Posts/Topics')
    notify_new_follower = BooleanField('New Followers')
    notify_admin_announcement = BooleanField('Admin Announcements')
    submit = SubmitField('Save Preferences')