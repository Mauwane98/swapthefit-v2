from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=500)])
    receiver_id = HiddenField()
    swap_request_id = HiddenField()
    order_id = HiddenField()
    donation_id = HiddenField()