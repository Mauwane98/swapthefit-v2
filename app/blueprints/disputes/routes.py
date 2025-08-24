# app/blueprints/disputes/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app.models.disputes import Dispute
from app.models.users import User
from app.models.listings import Listing # May be needed to link disputes to listings
from app.blueprints.disputes.forms import RaiseDisputeForm, ResolveDisputeForm

from app.blueprints.notifications.routes import add_notification # Import for dispute notifications
from datetime import datetime
from app.services.fraud_detection_service import FraudDetectionService
from app.services.user_reputation_service import update_dispute_counts # Import for updating user trust score

disputes_bp = Blueprint('disputes', __name__)

@disputes_bp.route("/disputes/raise/<string:entity_type>/<string:entity_id>", methods=['GET', 'POST'])
@login_required
def raise_dispute(entity_type, entity_id):
    """
    Allows a user to raise a new dispute against a user or a listing.
    'entity_type' can be 'user' or 'listing'.
    'entity_id' is the ID of the user or listing being disputed.
    """
    form = RaiseDisputeForm()

    if entity_type not in ['user', 'listing']:
        flash('Invalid entity type for raising a dispute.', 'danger')
        return redirect(url_for('landing_bp.index')) # Or a more appropriate fallback

    # Pre-populate form fields based on entity_type
    if request.method == 'GET':
        if entity_type == 'user':
            form.respondent_id.data = entity_id
        elif entity_type == 'listing':
            form.listing_id.data = entity_id

    if form.validate_on_submit():
        respondent_id = form.respondent_id.data
        listing_id = form.listing_id.data
        reason = form.reason.data

        # Ensure respondent exists
        respondent = User.objects(id=respondent_id).first()
        if not respondent:
            flash('The user ID for the other party is invalid.', 'danger')
            return render_template('disputes/raise_dispute.html', title='Raise Dispute', form=form)
        
        # Prevent disputing oneself
        if current_user.id == respondent.id:
            flash('You cannot raise a dispute against yourself.', 'danger')
            return render_template('disputes/raise_dispute.html', title='Raise Dispute', form=form)

        # Check if listing exists if provided
        listing = None
        if listing_id:
            listing = Listing.objects(id=listing_id).first()
            if not listing:
                flash('The provided Listing ID is invalid.', 'danger')
                return render_template('disputes/raise_dispute.html', title='Raise Dispute', form=form)
            # Optional: Add logic to ensure the listing is relevant to the initiator or respondent
            # e.g., if listing.user_id != current_user.id and listing.user_id != respondent.id:
            # flash('Listing is not related to either party.', 'danger')

        dispute = Dispute(
            initiator=current_user,
            respondent=respondent,
            listing=listing,
            reason=reason,
            status='open'
        )
        dispute.save()

        # Run fraud detection for initiator and respondent
        FraudDetectionService.check_user_dispute_volume(current_user.id)
        FraudDetectionService.check_user_dispute_volume(respondent.id)

        flash('Your dispute has been submitted and will be reviewed by an administrator.', 'success')

        # Notify the respondent about the new dispute
        add_notification(
            user_id=respondent.id,
            message=f"A dispute has been raised against you by {current_user.username} (Dispute ID: {dispute.id}).",
            notification_type='dispute_raised',
            payload={'dispute_id': str(dispute.id), 'initiator_id': str(current_user.id)}
        )
        # Notify admins about the new dispute (optional, for direct admin alerts)
        # You'd typically find admin IDs or have a dedicated admin notification channel
        # For now, let's assume admins will check the admin dashboard for new disputes.

        return redirect(url_for('disputes.my_disputes'))
    return render_template('disputes/raise_dispute.html', title='Raise Dispute', form=form)

@disputes_bp.route("/disputes/my")
@login_required
def my_disputes():
    """
    Displays disputes initiated by or involving the current user.
    """
    initiated_disputes = Dispute.objects(initiator=current_user).order_by('-date_raised')
    received_disputes = Dispute.objects(respondent=current_user).order_by('-date_raised')
    
    return render_template('disputes/my_disputes.html', 
                           title='My Disputes', 
                           initiated_disputes=initiated_disputes, 
                           received_disputes=received_disputes)

@disputes_bp.route("/disputes/<string:dispute_id>")
@login_required
def dispute_detail(dispute_id):
    """
    Displays the details of a specific dispute.
    Only accessible by the initiator, respondent, or an admin.
    """
    dispute = Dispute.objects(id=dispute_id).first_or_404()
    
    # Check if the current user is authorized to view this dispute
    if not (current_user.id == dispute.initiator.id or 
            current_user.id == dispute.respondent.id or 
            current_user.role == 'admin'):
        abort(403) # Forbidden
    
    return render_template('disputes/dispute_detail.html', title='Dispute Details', dispute=dispute)

