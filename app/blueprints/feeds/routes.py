from flask import render_template, Blueprint, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.blueprints.feeds import feeds_bp
from app.models.user_activity import UserActivity
from mongoengine.queryset.visitor import Q # Import Q for complex queries
from datetime import datetime # Import datetime

FEEDS_PER_PAGE = 20 # Define pagination constant

@feeds_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    activity_type = request.args.get('activity_type', 'all')
    sort_by = request.args.get('sort_by', '-timestamp') # Default to newest first

    query = Q()

    if activity_type != 'all':
        query &= Q(action_type=activity_type)

    # Add more filtering options here if needed, e.g., by user, by specific payload data

    activities_pagination = UserActivity.objects(query).order_by(sort_by).paginate(page=page, per_page=FEEDS_PER_PAGE)

    # Get distinct activity types for filter dropdown
    distinct_activity_types = UserActivity.objects.distinct('action_type')
    distinct_activity_types.sort() # Sort alphabetically

    return render_template('feeds/index.html',
                           activities_pagination=activities_pagination,
                           title='Activity Feed',
                           current_activity_type=activity_type,
                           current_sort_by=sort_by,
                           distinct_activity_types=distinct_activity_types,
                           datetime=datetime) # Pass datetime to the template
