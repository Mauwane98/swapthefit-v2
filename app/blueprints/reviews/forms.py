# app/blueprints/reviews/forms.py
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ReviewForm(FlaskForm):
    """
    Form for submitting a comprehensive review for another user after a transaction.
    Includes details about the transaction, communication, item accuracy, and logistics.
    """
    # The user being reviewed is typically passed via the route or hidden field
    # reviewed_user_id = IntegerField('Reviewed User ID', validators=[DataRequired()])

    # Link to the specific transaction this review is for (e.g., Swap ID, Order ID, Donation ID)
    # This is crucial for verifying reviews and associating them with concrete events.
    transaction_id = IntegerField('Transaction ID', validators=[DataRequired(), NumberRange(min=1)],
                                  render_kw={"placeholder": "e.g., 123 (ID of the completed swap, sale, or donation)"})
    
    # Overall rating for the user (e.g., 1 to 5 stars)
    rating = IntegerField('Overall Rating (1-5 Stars)', validators=[DataRequired(), NumberRange(min=1, max=5, message="Rating must be between 1 and 5.")],
                          render_kw={"placeholder": "e.g., 5"})
    
    # Specific rating for communication experience
    communication_rating = IntegerField('Communication Rating (1-5 Stars)', validators=[DataRequired(), NumberRange(min=1, max=5, message="Communication rating must be between 1 and 5.")],
                                        render_kw={"placeholder": "e.g., 4"})

    # Specific rating for logistics/pickup/delivery experience
    logistics_rating = IntegerField('Logistics/Pickup Rating (1-5 Stars)', validators=[DataRequired(), NumberRange(min=1, max=5, message="Logistics rating must be between 1 and 5.")],
                                    render_kw={"placeholder": "e.g., 5"})

    # Boolean field to confirm if the item received was as described
    item_as_described = BooleanField('Item was as described?', validators=[Optional()])

    # Detailed comment about the experience
    comment = TextAreaField('Your Detailed Review', validators=[DataRequired(), Length(min=20, max=1000)],
                            render_kw={"rows": 7, "placeholder": "Share your detailed experience with this user, focusing on communication, item accuracy, and overall transaction."})
    
    submit = SubmitField('Submit Review')
