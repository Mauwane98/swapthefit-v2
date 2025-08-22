# app/blueprints/help/routes.py
from flask import Blueprint, render_template

help_bp = Blueprint('help', __name__)

@help_bp.route("/faq")
def faq():
    """
    Displays the Frequently Asked Questions (FAQ) and Help Center.
    """
    # You can fetch FAQ content from a database, Markdown files, or define it directly here.
    # For simplicity, we'll define some mock FAQ data.
    faq_items = [
        {
            'question': 'How do I list an item for swap, sale, or donation?',
            'answer': 'To list an item, log in to your account and navigate to "My Listings" from the top navigation bar. Click on the "Create New Listing" button and fill in all the required details about your item, including its type (swap, sale, or donation), condition, size, and an image.'
        },
        {
            'question': 'What is the difference between a swap, sale, and donation?',
            'answer': 'A **swap** allows you to exchange your item for another user\'s item. A **sale** means you are selling your item for a specified price. A **donation** allows you to give your item away for free, typically to a school or NGO.'
        },
        {
            'question': 'How does the messaging system work?',
            'answer': 'Our messaging system allows you to communicate directly with other users interested in your listings or whose listings you are interested in. You can access your inbox from the top navigation bar to view and manage all your conversations.'
        },
        {
            'question': 'How do I report a user or a listing?',
            'answer': 'If you encounter inappropriate content, fraudulent listings, or abusive user behavior, you can report them directly from the listing\'s detail page or the user\'s profile page. Look for the "Report Listing" or "Report User" button. Your reports are reviewed by our administrators.'
        },
        {
            'question': 'What is the dispute resolution system?',
            'answer': 'The dispute resolution system provides a formal process to address issues that may arise during a transaction. If you have a problem with a swap, sale, or donation, you can raise a dispute from the relevant transaction details or the other user\'s profile. Our admin team will investigate and help resolve the issue.'
        },
        {
            'question': 'How do premium listings work?',
            'answer': 'Premium listings receive higher visibility on the marketplace, appearing at the top of search results and category pages. You can purchase premium status for your listings from your dashboard or the listing\'s detail page for a small fee, for a specified duration.'
        },
        {
            'question': 'How do I track my donated items as an NGO?',
            'answer': 'As a registered NGO, your dashboard provides an "Impact Report" section. Here, you can track the total number of items received, their estimated value, and the number of families/individuals supported year-to-date. You can also confirm receipt and mark items as distributed from your "Manage Donations" section.'
        },
        {
            'question': 'Is my personal information safe?',
            'answer': 'We prioritize your privacy and security. All personal data is encrypted and stored securely. We do not share your information with third parties without your consent. For more details, please refer to our Privacy Policy.'
        }
    ]
    return render_template('help/faq.html', title='FAQ & Help Center', faq_items=faq_items)

