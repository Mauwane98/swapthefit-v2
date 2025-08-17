from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models.swaps import SwapRequest
from app.models.listings import Listing
from app.models.users import User
from app.models.notifications import Notification
from app.blueprints.auth.routes import roles_required # For role-based access control
from app.extensions import socketio # Import socketio for real-time updates
from datetime import datetime

swaps_bp = Blueprint('swaps', __name__, url_prefix='/swaps', template_folder='templates')

@swaps_bp.route('/propose/<string:listing_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Only these roles can propose swaps
def propose_swap(listing_id):
    """
    Handles the proposal of a new swap request.
    A user proposes to swap one of their listings for another user's listing.
    """
    # The listing the current user wants
    requested_listing = Listing.objects(id=listing_id).first()
    if not requested_listing:
        flash('Requested listing not found.', 'danger')
        return redirect(url_for('listings.marketplace'))

    # Prevent proposing a swap for your own listing
    if str(requested_listing.owner.id) == str(current_user.id):
        flash('You cannot propose a swap for your own listing.', 'warning')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))

    # Get the current user's active listings that are available for swap
    # Exclude listings that are already 'pending_swap' or 'swapped'
    user_listings_for_swap = Listing.objects(
        owner=current_user.id, 
        is_active=True,
        status='available'
    ).all()

    # If the user has no available listings to offer, they cannot propose a swap
    if not user_listings_for_swap:
        flash('You need to have at least one available listing to propose a swap.', 'info')
        return redirect(url_for('listings.create_listing')) # Suggest creating a listing

    if request.method == 'POST':
        offered_listing_id = request.form.get('offered_listing_id')
        offered_listing = Listing.objects(id=offered_listing_id).first()

        # Validate the offered listing
        if not offered_listing or str(offered_listing.owner.id) != str(current_user.id):
            flash('Invalid listing offered for swap.', 'danger')
            return redirect(url_for('swaps.propose_swap', listing_id=listing_id))

        # Check if a similar swap request already exists (e.g., pending)
        existing_swap = SwapRequest.objects(
            proposer=current_user.id,
            recipient=requested_listing.owner.id,
            requested_listing=requested_listing.id,
            offered_listing=offered_listing.id,
            status='pending'
        ).first()

        if existing_swap:
            flash('You already have a pending swap request for these items.', 'info')
            return redirect(url_for('listings.listing_detail', listing_id=listing_id))
            
        try:
            # Create the new swap request
            swap_request = SwapRequest(
                proposer=current_user.id,
                recipient=requested_listing.owner.id,
                requested_listing=requested_listing.id,
                offered_listing=offered_listing.id,
                status='pending'
            )
            swap_request.save()

            # Update status of both listings to 'pending_swap' (optional, but good practice)
            requested_listing.status = 'pending_swap'
            requested_listing.save()
            offered_listing.status = 'pending_swap'
            offered_listing.save()

            # Create a notification for the recipient of the swap request
            notification_message = f"{current_user.username} has proposed a swap for your item: '{requested_listing.title}'."
            notification_link = url_for('swaps.view_swap_request', request_id=str(swap_request.id), _external=True)

            Notification.create_notification(
                recipient_user=requested_listing.owner,
                notification_type='swap_request',
                message_content=notification_message,
                sender_user=current_user,
                link=notification_link
            )

            # Emit real-time notification to the recipient
            socketio.emit('new_notification', {
                'message': notification_message,
                'link': notification_link,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'swap_request'
            }, room=str(requested_listing.owner.id))

            # Update recipient's unread count via SocketIO
            recipient_unread_count = Notification.objects(recipient=requested_listing.owner.id, read=False).count()
            socketio.emit('update_notification_count', {'count': recipient_unread_count}, room=str(requested_listing.owner.id))

            flash('Swap request has been sent successfully!', 'success')
            return redirect(url_for('listings.listing_detail', listing_id=listing_id))
        except Exception as e:
            current_app.logger.error(f"Error proposing swap: {e}")
            flash('An error occurred while proposing the swap. Please try again.', 'danger')

    return render_template(
        'swaps/propose_swap.html', 
        requested_listing=requested_listing, 
        user_listings=user_listings_for_swap,
        title='Propose Swap'
    )

@swaps_bp.route('/manage')
@login_required
def manage_swaps():
    """
    Displays all incoming and outgoing swap requests for the current user.
    """
    # Fetch incoming swap requests (where current user is the recipient)
    incoming_swaps = SwapRequest.objects(recipient=current_user.id).order_by('-date_proposed').all()
    
    # Fetch outgoing swap requests (where current user is the proposer)
    outgoing_swaps = SwapRequest.objects(proposer=current_user.id).order_by('-date_proposed').all()

    return render_template(
        'swaps/manage_swaps.html', 
        incoming_swaps=incoming_swaps, 
        outgoing_swaps=outgoing_swaps,
        title='Manage Swaps'
    )