# --- Admin Routes for Dispute Management ---
@disputes_bp.route("/admin/disputes")
@login_required
def manage_disputes():
    """
    Admin route to view and manage all disputes.
    """
    if current_user.role != 'admin':
        abort(403) # Forbidden
    
    # Optional: filter by status or search
    status_filter = request.args.get('status', 'all')
    query = Dispute.objects
    if status_filter != 'all':
        query = query.filter(status=status_filter)
        
    disputes = query.order_by('-date_raised')
    
    return render_template('admin/manage_disputes.html', 
                           title='Manage Disputes', 
                           disputes=disputes, 
                           status_filter=status_filter)

@disputes_bp.route("/admin/disputes/<string:dispute_id>/resolve", methods=['GET', 'POST'])
@login_required
def resolve_dispute(dispute_id):
    """
    Admin route to update the status and add resolution notes for a dispute.
    """
    if current_user.role != 'admin':
        abort(403) # Forbidden
    
    dispute = Dispute.objects(id=dispute_id).first_or_404()
    form = ResolveDisputeForm()

    if form.validate_on_submit():
        dispute.status = form.status.data
        dispute.resolution_notes = form.resolution_notes.data
        
        # Set date_resolved if status is 'resolved' or 'closed' and it's not already set
        if dispute.status in ['resolved', 'closed'] and not dispute.date_resolved:
            dispute.date_resolved = datetime.utcnow()
        elif dispute.status not in ['resolved', 'closed']:
            dispute.date_resolved = None # Clear if status reverts from resolved/closed

        dispute.save()
        flash('Dispute updated successfully!', 'success')

        # Update dispute counts for initiator and respondent
        if dispute.status == 'resolved': # Assuming 'resolved' means a clear outcome
            # The resolution_notes should ideally contain information about who was at fault or in favor.
            # For now, we'll use a simplified logic. You might need to add a field to the form
            # to explicitly state the resolution outcome (e.g., 'in_favor_of_initiator', 'in_favor_of_respondent').
            # Based on the current form, we'll assume 'resolved' implies a neutral resolution or
            # that the resolution_notes will clarify.
            # To properly update dispute counts, you need to know if the initiator or respondent was "at fault"
            # or "in favor". This requires more specific logic based on your dispute resolution process.
            # For demonstration, let's assume a simple case where 'resolved' means both parties get a 'resolved' count.
            # You'll need to refine this based on your actual dispute resolution outcomes.
            
            # Example of how you might call it if you had a clear outcome:
            # if form.resolution_outcome.data == 'in_favor_of_initiator':
            #     update_dispute_counts(dispute.initiator.id, 'resolved_in_favor_of_initiator')
            #     update_dispute_counts(dispute.respondent.id, 'resolved_against_respondent') # Assuming respondent was at fault
            # elif form.resolution_outcome.data == 'in_favor_of_respondent':
            #     update_dispute_counts(dispute.respondent.id, 'resolved_in_favor_of_respondent')
            #     update_dispute_counts(dispute.initiator.id, 'resolved_against_initiator') # Assuming initiator was at fault
            
            # For now, a placeholder call. You need to implement the logic to determine the actual resolution status.
            # This part needs careful consideration of your dispute resolution workflow.
            update_dispute_counts(dispute.initiator.id, 'resolved_in_favor_of_initiator') # Placeholder
            update_dispute_counts(dispute.respondent.id, 'resolved_in_favor_of_respondent') # Placeholder


        # Notify initiator and respondent about dispute status change
        message_to_initiator = f"Your dispute (ID: {dispute.id}) regarding '{dispute.listing.title if dispute.listing else 'an issue'}' has been updated to '{dispute.status}'. Check details."
        add_notification(
            user_id=dispute.initiator.id,
            message=message_to_initiator,
            notification_type='dispute_update',
            payload={'dispute_id': str(dispute.id), 'status': dispute.status}
        )
        
        message_to_respondent = f"The dispute (ID: {dispute.id}) raised by {dispute.initiator.username} against you has been updated to '{dispute.status}'. Check details."
        add_notification(
            user_id=dispute.respondent.id,
            message=message_to_respondent,
            notification_type='dispute_update',
            payload={'dispute_id': str(dispute.id), 'status': dispute.status}
        )

        # Run fraud detection for initiator and respondent after dispute resolution
        FraudDetectionService.check_user_dispute_volume(dispute.initiator.id)
        FraudDetectionService.check_user_dispute_volume(dispute.respondent.id)

        return redirect(url_for('disputes.manage_disputes'))
    
    elif request.method == 'GET':
        form.status.data = dispute.status
        form.resolution_notes.data = dispute.resolution_notes
        
    return render_template('admin/resolve_dispute.html', title='Resolve Dispute', form=form, dispute=dispute)