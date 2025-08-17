from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.users import User
from app.models.messages import Message
from app.models.notifications import Notification # Import Notification model
from app.extensions import mongo
from bson.objectid import ObjectId

messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging')

@messaging_bp.route('/inbox')
@login_required
def inbox():
    """
    Displays the user's inbox with all conversations.
    """
    pipeline = [
        {
            '$match': {
                '$or': [
                    {'sender_id': current_user.id},
                    {'recipient_id': current_user.id}
                ]
            }
        },
        {
            '$sort': {'timestamp': -1}
        },
        {
            '$group': {
                '_id': '$conversation_id',
                'latest_message': {'$first': '$$ROOT'}
            }
        },
        {
            '$replaceRoot': {'newRoot': '$latest_message'}
        },
        {
            '$sort': {'timestamp': -1}
        }
    ]
    latest_messages = list(mongo.db.messages.aggregate(pipeline))

    for message in latest_messages:
        if message['sender_id'] == current_user.id:
            other_user_id = message['recipient_id']
        else:
            other_user_id = message['sender_id']
        other_user = User.get(other_user_id)
        message['other_user'] = other_user

    return render_template('messaging/inbox.html', latest_messages=latest_messages)


@messaging_bp.route('/conversation/<conversation_id>')
@login_required
def conversation(conversation_id):
    """
    Displays a specific conversation thread.
    """
    messages = list(mongo.db.messages.find({'conversation_id': conversation_id}).sort('timestamp', 1))
    
    if not messages or (current_user.id not in [messages[0]['sender_id'], messages[0]['recipient_id']]):
        flash('Conversation not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('messaging.inbox'))

    if messages[0]['sender_id'] != current_user.id:
        other_user = User.get(messages[0]['sender_id'])
    else:
        other_user = User.get(messages[0]['recipient_id'])
    
    return render_template('messaging/conversation.html', messages=messages, other_user=other_user, conversation_id=conversation_id)


@messaging_bp.route('/send/<recipient_id>', methods=['GET', 'POST'])
@login_required
def send_message(recipient_id):
    """
    Handles sending a new message to a user, potentially about a listing.
    """
    recipient = User.get(recipient_id)
    listing_id = request.args.get('listing_id')
    listing = mongo.db.listings.find_one({'_id': ObjectId(listing_id)}) if listing_id else None

    if request.method == 'POST':
        body = request.form.get('body')
        if not body:
            flash('Message body cannot be empty.', 'warning')
            return redirect(request.url)

        # Determine the conversation ID
        user_ids = sorted([current_user.id, recipient_id])
        conversation_id = f"{user_ids[0]}_{user_ids[1]}"
        if listing_id:
            conversation_id += f"_listing_{listing_id}"

        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            body=body,
            conversation_id=conversation_id,
            listing_id=listing_id
        )
        message.save()
        
        # Create a notification for the recipient
        notification = Notification(
            user_id=recipient_id,
            message=f"You have a new message from {current_user.username}.",
            link=url_for('messaging.conversation', conversation_id=conversation_id, _external=True)
        )
        notification.save()

        flash('Your message has been sent.', 'success')
        return redirect(url_for('messaging.conversation', conversation_id=conversation_id))

    # For GET request, find existing conversation
    user_ids = sorted([current_user.id, recipient_id])
    conversation_id = f"{user_ids[0]}_{user_ids[1]}"
    if listing_id:
        conversation_id += f"_listing_{listing_id}"
        
    messages = list(mongo.db.messages.find({'conversation_id': conversation_id}).sort('timestamp', 1))

    return render_template('messaging/send_message.html', recipient=recipient, listing=listing, messages=messages)