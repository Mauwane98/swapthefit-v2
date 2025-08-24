from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_required
from app.models.sponsored_content import SponsoredContent
from app.blueprints.sponsored_content.forms import SponsoredContentForm
from app.utils.security import roles_required
from app.extensions import db
from datetime import datetime

sponsored_content_bp = Blueprint('sponsored_content', __name__)

@sponsored_content_bp.route("/admin/sponsored_content")
@login_required
@roles_required('admin')
def list_sponsored_content():
    sponsored_items = SponsoredContent.objects.all()
    return render_template("admin/sponsored_content/list.html", sponsored_items=sponsored_items, title="Manage Sponsored Content")

@sponsored_content_bp.route("/admin/sponsored_content/new", methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def create_sponsored_content():
    form = SponsoredContentForm()
    if form.validate_on_submit():
        try:
            sponsored_item = SponsoredContent(
                title=form.title.data,
                content=form.content.data,
                image_url=form.image_url.data,
                target_url=form.target_url.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                is_active=form.is_active.data
            )
            sponsored_item.save()
            flash('Sponsored content created successfully!', 'success')
            return redirect(url_for('sponsored_content.list_sponsored_content'))
        except Exception as e:
            flash(f'Error creating sponsored content: {e}', 'danger')
    return render_template("admin/sponsored_content/create_edit.html", form=form, title="Create Sponsored Content")

@sponsored_content_bp.route("/admin/sponsored_content/<string:item_id>/edit", methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_sponsored_content(item_id):
    sponsored_item = SponsoredContent.objects.get_or_404(id=item_id)
    form = SponsoredContentForm(obj=sponsored_item)
    if form.validate_on_submit():
        try:
            form.populate_obj(sponsored_item)
            sponsored_item.updated_at = datetime.utcnow()
            sponsored_item.save()
            flash('Sponsored content updated successfully!', 'success')
            return redirect(url_for('sponsored_content.list_sponsored_content'))
        except Exception as e:
            flash(f'Error updating sponsored content: {e}', 'danger')
    return render_template("admin/sponsored_content/create_edit.html", form=form, title="Edit Sponsored Content")

@sponsored_content_bp.route("/admin/sponsored_content/<string:item_id>/delete", methods=['POST'])
@login_required
@roles_required('admin')
def delete_sponsored_content(item_id):
    sponsored_item = SponsoredContent.objects.get_or_404(id=item_id)
    try:
        sponsored_item.delete()
        flash('Sponsored content deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting sponsored content: {e}', 'danger')
    return redirect(url_for('sponsored_content.list_sponsored_content'))
