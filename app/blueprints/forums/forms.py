from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class CreateTopicForm(FlaskForm):
    title = StringField('Topic Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Post Content', validators=[DataRequired(), Length(min=10)], render_kw={"class": "richtext-editor"})
    submit = SubmitField('Create Topic')

class CreatePostForm(FlaskForm):
    content = TextAreaField('Post Content', validators=[DataRequired(), Length(min=10)], render_kw={"class": "richtext-editor"})
    submit = SubmitField('Post Reply')