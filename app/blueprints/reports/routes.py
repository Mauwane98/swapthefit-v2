# app/blueprints/reports/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app.models.reports import Report
from app.models.users import User
from app.models.listings import Listing # Needed to verify reported listings
from app.blueprints.reports.forms import ReportForm, ResolveReportForm
from app.extensions import db
from app.blueprints.notifications.routes import add_notification # Import for report notifications
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route("/report/submit/<string:entity_type>/<string:entity_id>", methods=['GET', 'POST'])
@login_required
def submit_report(entity_type, entity_id):
    """
    Allows a user to submit a report against a listing or another user.
    'entity_type' can be 'listing' or 'user'.
    'entity_id' is the ID of the reported listing or user.
    """
    form = ReportForm()
    reported_entity = None
    entity_name = "unknown"

    if entity_type not in ['listing', 'user']:
        flash('Invalid entity type for reporting.', 'danger')
        return redirect(url_for('landing_bp.index')) # Or a more appropriate fallback

    if entity_type == 'listing':
        reported_entity = Listing.objects(id=entity_id).first()
        if reported_entity:
            entity_name = reported_entity.title
        else:
            flash('Listing not found.', 'danger')
            return redirect(url_for('listings.marketplace'))
    elif entity_type == 'user':
        reported_entity = User.objects(id=entity_id).first()
        if reported_entity:
            entity_name = reported_entity.username
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('listings.marketplace')) # Or user search page

    # Prevent reporting oneself
    if entity_type == 'user' and current_user.id == reported_entity.id:
        flash('You cannot report yourself.', 'danger')
        return redirect(url_for('listings.user_profile', user_id=reported_entity.id))

    if form.validate_on_submit():
        # Ensure the ID matches the entity_id from the URL
        if form.reported_entity_id.data != entity_id:
            flash('Mismatch between URL entity ID and form entity ID.', 'danger')
            return render_template('reports/submit_report.html', title='Submit Report', form=form, 
                                   entity_type=entity_type, entity_id=entity_id, entity_name=entity_name)

        report = Report(
            reporter_id=current_user.id,
            reported_entity_type=entity_type,
            reported_entity_id=entity_id,
            reason_category=form.reason_category.data,
            description=form.description.data,
            status='pending'
        )
        report.save()

        flash('Your report has been submitted and will be reviewed by an administrator.', 'success')

        # Notify admins about the new report
        # In a real application, you might have a specific admin group or role to notify.
        # For simplicity, we'll assume admins will check the admin dashboard.
        # However, a notification can be sent to all admins for immediate attention.
        admins = User.objects(role='admin')
        for admin in admins:
            add_notification(
                user_id=admin.id,
                message=f"New report submitted for {entity_type} '{entity_name}' (ID: {entity_id}).",
                notification_type='new_report',
                payload={'report_id': report.id, 'entity_type': entity_type, 'entity_id': entity_id}
            )

        return redirect(url_for('reports.my_reports'))
    
    # Pre-populate reported_entity_id if it's a GET request
    if request.method == 'GET':
        form.reported_entity_id.data = entity_id

    return render_template('reports/submit_report.html', title='Submit Report', form=form, 
                           entity_type=entity_type, entity_id=entity_id, entity_name=entity_name)

@reports_bp.route("/reports/my")
@login_required
def my_reports():
    """
    Displays reports submitted by the current user.
    """
    submitted_reports = Report.objects(reporter_id=current_user.id).order_by('-date_reported')
    
    # Fetch reported entity details for display
    for report in submitted_reports:
        if report.reported_entity_type == 'listing':
            report.reported_object = Listing.objects(id=report.reported_entity_id).first()
        elif report.reported_entity_type == 'user':
            report.reported_object = User.objects(id=report.reported_entity_id).first()
        else:
            report.reported_object = None # Fallback

    return render_template('reports/my_reports.html', 
                           title='My Reports', 
                           submitted_reports=submitted_reports)

@reports_bp.route("/reports/<string:report_id>")
@login_required
def report_detail(report_id):
    """
    Displays the details of a specific report.
    Only accessible by the reporter or an admin.
    """
    report = Report.objects(id=report_id).first_or_404()
    
    # Check if the current user is authorized to view this report
    if not (current_user.id == report.reporter_id or 
            current_user.role == 'admin'):
        abort(403) # Forbidden

    # Fetch reported entity details for display
    if report.reported_entity_type == 'listing':
        report.reported_object = Listing.objects(id=report.reported_entity_id).first()
    elif report.reported_entity_type == 'user':
        report.reported_object = User.objects(id=report.reported_entity_id).first()
    else:
        report.reported_object = None # Fallback
    
    return render_template('reports/report_detail.html', title='Report Details', report=report)

# --- Admin Routes for Report Management ---
@reports_bp.route("/admin/reports")
@login_required
def manage_reports():
    """
    Admin route to view and manage all reports.
    """
    if current_user.role != 'admin':
        abort(403) # Forbidden
    
    status_filter = request.args.get('status', 'all')
    query = Report.objects
    if status_filter != 'all':
        query = query(status=status_filter)
        
    reports = query.order_by('-date_reported')

    # Fetch reported entity details for each report
    for report in reports:
        if report.reported_entity_type == 'listing':
            report.reported_object = Listing.objects(id=report.reported_entity_id).first()
        elif report.reported_entity_type == 'user':
            report.reported_object = User.objects(id=report.reported_entity_id).first()
        else:
            report.reported_object = None # Fallback
    
    return render_template('admin/manage_reports.html', 
                           title='Manage Reports', 
                           reports=reports, 
                           status_filter=status_filter)

@reports_bp.route("/admin/reports/<string:report_id>/resolve", methods=['GET', 'POST'])
@login_required
def resolve_report(report_id):
    """
    Admin route to update the status and add admin notes for a report.
    """
    if current_user.role != 'admin':
        abort(403) # Forbidden
    
    report = Report.objects(id=report_id).first_or_404()
    form = ResolveReportForm()

    # Fetch reported entity details for display
    if report.reported_entity_type == 'listing':
        report.reported_object = Listing.objects(id=report.reported_entity_id).first()
    elif report.reported_entity_type == 'user':
        report.reported_object = User.objects(id=report.reported_entity_id).first()
    else:
        report.reported_object = None # Fallback

    if form.validate_on_submit():
        report.status = form.status.data
        report.admin_notes = form.admin_notes.data
        
        # Set date_resolved if status is 'resolved' or 'dismissed' and it's not already set
        if report.status in ['resolved', 'dismissed'] and not report.date_resolved:
            report.date_resolved = datetime.utcnow()
        elif report.status not in ['resolved', 'dismissed']:
            report.date_resolved = None # Clear if status reverts

        report.save()
        flash('Report updated successfully!', 'success')

        # Notify the reporter about the report status change
        add_notification(
            user_id=report.reporter.id,
            message=f"Your report (ID: {report.id}) regarding {report.reported_entity_type} '{report.reported_object.username if report.reported_object and report.reported_entity_type == 'user' else report.reported_object.title if report.reported_object and report.reported_entity_type == 'listing' else 'an entity'}' has been updated to '{report.status}'.",
            notification_type='report_update',
            payload={'report_id': report.id, 'status': report.status, 'entity_type': report.reported_entity_type, 'entity_id': report.reported_entity_id}
        )

        return redirect(url_for('reports.manage_reports'))
    
    elif request.method == 'GET':
        form.status.data = report.status
        form.admin_notes.data = report.admin_notes
        
    return render_template('admin/resolve_report.html', title='Resolve Report', form=form, report=report)

