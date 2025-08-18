from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, MultipleFileField, FloatField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from flask_wtf.file import FileAllowed # Removed FileRequired for MultipleFileField

class ListingForm(FlaskForm):
    """
    Form for creating a new clothing item listing.
    This form collects all necessary details for a listing, including photos.
    """
    title = StringField(
        'Listing Title',
        validators=[DataRequired(), Length(min=5, max=150)],
        render_kw={"placeholder": "e.g., Boys Grey School Trousers"}
    )
    description = TextAreaField(
        'Description',
        validators=[DataRequired(), Length(min=20, max=1000)],
        render_kw={"placeholder": "Provide a detailed description of the item, including any wear or features."}
    )
    category = SelectField(
        'Category',
        choices=[
            ('', 'Select Category'), # Placeholder for better UX
            ('School Uniform', 'School Uniform'),
            ('Shoes', 'Shoes'),
            ('Bags', 'Bags'),
            ('Sports Gear', 'Sports Gear'),
            ('Books', 'Books'),
            ('Other Kids Gear', 'Other Kids Gear')
        ],
        validators=[DataRequired(message="Please select a category.")]
    )
    school_name = StringField(
        'School Name (Optional)',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., Springfield Primary School (if uniform specific)"}
    )
    size = StringField(
        'Size',
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "e.g., Age 7-8, Size 30, UK 12 (for shoes)"}
    )
    condition = SelectField(
        'Condition',
        choices=[
            ('', 'Select Condition'), # Placeholder
            ('New with tags', 'New with tags'),
            ('Like new', 'Like new'),
            ('Good', 'Good'),
            ('Fair', 'Fair'),
            ('Used - Acceptable', 'Used - Acceptable')
        ],
        validators=[DataRequired(message="Please select the item's condition.")]
    )
    listing_type = SelectField(
        'Listing Type',
        choices=[
            ('swap', 'Swap Item'),
            ('sale', 'Sell Item'),
            ('donation', 'Donate Item')
        ],
        validators=[DataRequired(message="Please select a listing type.")]
    )
    price = FloatField(
        'Price (ZAR)',
        validators=[Optional(), NumberRange(min=0.01, message="Price must be a positive number.")],
        render_kw={"placeholder": "Enter price if selling (e.g., 150.00)"}
    )
    is_premium = BooleanField(
        'Premium Listing (get more visibility)'
    )
    # Using MultipleFileField to allow multiple photo uploads
    photos = MultipleFileField(
        'Upload Photos (Max 5)',
        validators=[
            FileAllowed(['jpg', 'png', 'jpeg'], 'Images only! Allowed formats: JPG, PNG, JPEG.'),
            Optional() # Make photos optional for now, can be required in routes if needed
        ],
        render_kw={"multiple": True} # Enable multiple file selection in HTML
    )
    desired_swap_items = TextAreaField(
        'Desired Swap Items (Optional, if swapping)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "e.g., Looking for a size 10 school blazer, or open to offers."}
    )
    submit = SubmitField('Create Listing')

    def validate_price(self, field):
        """
        Custom validator for price field.
        Price is required if listing_type is 'sale'.
        """
        if self.listing_type.data == 'sale' and not field.data:
            raise ValidationError('Price is required for sale listings.')
        if self.listing_type.data != 'sale' and field.data is not None:
             # If it's not a sale, ensure price is not set
            field.data = None


class EditListingForm(FlaskForm):
    """
    Form for editing an existing clothing item listing.
    Similar to ListingForm but with optional photo uploads for updates.
    """
    title = StringField(
        'Listing Title',
        validators=[DataRequired(), Length(min=5, max=150)],
        render_kw={"placeholder": "e.g., Boys Grey School Trousers"}
    )
    description = TextAreaField(
        'Description',
        validators=[DataRequired(), Length(min=20, max=1000)],
        render_kw={"placeholder": "Provide a detailed description of the item, including any wear or features."}
    )
    category = SelectField(
        'Category',
        choices=[
            ('', 'Select Category'),
            ('School Uniform', 'School Uniform'),
            ('Shoes', 'Shoes'),
            ('Bags', 'Bags'),
            ('Sports Gear', 'Sports Gear'),
            ('Books', 'Books'),
            ('Other Kids Gear', 'Other Kids Gear')
        ],
        validators=[DataRequired(message="Please select a category.")]
    )
    school_name = StringField(
        'School Name (Optional)',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., Springfield Primary School (if uniform specific)"}
    )
    size = StringField(
        'Size',
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "e.g., Age 7-8, Size 30, UK 12 (for shoes)"}
    )
    condition = SelectField(
        'Condition',
        choices=[
            ('', 'Select Condition'),
            ('New with tags', 'New with tags'),
            ('Like new', 'Like new'),
            ('Good', 'Good'),
            ('Fair', 'Fair'),
            ('Used - Acceptable', 'Used - Acceptable')
        ],
        validators=[DataRequired(message="Please select the item's condition.")]
    )
    listing_type = SelectField(
        'Listing Type',
        choices=[
            ('swap', 'Swap Item'),
            ('sale', 'Sell Item'),
            ('donation', 'Donate Item')
        ],
        validators=[DataRequired(message="Please select a listing type.")]
    )
    price = FloatField(
        'Price (ZAR)',
        validators=[Optional(), NumberRange(min=0.01, message="Price must be a positive number.")],
        render_kw={"placeholder": "Enter price if selling (e.g., 150.00)"}
    )
    is_premium = BooleanField(
        'Premium Listing (get more visibility)'
    )
    # Photos are optional when editing, as existing photos might be kept
    photos = MultipleFileField(
        'Upload New Photos (Optional, replaces existing)',
        validators=[
            FileAllowed(['jpg', 'png', 'jpeg'], 'Images only! Allowed formats: JPG, PNG, JPEG.'),
            Optional()
        ],
        render_kw={"multiple": True}
    )
    desired_swap_items = TextAreaField(
        'Desired Swap Items (Optional, if swapping)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "e.g., Looking for a size 10 school blazer, or open to offers."}
    )
    submit = SubmitField('Update Listing')

    def validate_price(self, field):
        """
        Custom validator for price field.
        Price is required if listing_type is 'sale'.
        """
        if self.listing_type.data == 'sale' and not field.data:
            raise ValidationError('Price is required for sale listings.')
        if self.listing_type.data != 'sale' and field.data is not None:
            field.data = None