@swaps_bp.route('/view/<string:request_id>')
@login_required
def view_swap_request(request_id):
    """
    Displays the details of a specific swap request.
    Allows the recipient to accept or reject the request.
    """
    swap_request = SwapRequest.objects(id=request_id).first()
    if not swap_request:
        abort(404) # Swap request not found

    # Ensure current user is either the proposer or recipient to view
    if str(swap_request.proposer.id) != str(current_user.id) and \
       str(swap_request.recipient.id) != str(current_user.id):
        flash('You do not have permission to view this swap request.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))

    return render_template(
        'swaps/view_swap_request.html', # Create this template next
        swap_request=swap_request,
        title='Swap Request Details'
    )


@swaps_bp.route('/respond/<string:request_id>/<string:action>', methods=['POST'])
@login_required
def respond_swap(request_id, action):
    """
    Handles the response (accept/reject/cancel) to a swap request.
    - 'accept' and 'reject' actions are for the recipient.
    - 'cancel' action is for the proposer.
    """
    swap_request = SwapRequest.objects(id=request_id).first()
    if not swap_request:
        flash('Swap request not found.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))

    # Action: Accept or Reject (by Recipient)
    if action in ['accept', 'reject']:
        if str(swap_request.recipient.id) != str(current_user.id):
            flash('You do not have permission to respond to this swap request.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        if swap_request.status != 'pending':
            flash(f'This swap request is already {swap_request.status}.', 'warning')
            return redirect(url_for('swaps.view_swap_request', request_id=request_id))

        swap_request.status = action + 'ed' # 'accepted' or 'rejected'
        
        # Update listing statuses based on action
        if action == 'accept':
            # Mark both listings as 'swapped'
            swap_request.requested_listing.status = 'swapped'
            swap_request.requested_listing.save()
            swap_request.offered_listing.status = 'swapped'
            swap_request.offered_listing.save()
            # Optionally, deactivate other pending swaps involving these listings
            # (more complex logic needed for this)
            flash_message = 'Swap request accepted! Both listings are now marked as swapped.'
        else: # action == 'reject'
            # Revert listings to 'available' if they were 'pending_swap'
            if swap_request.requested_listing.status == 'pending_swap':
                swap_request.requested_listing.status = 'available'
                swap_request.requested_listing.save()
            if swap_request.offered_listing.status == 'pending_swap':
                swap_request.offered_listing.status = 'available'
                swap_request.offered_listing.save()
            flash_message = 'Swap request rejected.'

        swap_request.save()

        # Notify the proposer
        notification_message = f"Your swap request for '{swap_request.requested_listing.title}' has been {action}ed."
        notification_link = url_for('swaps.view_swap_request', request_id=str(swap_request.id), _external=True)

        Notification.create_notification(
            recipient_user=swap_request.proposer,
            notification_type='swap_status_update',
            message_content=notification_message,
            sender_user=current_user,
            link=notification_link
        )
        socketio.emit('new_notification', {
            'message': notification_message,
            'link': notification_link,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'swap_status_update'
        }, room=str(swap_request.proposer.id))
        proposer_unread_count = Notification.objects(recipient=swap_request.proposer.id, read=False).count()
        socketio.emit('update_notification_count', {'count': proposer_unread_count}, room=str(swap_request.proposer.id))

        flash(flash_message, 'success')
        return redirect(url_for('swaps.manage_swaps'))

    # Action: Cancel (by Proposer)
    elif action == 'cancel':
        if str(swap_request.proposer.id) != str(current_user.id):
            flash('You do not have permission to cancel this swap request.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        if swap_request.status != 'pending':
            flash(f'This swap request is already {swap_request.status} and cannot be cancelled.', 'warning')
            return redirect(url_for('swaps.view_swap_request', request_id=request_id))
        
        swap_request.status = 'cancelled'
        swap_request.save()

        # Revert listing statuses to 'available'
        if swap_request.requested_listing.status == 'pending_swap':
            swap_request.requested_listing.status = 'available'
            swap_request.requested_listing.save()
        if swap_request.offered_listing.status == 'pending_swap':
            swap_request.offered_listing.status = 'available'
            swap_request.offered_listing.save()

        # Notify the recipient of the cancellation
        notification_message = f"{current_user.username} has cancelled the swap request for '{swap_request.requested_listing.title}'."
        notification_link = url_for('swaps.view_swap_request', request_id=str(swap_request.id), _external=True)

        Notification.create_notification(
            recipient_user=swap_request.recipient,
            notification_type='swap_status_update',
            message_content=notification_message,
            sender_user=current_user,
            link=notification_link
        )
        socketio.emit('new_notification', {
            'message': notification_message,
            'link': notification_link,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'swap_status_update'
        }, room=str(swap_request.recipient.id))
        recipient_unread_count = Notification.objects(recipient=swap_request.recipient.id, read=False).count()
        socketio.emit('update_notification_count', {'count': recipient_unread_count}, room=str(swap_request.recipient.id))

        flash('Swap request cancelled.', 'info')
        return redirect(url_for('swaps.manage_swaps'))

    flash('Invalid action.', 'danger')
    return redirect(url_for('swaps.manage_swaps'))
