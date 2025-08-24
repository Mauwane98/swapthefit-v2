from app.models.users import User
from app.models.badges import Badge, UserBadge
from app.models.swaps import SwapRequest
from app.models.donations import Donation
from app.models.reviews import Review
from mongoengine.queryset.visitor import Q

class BadgeService:
    def __init__(self):
        # Define badge criteria. These can be loaded from a config or database in a real app.
        self.badge_definitions = {
            "Swap Master": {
                "description": "Awarded for completing 10 or more swaps.",
                "image_url": "badge_swap_master.png", # Placeholder image
                "criteria_func": self._check_swap_master
            },
            "Top Donor": {
                "description": "Awarded for completing 5 or more donations.",
                "image_url": "badge_top_donor.png", # Placeholder image
                "criteria_func": self._check_top_donor
            },
            "Trusted Trader": {
                "description": "Awarded for maintaining a high trust score and completing many transactions.",
                "image_url": "badge_trusted_trader.png", # Placeholder image
                "criteria_func": self._check_trusted_trader
            },
            # Add more badge definitions here
        }

    def _check_swap_master(self, user):
        completed_swaps_count = SwapRequest.objects(Q(requester=user.id) | Q(responder=user.id), status='completed').count()
        return completed_swaps_count >= 10

    def _check_top_donor(self, user):
        completed_donations_count = Donation.objects(Q(donor=user.id) | Q(recipient=user.id), status='completed').count()
        return completed_donations_count >= 5

    def _check_trusted_trader(self, user):
        # Example criteria: trust score >= 70, total transactions >= 20, positive reviews >= 15
        return user.trust_score >= 70 and user.total_transactions >= 20 and user.positive_reviews_count >= 15

    def check_and_award_badges(self, user):
        awarded_badges = []
        for badge_name, definition in self.badge_definitions.items():
            badge = Badge.objects(name=badge_name).first()
            if not badge:
                # Create badge if it doesn't exist in the database
                badge = Badge(
                    name=badge_name,
                    description=definition["description"],
                    image_url=definition["image_url"],
                    criteria={}
                )
                badge.save()

            if badge and definition["criteria_func"](user):
                # Check if user already has this badge
                if not UserBadge.objects(user=user.id, badge=badge.id).first():
                    user_badge = UserBadge(user=user.id, badge=badge.id)
                    user_badge.save()
                    awarded_badges.append(badge)
        return awarded_badges

    def get_user_badges(self, user):
        return UserBadge.objects(user=user.id).all()

badge_service = BadgeService()