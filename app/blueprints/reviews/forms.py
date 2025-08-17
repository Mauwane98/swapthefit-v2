from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

class ReviewForm(FlaskForm):
    """
    Form for users to submit a review for another user.
    This form collects a rating and an optional comment.
    """
    rating = SelectField(
        'Rating (1-5 Stars)',
        choices=[
            ('', 'Select Rating'), # Placeholder
            (1, '1 - Poor'),
            (2, '2 - Fair'),
            (3, '3 - Good'),
            (4, '4 - Very Good'),
            (5, '5 - Excellent')
        ],
        validators=[DataRequired(message="Please select a rating.")],
        coerce=int # Ensure the value is cast to an integer
    )
    comment = TextAreaField(
        'Comment (Optional)',
        validators=[Optional(), Length(max=500, message="Comment cannot exceed 500 characters.")],
        render_kw={"placeholder": "Share your experience with this user (optional)."}
    )
    submit = SubmitField('Submit Review')
