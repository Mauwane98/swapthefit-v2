from app import create_app
from app.models.users import User
from app.models.listings import Listing
from app.models.messages import Message
from app.models.reviews import Review
from app.models.swaps import SwapRequest
from app.models.wishlist import Wishlist
from app.extensions import mongo
from werkzeug.security import generate_password_hash
import datetime

def seed_admin_user():
    app = create_app()
    with app.app_context():
        if not User.find_by_email("admin@example.com"):
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("adminpassword"),
                is_admin=True
            )
            admin_user.save()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

def seed_sample_data():
    app = create_app()
    with app.app_context():
        # Create some regular users
        user1 = User.find_by_email("user1@example.com")
        if not user1:
            user1 = User(
                username="user1",
                email="user1@example.com",
                password_hash=generate_password_hash("password123")
            )
            user1.save()
            print("User1 created.")
        else:
            print("User1 already exists.")

        user2 = User.find_by_email("user2@example.com")
        if not user2:
            user2 = User(
                username="user2",
                email="user2@example.com",
                password_hash=generate_password_hash("password123")
            )
            user2.save()
            print("User2 created.")
        else:
            print("User2 already exists.")

        # Create sample listings
        listing1_data = mongo.db.listings.find_one({'item_name': "Sample Listing 1"})
        if not listing1_data:
            listing1 = Listing(
                user_id=user1.id,
                item_name="Sample Listing 1",
                description="This is a description for sample listing 1.",
                price=10.00,
                size="M",
                condition="Used",
                school_name="Sample School"
            )
            listing1.save()
            print("Listing 1 created.")
        else:
            listing1 = Listing(**listing1_data)
            print("Listing 1 already exists.")

        listing2_data = mongo.db.listings.find_one({'item_name': "Sample Listing 2"})
        if not listing2_data:
            listing2 = Listing(
                user_id=user2.id,
                item_name="Sample Listing 2",
                description="This is a description for sample listing 2.",
                price=20.00,
                size="L",
                condition="New",
                school_name="Another School"
            )
            listing2.save()
            print("Listing 2 created.")
        else:
            listing2 = Listing(**listing2_data)
            print("Listing 2 already exists.")

        # Create sample messages
        if not mongo.db.messages.find_one({'sender_id': user1.id, 'receiver_id': user2.id, 'content': "Is Sample Listing 2 still available?"}):
            Message.create(
                sender_id=user1.id,
                receiver_id=user2.id,
                listing_id=listing2.id,
                content="Is Sample Listing 2 still available?"
            )
            print("Message 1 created.")
        else:
            print("Message 1 already exists.")

        # Create sample swap requests
        if not mongo.db.swap_requests.find_one({'proposer_id': user1.id, 'requested_listing_id': listing1.id}):
            swap_request1 = SwapRequest(
                proposer_id=user1.id,
                receiver_id=user2.id,
                requested_listing_id=listing1.id,
                offered_listing_id=listing2.id,
                status="pending"
            )
            swap_request1.save()
            print("Swap Request 1 created.")
        else:
            print("Swap Request 1 already exists.")

        # Create sample reviews
        if not Review.has_reviewed(user1.id, user2.id):
            review1 = Review(
                reviewer_id=user1.id,
                reviewed_user_id=user2.id,
                rating=5,
                comment="Great user to swap with!"
            )
            review1.save()
            print("Review 1 created.")
        else:
            print("Review 1 already exists.")

        # Create sample wishlist items
        if not mongo.db.wishlist.find_one({'user_id': user1.id, 'listing_id': listing2.id}):
            wishlist_item1 = Wishlist(
                user_id=user1.id,
                listing_id=listing2.id
            )
            wishlist_item1.save()
            print("Wishlist item 1 created.")
        else:
            print("Wishlist item 1 already exists.")


if __name__ == "__main__":
    seed_admin_user()
    seed_sample_data()
    print("Database seeding complete.")
