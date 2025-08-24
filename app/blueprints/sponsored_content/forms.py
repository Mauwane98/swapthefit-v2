from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Length, URL, Optional
from flask_wtf.file import FileField, FileAllowed

class SponsoredContentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(max=500)])
    image_url = StringField('Image URL (Optional)', validators=[Optional(), URL()])
    # Alternatively, if we want to allow file uploads:
    # image_file = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    target_url = StringField('Target URL', validators=[DataRequired(), URL()])
    start_date = DateTimeField('Start Date (YYYY-MM-DD HH:MM:SS)', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    end_date = DateTimeField('End Date (YYYY-MM-DD HH:MM:SS)', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    is_active = BooleanField('Is Active', default=True)
    submit = SubmitField('Save Sponsored Content')