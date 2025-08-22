# app/blueprints/wishlist/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class SavedSearchForm(FlaskForm):
    """
    Form for users to name and save a search query.
    """
    name = StringField('Search Name', validators=[DataRequired(), Length(min=2, max=100)],
                       render_kw={"placeholder": "e.g., 'Blue School Uniforms for Boys'"})
    submit = SubmitField('Save Search')

class RemoveFromWishlistForm(FlaskForm):
    """
    A simple form for removing an item from the wishlist.
    """
    submit = SubmitField('Remove from Wishlist')

class DeleteSavedSearchForm(FlaskForm):
    """
    A simple form for deleting a saved search.
    """
    submit = SubmitField('Delete Search')
