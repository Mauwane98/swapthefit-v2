from app.models.user_activity import UserActivity
from app.models.listings import Listing
from app.models.wishlist import WishlistItem
from app.models.users import User
from mongoengine.queryset.visitor import Q

class RecommendationService:
    def __init__(self):
        pass

    def get_recommendations(self, user: User, limit: int = 10) -> list[Listing]:
        recommended_listings = []
        viewed_categories = set()
        viewed_brands = set()
        wishlist_categories = set()
        wishlist_brands = set()

        # 1. Get preferences from UserActivity (browsing history)
        recent_activities = UserActivity.objects(user=user).order_by('-timestamp').limit(50)
        for activity in recent_activities:
            if activity.action_type == 'viewed_listing' and activity.payload and 'listing_id' in activity.payload:
                try:
                    listing = Listing.objects.get(id=activity.payload['listing_id'])
                    viewed_categories.add(listing.uniform_type)
                    if listing.brand: # Check if brand exists
                        viewed_brands.add(listing.brand)
                except Listing.DoesNotExist:
                    continue

        # 2. Get preferences from Wishlist
        user_wishlist = WishlistItem.objects(user=user).first()
        if user_wishlist:
            for item in user_wishlist.items:
                wishlist_categories.add(item.category)
                if item.brand: # Check if brand exists
                    wishlist_brands.add(item.brand)

        all_preferred_categories = list(viewed_categories.union(wishlist_categories))
        all_preferred_brands = list(viewed_brands.union(wishlist_brands))

        # Build a query for recommendations
        query_filters = Q()

        if all_preferred_categories:
            query_filters |= Q(uniform_type__in=all_preferred_categories)
        if all_preferred_brands:
            query_filters |= Q(brand__in=all_preferred_brands)

        # Exclude listings already viewed by the user (optional, but good for fresh recommendations)
        viewed_listing_ids = [activity.payload['listing_id'] for activity in recent_activities if activity.action_type == 'viewed_listing' and activity.payload and 'listing_id' in activity.payload]
        if viewed_listing_ids:
            query_filters &= Q(id__nin=viewed_listing_ids)

        # Exclude listings already in the user's wishlist
        if user_wishlist:
            wishlist_listing_ids = [item.listing.id for item in user_wishlist.items if item.listing]
            if wishlist_listing_ids:
                query_filters &= Q(id__nin=wishlist_listing_ids)

        # Fetch recommendations
        if query_filters:
            recommended_listings = Listing.objects(query_filters).limit(limit)
        else:
            # Fallback: if no strong preferences, recommend popular or newest listings
            recommended_listings = Listing.objects().order_by('-created_at').limit(limit)

        return list(recommended_listings)

    def get_similar_listings(self, listing: Listing, limit: int = 5) -> list[Listing]:
        """
        Gets listings similar to a given listing based on category and brand.
        """
        query_filters = Q(
            Q(uniform_type=listing.uniform_type) |
            Q(brand=listing.brand)
        )
        # Exclude the current listing itself
        query_filters &= Q(id__ne=listing.id)

        similar_listings = Listing.objects(query_filters).limit(limit)
        return list(similar_listings)