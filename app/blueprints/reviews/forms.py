from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ReviewForm(FlaskForm):
    """
    Form for users to submit a review.
    """
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5, message="Please provide a rating between 1 and 5.")])
    comment = TextAreaField('Comment')
    submit = SubmitField('Submit Review')
