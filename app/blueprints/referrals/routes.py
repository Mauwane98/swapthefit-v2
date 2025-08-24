from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_required, current_user
from app.models.referrals import Referral
from app.models.users import User

referrals_bp = Blueprint('referrals', __name__)

@referrals_bp.route("/my_referrals")
@login_required
def my_referrals():
    user_referral_code = current_user.referral_code
    # Find all referrals where the current user is the referrer
    my_referred_users = Referral.objects(referrer=current_user.id).order_by('-created_at')
    
    return render_template(
        "referrals/my_referrals.html",
        title="My Referrals",
        user_referral_code=user_referral_code,
        my_referred_users=my_referred_users
    )
