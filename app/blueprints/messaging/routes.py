from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.users import User
from app.models.messages import Message
from app.models.listings import Listing
from app.models.notifications import Notification
from app.extensions import socketio # Import socketio for emitting events
from datetime import datetime
from mongoengine.queryset.visitor import Q # For OR queries in MongoEngine

messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging', template_folder='templates')

@messaging_bp.route('/inbox')
@login_required
def inbox():
    """
    Displays the user's inbox with all conversations.
    Each conversation is represented by the latest message in that thread,
    grouped by the unique combination of participants and listing.
    """
    # Aggregate to find the latest message for each unique conversation thread
    # A conversation thread is defined by the two participants and the listing they are discussing.
    
    # Step 1: Find all messages where the current user is either sender or recipient
    # Step 2: Sort messages by sent_at in descending order (latest first)
    # Step 3: Group messages by a unique conversation key (listing_id, user1_id, user2_id)
    #         The user IDs are sorted to ensure the key is consistent regardless of who sent the first message.
    # Step 4: For each group, take the first message (which is the latest due to sorting)
    # Step 5: Replace the root with the latest message document
    # Step 6: Sort the resulting latest messages by their timestamp again to show most recent conversations first

    conversations_raw = Message.objects(
        Q(sender=current_user.id) | Q(recipient=current_user.id)
    ).order_by('-sent_at').all()

    # Manually group to find the latest message for each unique conversation thread
    # This is a common pattern when MongoEngine's aggregation framework is not directly used for complex grouping.
    unique_conversations = {} # Key: (listing_id, other_user_id)
    
    for msg in conversations_raw:
        # Determine the 'other' participant in the conversation
        other_user = msg.sender if msg.recipient == current_user else msg.recipient
        
        # Create a unique key for the conversation thread
        # Using sorted IDs ensures consistent key regardless of sender/recipient order
        conversation_key = (str(msg.listing.id), str(other_user.id))

        if conversation_key not in unique_conversations:
            unique_conversations[conversation_key] = {
                'listing': msg.listing,
                'other_user': other_user,
                'latest_message': msg,
                'unread_count': 0 # Initialize unread count
            }
        
        # Count unread messages for the current user in this specific conversation thread
        # This needs to be done separately as the initial grouping only gets the *latest* message.
        if msg.recipient == current_user and not msg.is_read:
            unique_conversations[conversation_key]['unread_count'] += 1

    # Convert dictionary values to a list and sort by latest message timestamp
    conversations = sorted(
        unique_conversations.values(), 
        key=lambda x: x['latest_message'].sent_at, 
        reverse=True
    )
    
    return render_template('messaging/inbox.html', conversations=conversations, user=current_user)

@messaging_bp.route('/conversation/<string:listing_id>/<string:other_user_id>', methods=['GET'])
@login_required
def conversation_api(listing_id, other_user_id):
    """
    API endpoint to fetch messages for a specific conversation thread.
    This is called via AJAX from the inbox.html to load messages dynamically.
    Also marks messages as read when fetched.
    """
    try:
        # Ensure both users are part of this conversation
        messages = Message.objects(
            (Q(sender=current_user.id, recipient=other_user_id) | 
             Q(sender=other_user_id, recipient=current_user.id)),
            listing=listing_id
        ).order_by('sent_at').all() # Order by oldest first for chat history

        # Mark messages received by current_user in this conversation as read
        unread_messages_in_thread = Message.objects(
            recipient=current_user.id,
            sender=other_user_id,
            listing=listing_id,
            is_read=False
        )
        for msg in unread_messages_in_thread:
            msg.is_read = True
            msg.save()
        
        # After marking as read, update the global unread count for the user via SocketIO
        total_unread_count = Notification.objects(recipient=current_user.id, read=False).count()
        socketio.emit('update_notification_count', {'count': total_unread_count}, room=str(current_user.id))

        # Prepare messages for JSON response
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': str(msg.id),
                'sender_id': str(msg.sender.id),
                'sender_username': msg.sender.username, # Include sender's username
                'recipient_id': str(msg.recipient.id),
                'listing_id': str(msg.listing.id),
                'content': msg.content,
                'is_read': msg.is_read,
                'timestamp': msg.sent_at.isoformat() # ISO format for easy JS parsing
            })
        
        return jsonify({'messages': messages_data})

    except Exception as e:
        current_app.logger.error(f"Error fetching conversation {listing_id}/{other_user_id}: {e}")
        return jsonify({'error': 'Could not load conversation.'}), 500

@messaging_bp.route('/send_message/<string:recipient_id>', methods=['GET', 'POST'])
@login_required
def send_message(recipient_id):
    """
    Handles sending a new message to a user, potentially about a specific listing.
    This route is typically hit when initiating a message from a listing detail page.
    """
    recipient = User.objects(id=recipient_id).first()
    if not recipient:
        flash('Recipient user not found.', 'danger')
        return redirect(url_for('listings.marketplace')) # Redirect to a safe place

    listing_id = request.args.get('listing_id')
    listing = None
    if listing_id:
        listing = Listing.objects(id=listing_id).first()
        if not listing:
            flash('Related listing not found.', 'danger')
            return redirect(url_for('listings.marketplace'))

    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Message content cannot be empty.', 'warning')
            # Redirect back to the inbox or listing detail if no content
            return redirect(url_for('messaging.inbox', listing_id=listing_id, other_user_id=recipient_id))
        
        try:
            # Create and save the new message
            message = Message(
                sender=current_user.id,
                recipient=recipient.id,
                listing=listing.id if listing else None, # Associate with listing if present
                content=content
            )
            message.save()

            # Create a notification for the recipient
            notification_message = f"You have a new message from {current_user.username} about '{listing.title}'." if listing else f"You have a new message from {current_user.username}."
            notification_link = url_for('messaging.inbox', listing_id=str(listing.id), other_user_id=str(current_user.id), _external=True) if listing else url_for('messaging.inbox', _external=True)

            Notification.create_notification(
                recipient_user=recipient,
                notification_type='new_message',
                message_content=notification_message,
                sender_user=current_user,
                link=notification_link
            )

            # Emit real-time notification to the recipient
            # This will update their notification badge and potentially show a toast
            socketio.emit('new_notification', {
                'message': notification_message,
                'link': notification_link,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'new_message'
            }, room=str(recipient.id))

            # Update recipient's unread count via SocketIO
            recipient_unread_count = Notification.objects(recipient=recipient.id, read=False).count()
            socketio.emit('update_notification_count', {'count': recipient_unread_count}, room=str(recipient.id))

            flash('Your message has been sent!', 'success')
            # Redirect to the inbox, focusing on the new conversation
            return redirect(url_for('messaging.inbox', listing_id=str(listing.id), other_user_id=str(recipient.id)))
        except Exception as e:
            current_app.logger.error(f"Error sending message: {e}")
            flash('An error occurred while sending your message. Please try again.', 'danger')
            return redirect(request.url)

    # For GET request (when initiating a message from a listing page)
    # We will redirect to the inbox with parameters to pre-select the conversation.
    # The actual chat window content is loaded via AJAX in inbox.html.
    if listing and recipient:
        return redirect(url_for('messaging.inbox', listing_id=str(listing.id), other_user_id=str(recipient.id)))
    else:
        # If no listing context, just go to general inbox
        return redirect(url_for('messaging.inbox'))

