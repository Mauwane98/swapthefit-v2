from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Optional

class ListingForm(FlaskForm):
    """Form for creating a new listing."""
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('uniform', 'School Uniform'),
        ('shoes', 'Shoes'),
        ('accessory', 'Accessory')
    ], validators=[DataRequired()])
    school = StringField('School Name (if applicable)')
    size = StringField('Size', validators=[DataRequired()])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like-new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], validators=[DataRequired()])
    photos = FileField('Upload Photos', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Create Listing')

class EditListingForm(FlaskForm):
    """Form for editing an existing listing."""
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('uniform', 'School Uniform'),
        ('shoes', 'Shoes'),
        ('accessory', 'Accessory')
    ], validators=[DataRequired()])
    school = StringField('School Name (if applicable)')
    size = StringField('Size', validators=[DataRequired()])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like-new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], validators=[DataRequired()])
    photos = FileField('Upload New Photos (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Update Listing')
