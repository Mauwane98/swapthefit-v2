# app/blueprints/disputes/forms.py
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class RaiseDisputeForm(FlaskForm):
    """
    Form for a user to raise a new dispute.
    """
    respondent_id = IntegerField('User ID of the Other Party', validators=[DataRequired(), NumberRange(min=1)],
                                 render_kw={"placeholder": "e.g., 123 (User ID of the person you have a dispute with)"})
    listing_id = IntegerField('Listing ID (Optional)', validators=[Optional(), NumberRange(min=1)],
                              render_kw={"placeholder": "e.g., 456 (If dispute is related to a specific listing)"})
    reason = TextAreaField('Reason for Dispute', validators=[DataRequired(), Length(min=50, max=1000)],
                           render_kw={"rows": 6, "placeholder": "Please provide a detailed explanation of the issue (min 50 characters)."})
    submit = SubmitField('Submit Dispute')

class ResolveDisputeForm(FlaskForm):
    """
    Form for administrators to resolve or update the status of a dispute.
    """
    status = SelectField('Dispute Status', choices=[
        ('open', 'Open'),
        ('under review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], validators=[DataRequired()])
    resolution_notes = TextAreaField('Resolution Notes (Optional)', validators=[Optional(), Length(max=2000)],
                                     render_kw={"rows": 8, "placeholder": "Enter details about the resolution, steps taken, or outcome."})
    submit = SubmitField('Update Dispute')

