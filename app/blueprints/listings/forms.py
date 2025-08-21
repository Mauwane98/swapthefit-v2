# app/blueprints/listings/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

class ListingForm(FlaskForm):
    """
    Form for creating and editing product listings.
    Includes fields for various item attributes and validation.
    """
    def __init__(self, *args, **kwargs):
        self.current_step = kwargs.pop('current_step', 1)
        super(ListingForm, self).__init__(*args, **kwargs)

    # Step 1: Basic Details
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20, max=1000)])
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

    # Step 2: Images
    images = MultipleFileField('Upload Images', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])

    # Step 3: Pricing & Type
    price = FloatField('Price (ZAR)', validators=[Optional(), NumberRange(min=0.01)],
                       render_kw={"placeholder": "Enter price if for sale"})
    listing_type = SelectField('Listing Type', choices=[
        ('sale', 'For Sale'),
        ('swap', 'For Swap'),
        ('donation', 'For Donation')
    ], validators=[DataRequired()], default='sale')
    brand = StringField('Brand (Optional)', validators=[Length(max=50)])
    color = StringField('Color (Optional)', validators=[Length(max=50)])
    is_premium = BooleanField('Premium Listing')

    submit = SubmitField('Next') # Changed to 'Next' for multi-step
    post_listing_submit = SubmitField('Post Listing') # New submit button for final step

    def validate_on_submit(self, extra_validators=None):
        # Custom validation for each step
        if self.current_step == 1:
            return super().validate_on_submit()
        elif self.current_step == 2:
            # Images are optional, so no DataRequired for this step
            return super().validate_on_submit()
        elif self.current_step == 3:
            # Validate price based on listing_type
            if self.listing_type.data == 'sale' and not self.price.data:
                self.price.errors.append('Price is required for sale listings.')
            
            # Call super().validate_on_submit after custom validation
            return super().validate_on_submit()
        return super().validate_on_submit()

class BulkUploadForm(FlaskForm):
    """
    Form for uploading a CSV file for bulk listing creation.
    """
    csv_file = FileField('CSV File', validators=[DataRequired(), FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Upload Listings')