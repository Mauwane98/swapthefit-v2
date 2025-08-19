# app/blueprints/listings/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ListingForm(FlaskForm):
    """
    Form for creating and editing product listings.
    Includes fields for various item attributes and validation.
    """
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20, max=1000)])
    
    # Price is optional as it might be a swap/donation
    price = FloatField('Price (ZAR)', validators=[Optional(), NumberRange(min=0.01)],
                       render_kw={"placeholder": "Enter price if for sale"})
    
    # Dropdowns for standardized inputs
    uniform_type = SelectField('Uniform Type', choices=[
        ('School Uniform', 'School Uniform'),
        ('Sports Kit', 'Sports Kit'),
        ('Casual Wear', 'Casual Wear'),
        ('Formal Wear', 'Formal Wear'),
        ('Other', 'Other')
    ], validators=[DataRequired()])

    condition = SelectField('Condition', choices=[
        ('New', 'New'),
        ('Used - Like New', 'Used - Like New'),
        ('Used - Good', 'Used - Good'),
        ('Used - Fair', 'Used - Fair'),
        ('Used - Poor', 'Used - Poor')
    ], validators=[DataRequired()])

    size = SelectField('Size', choices=[
        ('Small', 'Small'), ('Medium', 'Medium'), ('Large', 'Large'),
        ('XS', 'XS'), ('XL', 'XL'), ('XXL', 'XXL'),
        ('Age 2-3', 'Age 2-3'), ('Age 4-5', 'Age 4-5'), ('Age 6-7', 'Age 6-7'),
        ('Age 8-9', 'Age 8-9'), ('Age 10-11', 'Age 10-11'), ('Age 12-13', 'Age 12-13'),
        ('Age 14-15', 'Age 14-15'), ('Age 16+', 'Age 16+')
    ], validators=[DataRequired()])

    gender = SelectField('Gender', choices=[
        ('Unisex', 'Unisex'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ], validators=[DataRequired()])

    school_name = StringField('School Name (Optional)', validators=[Length(max=100)])
    location = StringField('Location (e.g., City, Suburb)', validators=[DataRequired(), Length(max=100)])
    
    listing_type = SelectField('Listing Type', choices=[
        ('sale', 'For Sale'),
        ('swap', 'For Swap'),
        ('donation', 'For Donation')
    ], validators=[DataRequired()])

    # New fields for brand and color
    brand = StringField('Brand (Optional)', validators=[Length(max=50)])
    color = StringField('Color (Optional)', validators=[Length(max=50)])

    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])

    # For premium listings (admin or specific user roles might set this)
    is_premium = BooleanField('Premium Listing')

    submit = SubmitField('Post Listing')
