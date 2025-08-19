# app/blueprints/reports/forms.py
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError

class ReportForm(FlaskForm):
    """
    Form for a user to submit a report against a listing or another user.
    """
    # This field will be dynamically set in the route based on what's being reported
    # reported_entity_type = SelectField('Report Type', choices=[('listing', 'Listing'), ('user', 'User')], validators=[DataRequired()])
    
    reported_entity_id = IntegerField('ID of Reported Item/User', validators=[DataRequired(), NumberRange(min=1)],
                                      render_kw={"placeholder": "Enter the ID of the listing or user being reported"})
    
    reason_category = SelectField('Reason Category', choices=[
        ('fraudulent', 'Fraudulent Activity'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('spam', 'Spam / Duplicate'),
        ('harassment', 'Harassment / Abuse'),
        ('misleading_information', 'Misleading Information'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Detailed Description', validators=[DataRequired(), Length(min=50, max=1000)],
                                render_kw={"rows": 6, "placeholder": "Please provide a detailed explanation of why you are reporting this (min 50 characters)."})
    
    submit = SubmitField('Submit Report')

class ResolveReportForm(FlaskForm):
    """
    Form for administrators to resolve or update the status of a report.
    """
    status = SelectField('Report Status', choices=[
        ('pending', 'Pending Review'),
        ('under review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed')
    ], validators=[DataRequired()])
    
    admin_notes = TextAreaField('Admin Notes (Optional)', validators=[Optional(), Length(max=2000)],
                                 render_kw={"rows": 8, "placeholder": "Enter notes about the investigation, actions taken, or reason for dismissal/resolution."})
    
    submit = SubmitField('Update Report')

