from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from app.models.forums import Forum

class CreateTopicForm(FlaskForm):
    forum = SelectField('Forum', coerce=str, validators=[DataRequired()])
    title = StringField('Topic Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Post Content', validators=[DataRequired(), Length(min=10)], render_kw={"class": "richtext-editor"})
    submit = SubmitField('Create Topic')

    def __init__(self, *args, **kwargs):
        super(CreateTopicForm, self).__init__(*args, **kwargs)
        self.forum.choices = [(str(forum.id), forum.name) for forum in Forum.objects.order_by('name')]

class CreatePostForm(FlaskForm):
    content = TextAreaField('Post Content', validators=[DataRequired(), Length(min=10)], render_kw={"class": "richtext-editor"})
    submit = SubmitField('Post Reply')