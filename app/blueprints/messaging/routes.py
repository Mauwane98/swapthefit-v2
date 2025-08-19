from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.messages import Message
from app.models.users import User # Import User model to fetch sender/receiver info
from app.extensions import db
from mongoengine.queryset.visitor import Q # Import Q for complex queries

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/inbox')
@login_required
def inbox():
    """
    Displays the user's inbox, showing a list of active conversations
    and the messages within a selected conversation.
    """
    # Get all unique users current_user has exchanged messages with
    # This involves querying messages where current_user is either sender or receiver
    sender_ids = Message.objects(receiver=current_user).distinct('sender')
    receiver_ids = Message.objects(sender=current_user).distinct('receiver')

    # Combine results and exclude current_user themselves
    partner_ids = list(set(sender_ids + receiver_ids))
    if current_user.id in partner_ids:
        partner_ids.remove(current_user.id)

    # Fetch User objects for conversation partners
    conversation_partners = User.objects(id__in=partner_ids)

    # Sort conversations by the latest message
    sorted_partners = []
    for partner in conversation_partners:
        latest_message = Message.objects(
            (Q(sender=current_user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=current_user))
        ).order_by('-timestamp').first()
        if latest_message:
            sorted_partners.append((partner, latest_message.timestamp))
    
    # Sort partners by the timestamp of their latest message (most recent first)
    sorted_partners.sort(key=lambda x: x[1], reverse=True)
    conversation_partners = [partner for partner, _ in sorted_partners]


    selected_conversation_id = request.args.get('user_id', type=str) # Changed to str for ObjectId
    messages = []
    selected_partner = None

    if selected_conversation_id:
        selected_partner = User.objects(id=selected_conversation_id).first()
        if selected_partner and selected_partner.id != current_user.id:
            # Fetch messages between current_user and selected_partner
            messages = Message.objects(
                (Q(sender=current_user) & Q(receiver=selected_partner)) |
                (Q(sender=selected_partner) & Q(receiver=current_user))
            ).order_by('timestamp')

            # Mark messages sent *to* the current user as read
            for message in messages:
                if message.receiver == current_user and not message.read_status:
                    message.read_status = True
                    message.save() # Save the updated message

    return render_template(
        'messaging/inbox.html',
        conversation_partners=conversation_partners,
        messages=messages,
        selected_partner=selected_partner
    )

@messaging_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """
    Handles sending a new message.
    Expects 'receiver_id' and 'content' in the form data.
    """
    receiver_id = request.form.get('receiver_id', type=str) # Changed to str for ObjectId
    content = request.form.get('content')

    if not receiver_id or not content:
        flash('Receiver and message content are required.', 'danger')
        return redirect(url_for('messaging.inbox'))

    receiver = User.objects(id=receiver_id).first()
    if not receiver:
        flash('Invalid recipient.', 'danger')
        return redirect(url_for('messaging.inbox'))

    if current_user.id == receiver.id:
        flash('You cannot send messages to yourself.', 'danger')
        return redirect(url_for('messaging.inbox'))

    try:
        new_message = Message(
            sender=current_user,
            receiver=receiver,
            content=content
        )
        new_message.save()
        flash('Message sent!', 'success')
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'danger')

    return redirect(url_for('messaging.inbox', user_id=receiver_id))


@messaging_bp.route('/api/messages/<string:partner_id>') # Changed to string for ObjectId
@login_required
def api_get_messages(partner_id):
    """
    API endpoint to fetch messages between the current user and a specific partner.
    Used for AJAX updates in the chat interface.
    """
    partner = User.objects(id=partner_id).first()
    if not partner:
        return jsonify({'error': 'Partner not found'}), 404

    messages = Message.objects(
        (Q(sender=current_user) & Q(receiver=partner)) |
        (Q(sender=partner) & Q(receiver=current_user))
    ).order_by('timestamp')

    # Mark messages sent *to* the current user as read
    for message in messages:
        if message.receiver == current_user and not message.read_status:
            message.read_status = True
            message.save() # Save the updated message

    return jsonify([msg.to_dict() for msg in messages])

@messaging_bp.route('/api/conversations')
@login_required
def api_get_conversations():
    """
    API endpoint to fetch a list of conversation partners for the current user.
    Used for AJAX updates of the conversation list.
    """
    sender_ids = Message.objects(receiver=current_user).distinct('sender')
    receiver_ids = Message.objects(sender=current_user).distinct('receiver')

    partner_ids = list(set(sender_ids + receiver_ids))
    if current_user.id in partner_ids:
        partner_ids.remove(current_user.id)

    conversation_partners = User.objects(id__in=partner_ids)

    partners_data = []
    for partner in conversation_partners:
        latest_message = Message.objects(
            (Q(sender=current_user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=current_user))
        ).order_by('-timestamp').first()

        unread_count = Message.objects(
            sender=partner,
            receiver=current_user,
            read_status=False
        ).count()

        if latest_message:
            partners_data.append({
                'id': str(partner.id),
                'username': partner.username,
                'latest_message_content': latest_message.content,
                'latest_message_timestamp': latest_message.timestamp.isoformat() + 'Z',
                'profile_pic': partner.image_file, # Assuming User model has image_file
                'unread_count': unread_count
            })
    
    # Sort partners by the timestamp of their latest message (most recent first)
    partners_data.sort(key=lambda x: x['latest_message_timestamp'], reverse=True)

    return jsonify(partners_data)
