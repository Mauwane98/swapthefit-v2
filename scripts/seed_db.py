# scripts/seed_db.py
import sys
import os
# Add the parent directory to the Python path so that 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import secrets
from app import create_app
from app.models.users import User
from app.models.listings import Listing
from app.models.messages import Message
from app.models.reviews import Review
from app.models.swaps import SwapRequest
from app.models.wishlist import WishlistItem
from app.models.donations import Donation
from app.models.payments import Order
from app.models.logistics import Logistics
from app.models.reports import Report
from app.models.disputes import Dispute
from app.models.saved_search import SavedSearch
from app.models.user_activity import UserActivity # Import UserActivity for clearing
from app.models.forums import Forum # Import Forum model
from app.extensions import db, bcrypt # db is MongoEngine instance here
from datetime import datetime, timedelta
import random
import os
from bson import ObjectId # Import ObjectId for MongoEngine IDs
from app.services.user_reputation_service import update_user_trust_score

def clear_all_collections(app):
    """
    Clears all data from the collections managed by MongoEngine models.
    Use with extreme caution, as this will delete all data!
    """
    with app.app_context():
        print("Clearing existing data...")
        User.objects.delete()
        Listing.objects.delete()
        Message.objects.delete()
        Review.objects.delete()
        SwapRequest.objects.delete()
        WishlistItem.objects.delete()
        Donation.objects.delete()
        Order.objects.delete()
        Logistics.objects.delete()
        Report.objects.delete()
        Dispute.objects.delete()
        SavedSearch.objects.delete()
        UserActivity.objects.delete() # Clear activity logs too for a fresh start
        Forum.objects.delete() # Clear forums
        print("All collections cleared.")

def seed_forums():
    """
    Seeds sample forum categories.
    """
    print("Seeding forums...")
    forums = {}

    if not Forum.objects(name="General Discussion").first():
        general_discussion = Forum(
            name="General Discussion",
            description="A place for all general discussions about school uniforms and supplies.",
            topic_count=0,
            post_count=0,
            last_post_at=datetime.utcnow()
        )
        general_discussion.save()
        print(f"Created Forum: {general_discussion.name}")
    else:
        general_discussion = Forum.objects(name="General Discussion").first()
        print(f"Forum '{general_discussion.name}' already exists.")
    forums['general_discussion'] = general_discussion

    if not Forum.objects(name="Swap & Sell Tips").first():
        swap_sell_tips = Forum(
            name="Swap & Sell Tips",
            description="Share and get tips on swapping and selling uniforms effectively.",
            topic_count=0,
            post_count=0,
            last_post_at=datetime.utcnow()
        )
        swap_sell_tips.save()
        print(f"Created Forum: {swap_sell_tips.name}")
    else:
        swap_sell_tips = Forum.objects(name="Swap & Sell Tips").first()
        print(f"Forum '{swap_sell_tips.name}' already exists.")
    forums['swap_sell_tips'] = swap_sell_tips

    if not Forum.objects(name="Donation Stories").first():
        donation_stories = Forum(
            name="Donation Stories",
            description="Share heartwarming stories about donations and their impact.",
            topic_count=0,
            post_count=0,
            last_post_at=datetime.utcnow()
        )
        donation_stories.save()
        print(f"Created Forum: {donation_stories.name}")
    else:
        donation_stories = Forum.objects(name="Donation Stories").first()
        print(f"Forum '{donation_stories.name}' already exists.")
    forums['donation_stories'] = donation_stories

    return forums

def seed_users():
    """
    Seeds various types of users.
    """
    users = {}
    print("Seeding users...")

    # Admin User with specified credentials
    admin_email = "oleratodichaba@gmail.com"
    admin_password = "wszxderfc1"
    if not User.objects(email=admin_email).first():
        admin = User(
            username="AdminUser",
            email=admin_email,
            password=bcrypt.generate_password_hash(admin_password).decode('utf-8'),
            role="admin",
            image_file="default.jpg",
            date_joined=datetime.utcnow() - timedelta(days=365)
        )
        admin.save()
        print(f"Created Admin: {admin.username} with email {admin_email}")
    else:
        admin = User.objects(email=admin_email).first()
        print(f"Admin user '{admin.username}' with email {admin_email} already exists.")
    users['admin'] = admin

    # Parent User 1
    parent1_email = "parent1@example.com"
    if not User.objects(email=parent1_email).first():
        parent1 = User(
            username="ParentOne",
            email=parent1_email,
            password=bcrypt.generate_password_hash("password").decode('utf-8'),
            role="parent",
            image_file="20190514_124208.jpg", # Example existing image
            date_joined=datetime.utcnow() - timedelta(days=180)
        )
        parent1.save()
        print(f"Created Parent: {parent1.username}")
    else:
        parent1 = User.objects(email=parent1_email).first()
        print(f"Parent user '{parent1.username}' already exists.")
    users['parent1'] = parent1

    # Parent User 2
    parent2_email = "parent2@example.com"
    if not User.objects(email=parent2_email).first():
        parent2 = User(
            username="ParentTwo",
            email=parent2_email,
            password=bcrypt.generate_password_hash("password").decode('utf-8'),
            role="parent",
            image_file="default.jpg",
            date_joined=datetime.utcnow() - timedelta(days=90)
        )
        parent2.save()
        print(f"Created Parent: {parent2.username}")
    else:
        parent2 = User.objects(email=parent2_email).first()
        print(f"Parent user '{parent2.username}' already exists.")
    users['parent2'] = parent2

    # School User
    school_email = "school@example.com"
    if not User.objects(email=school_email).first():
        school = User(
            username="SpringfieldHigh",
            email=school_email,
            password=bcrypt.generate_password_hash("schoolpass").decode('utf-8'),
            role="school",
            image_file="default.jpg",
            date_joined=datetime.utcnow() - timedelta(days=200)
        )
        school.save()
        print(f"Created School: {school.username}")
    else:
        school = User.objects(email=school_email).first()
        print(f"School user '{school.username}' already exists.")
    users['school'] = school

    # NGO User
    ngo_email = "ngo@example.com"
    if not User.objects(email=ngo_email).first():
        ngo = User(
            username="HelpingHands",
            email=ngo_email,
            password=bcrypt.generate_password_hash("ngopass").decode('utf-8'),
            role="ngo",
            image_file="default.jpg",
            date_joined=datetime.utcnow() - timedelta(days=150)
        )
        ngo.save()
        print(f"Created NGO: {ngo.username}")
    else:
        ngo = User.objects(email=ngo_email).first()
        print(f"NGO user '{ngo.username}' already exists.")
    users['ngo'] = ngo
    
    # No db.session.commit() needed for individual saves in MongoEngine, .save() commits
    return users

def seed_listings(users):
    """
    Seeds sample listings.
    """
    listings = {}
    print("Seeding listings...")

    # Listing 1 (Sale, Premium) by Parent1
    if not Listing.objects(title="Blue School Blazer").first():
        listing1 = Listing(
            user=users['parent1'].id, # ReferenceField requires ObjectId
            title="Blue School Blazer",
            description="Excellent condition blue school blazer, hardly worn. Suitable for 10-12 year olds.",
            price=250.00,
            uniform_type="School Uniform",
            condition="Used - Like New",
            size="Age 10-12",
            gender="Unisex",
            school_name="Springfield High",
            location="Johannesburg",
            image_file="default.jpg",
            listing_type="sale",
            is_premium=True,
            premium_expiry_date=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
            brand="School Outfitters",
            color="Blue"
        )
        listing1.save()
        print(f"Created Listing: {listing1.title}")
    else:
        listing1 = Listing.objects(title="Blue School Blazer").first()
        print(f"Listing '{listing1.title}' already exists.")
    listings['blazer'] = listing1

    # Listing 2 (Swap) by Parent2
    if not Listing.objects(title="Red Sports Shorts").first():
        listing2 = Listing(
            user=users['parent2'].id,
            title="Red Sports Shorts",
            description="Comfortable red sports shorts, size Small. Looking to swap for a larger size.",
            price=None,
            uniform_type="Sports Kit",
            condition="Used - Good",
            size="Small",
            gender="Unisex",
            school_name="Another School",
            location="Pretoria",
            image_file="default.jpg",
            listing_type="swap",
            is_premium=False,
            brand="Nike",
            color="Red"
        )
        listing2.save()
        print(f"Created Listing: {listing2.title}")
    else:
        listing2 = Listing.objects(title="Red Sports Shorts").first()
        print(f"Listing '{listing2.title}' already exists.")
    listings['shorts'] = listing2

    # Listing 3 (Donation) by Parent1
    if not Listing.objects(title="White School Shirt (Donation)").first():
        listing3 = Listing(
            user=users['parent1'].id,
            title="White School Shirt (Donation)",
            description="Clean white school shirt, size Medium. Happy to donate to a good cause.",
            price=None,
            uniform_type="School Uniform",
            condition="Used - Fair",
            size="Medium",
            gender="Male",
            school_name="Springfield High",
            location="Johannesburg",
            image_file="default.jpg",
            listing_type="donation",
            is_premium=False,
            brand="Generic",
            color="White"
        )
        listing3.save()
        print(f"Created Listing: {listing3.title}")
    else:
        listing3 = Listing.objects(title="White School Shirt (Donation)").first()
        print(f"Listing '{listing3.title}' already exists.")
    listings['shirt_donation'] = listing3

    # Listing 4 (Sale) by Parent2 - for purchase example
    if not Listing.objects(title="Black School Shoes").first():
        listing4 = Listing(
            user=users['parent2'].id,
            title="Black School Shoes",
            description="Durable black school shoes, size 6. Still in good shape.",
            price=180.00,
            uniform_type="School Uniform",
            condition="Used - Good",
            size="Size 6",
            gender="Unisex",
            school_name="Another School",
            location="Pretoria",
            image_file="360_F_1303457674_qFx2gcKhwSCgLe38Imn5QFPWZzAHabSh.jpg", # Example existing image
            listing_type="sale",
            is_premium=False,
            brand="Bata",
            color="Black"
        )
        listing4.save()
        print(f"Created Listing: {listing4.title}")
    else:
        listing4 = Listing.objects(title="Black School Shoes").first()
        print(f"Listing '{listing4.title}' already exists.")
    listings['shoes'] = listing4

    # No db.session.commit() needed here, .save() commits
    return listings

def seed_messages(users, listings):
    """
    Seeds sample messages.
    """
    print("Seeding messages...")
    
    # Message 1: Parent1 to Parent2 about Listing2
    if not Message.objects(sender=users['parent1'].id, receiver=users['parent2'].id, content="Hi, is the red sports shorts still available?").first():
        msg1 = Message(
            sender=users['parent1'].id,
            receiver=users['parent2'].id,
            content="Hi, is the red sports shorts still available?",
            timestamp=datetime.utcnow() - timedelta(hours=5)
        )
        msg1.save()
        print("Created Message 1.")
    else:
        print("Message 1 already exists.")

    # Message 2: Parent2 to Parent1 (reply)
    if not Message.objects(sender=users['parent2'].id, receiver=users['parent1'].id, content="Yes, it is! What size are you looking for?").first():
        msg2 = Message(
            sender=users['parent2'].id,
            receiver=users['parent1'].id,
            content="Yes, it is! What size are you looking for?",
            timestamp=datetime.utcnow() - timedelta(hours=4)
        )
        msg2.save()
        print("Created Message 2.")
    else:
        print("Message 2 already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_swaps(users, listings):
    """
    Seeds sample swap requests.
    """
    print("Seeding swap requests...")

    # Pending Swap: Parent1 offers blazer for Parent2's shorts
    if not SwapRequest.objects(requester=users['parent1'].id, requester_listing=listings['blazer'].id, responder_listing=listings['shorts'].id).first():
        swap1 = SwapRequest(
            requester=users['parent1'].id,
            responder=users['parent2'].id,
            requester_listing=listings['blazer'].id,
            responder_listing=listings['shorts'].id,
            message="Would you be interested in swapping my blazer for your shorts?",
            status="pending",
            requested_date=datetime.utcnow() - timedelta(days=7)
        )
        swap1.save()
        print("Created Pending Swap Request 1.")
    else:
        swap1 = SwapRequest.objects(requester=users['parent1'].id, requester_listing=listings['blazer'].id, responder_listing=listings['shorts'].id).first()
        print("Pending Swap Request 1 already exists.")

    # Completed Swap: Parent2 offers shorts for Parent1's blazer (simulated completed)
    if not SwapRequest.objects(requester=users['parent2'].id, requester_listing=listings['shorts'].id, responder_listing=listings['blazer'].id, status='completed').first():
        swap2 = SwapRequest(
            requester=users['parent2'].id,
            responder=users['parent1'].id,
            requester_listing=listings['shorts'].id,
            responder_listing=listings['blazer'].id,
            message="Let's do the swap!",
            status="completed",
            requested_date=datetime.utcnow() - timedelta(days=10),
            updated_date=datetime.utcnow() - timedelta(days=9)
        )
        swap2.save()
        print("Created Completed Swap Request 2.")
    else:
        swap2 = SwapRequest.objects(requester=users['parent2'].id, requester_listing=listings['shorts'].id, responder_listing=listings['blazer'].id, status='completed').first()
        print("Completed Swap Request 2 already exists.")
    
    # No db.session.commit() needed here, .save() commits

def seed_orders(users, listings):
    """
    Seeds sample orders (sales).
    """
    print("Seeding orders...")

    # Completed Order: Parent1 buys shoes from Parent2
    if not Order.objects(buyer=users['parent1'].id, listing=listings['shoes'].id).first():
        order1 = Order(
            buyer=users['parent1'].id,
            seller=users['parent2'].id,
            listing=listings['shoes'].id,
            price_at_purchase=listings['shoes'].price,
            status="completed",
            order_date=datetime.utcnow() - timedelta(days=15),
            transaction_id_gateway=secrets.token_urlsafe(16),
            payment_gateway="PayFast",
            amount_paid_total=listings['shoes'].price,
            platform_fee=listings['shoes'].price * 0.05,
            seller_payout_amount=listings['shoes'].price * 0.95,
            payout_status="pending"
        )
        order1.save()
        print("Created Order 1 (Sale).")
    else:
        order1 = Order.objects(buyer=users['parent1'].id, listing=listings['shoes'].id).first()
        print("Order 1 (Sale) already exists.")

    # Premium Listing Purchase Order: Parent1 buys premium for their blazer
    if not Order.objects(buyer=users['parent1'].id, premium_listing_ref=listings['blazer'].id, is_premium_listing_purchase=True).first():
        premium_order = Order(
            buyer=users['parent1'].id,
            seller=users['admin'].id, # Platform as seller for premium
            listing=listings['blazer'].id, # This is the listing associated with the purchase
            price_at_purchase=50.00, # Cost of premium package
            status="completed",
            order_date=datetime.utcnow() - timedelta(days=2),
            transaction_id_gateway=secrets.token_urlsafe(16),
            payment_gateway="Stripe",
            amount_paid_total=50.00,
            platform_fee=50.00, # Entire amount is platform fee
            seller_payout_amount=0.0,
            payout_status="paid",
            is_premium_listing_purchase=True,
            premium_listing_ref=listings['blazer'].id # Link to the actual listing made premium
        )
        premium_order.save()
        print("Created Premium Listing Purchase Order.")
    else:
        print("Premium Listing Purchase Order already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_donations(users, listings):
    """
    Seeds sample donation requests.
    """
    print("Seeding donations...")

    # Pending Donation: Parent1 donates shirt to School
    if not Donation.objects(donor=users['parent1'].id, donated_listing=listings['shirt_donation'].id, recipient=users['school'].id).first():
        donation1 = Donation(
            donor=users['parent1'].id,
            donated_listing=listings['shirt_donation'].id,
            recipient=users['school'].id,
            quantity=1,
            estimated_value=80.00,
            status="pending_pickup",
            donation_date=datetime.utcnow() - timedelta(days=20),
            notes="Ready for pickup any weekday afternoon."
        )
        donation1.save()
        print("Created Pending Donation 1.")
    else:
        donation1 = Donation.objects(donor=users['parent1'].id, donated_listing=listings['shirt_donation'].id, recipient=users['school'].id).first()
        print("Pending Donation 1 already exists.")

    # Received Donation: Parent2 donates to NGO (NGO confirms receipt)
    if not Donation.objects(donor=users['parent2'].id, donated_listing=listings['shorts'].id, recipient=users['ngo'].id, status='received').first():
        donation2 = Donation(
            donor=users['parent2'].id,
            donated_listing=listings['shorts'].id,
            recipient=users['ngo'].id,
            quantity=2, # Assume 2 pairs of shorts
            estimated_value=120.00,
            status="received",
            donation_date=datetime.utcnow() - timedelta(days=25),
            updated_date=datetime.utcnow() - timedelta(days=20),
            notes="Received in good condition."
        )
        donation2.save()
        print("Created Received Donation 2.")
    else:
        donation2 = Donation.objects(donor=users['parent2'].id, donated_listing=listings['shorts'].id, recipient=users['ngo'].id, status='received').first()
        print("Received Donation 2 already exists.")

    # Distributed Donation: Parent1 donates to NGO (NGO confirms distributed)
    if not Donation.objects(donor=users['parent1'].id, donated_listing=listings['blazer'].id, recipient=users['ngo'].id, status='distributed').first():
        donation3 = Donation(
            donor=users['parent1'].id,
            donated_listing=listings['blazer'].id,
            recipient=users['ngo'].id,
            quantity=1,
            estimated_value=200.00,
            families_supported=1,
            status="distributed",
            donation_date=datetime.utcnow() - timedelta(days=30),
            updated_date=datetime.utcnow() - timedelta(days=28),
            notes="Distributed to a learner in need."
        )
        donation3.save()
        print("Created Distributed Donation 3.")
    else:
        donation3 = Donation.objects(donor=users['parent1'].id, donated_listing=listings['blazer'].id, recipient=users['ngo'].id, status='distributed').first()
        print("Distributed Donation 3 already exists.")

    # No db.session.commit() needed here, .save() commits
    # Manually update NGO user's aggregated metrics after seeding donations
    # This simulates the logic in the donations blueprint routes
    ngo_user = users['ngo']
    ngo_donations = Donation.objects(recipient=ngo_user.id).all()
    ngo_user.total_donations_received_count = sum(d.quantity for d in ngo_donations if d.status in ['received', 'distributed'])
    ngo_user.total_donations_value = sum(d.estimated_value for d in ngo_donations if d.status in ['received', 'distributed'])
    ngo_user.total_families_supported_ytd = sum(d.families_supported for d in ngo_donations if d.status == 'distributed')
    ngo_user.save() # Save updated user metrics
    print(f"Updated NGO '{ngo_user.username}' impact metrics.")


def seed_logistics(users, orders, swaps, donations):
    """
    Seeds sample logistics records.
    """
    print("Seeding logistics records...")

    # Logistics for Order 1 (Sale) - Parent2 (seller) to Parent1 (buyer)
    order1 = orders[0] # Assuming order1 is the first one created
    if not Logistics.objects(transaction_id=str(order1.id), transaction_type='sale').first():
        logistics1 = Logistics(
            transaction_id=str(order1.id),
            transaction_type='sale',
            sender=users['parent2'].id, # ReferenceField
            receiver=users['parent1'].id, # ReferenceField
            shipping_method='courier',
            status='in_transit',
            courier_name='FastDeliveries',
            tracking_number='FD123456789',
            tracking_url='https://track.fastdeliveries.com/FD123456789',
            pickup_address='123 Seller St, Pretoria',
            delivery_address='456 Buyer Ave, Johannesburg',
            scheduled_pickup_date=datetime.utcnow() - timedelta(days=14),
            actual_pickup_date=datetime.utcnow() - timedelta(days=13),
            scheduled_delivery_date=datetime.utcnow() - timedelta(days=10),
            last_status_update=datetime.utcnow() - timedelta(days=12),
            notes="Item picked up, on its way."
        )
        logistics1.save()
        print("Created Logistics 1 (Sale).")
    else:
        print("Logistics 1 (Sale) already exists.")

    # Logistics for Swap 2 (Completed Swap) - Parent2 to Parent1
    swap2 = swaps[1] # Assuming swap2 is the completed one
    if not Logistics.objects(transaction_id=str(swap2.id), transaction_type='swap').first():
        logistics2 = Logistics(
            transaction_id=str(swap2.id),
            transaction_type='swap',
            sender=users['parent2'].id, # ReferenceField
            receiver=users['parent1'].id, # ReferenceField
            shipping_method='pickup_dropoff',
            status='delivered', # Already delivered
            pudo_location_name='Central Locker',
            pudo_address='789 Locker Rd, City',
            pudo_code='SWAPXYZ',
            scheduled_pickup_date=datetime.utcnow() - timedelta(days=6),
            actual_pickup_date=datetime.utcnow() - timedelta(days=5),
            scheduled_delivery_date=datetime.utcnow() - timedelta(days=4),
            actual_delivery_date=datetime.utcnow() - timedelta(days=4),
            last_status_update=datetime.utcnow() - timedelta(days=4),
            notes="Both items successfully exchanged via PUDO.",
            tracking_number=secrets.token_urlsafe(16)
        )
        logistics2.save()
        print("Created Logistics 2 (Swap).")
    else:
        print("Logistics 2 (Swap) already exists.")

    # Logistics for Donation 2 (Received Donation) - Parent2 to NGO
    donation2 = donations[1] # Assuming donation2 is the received one
    if not Logistics.objects(transaction_id=str(donation2.id), transaction_type='donation').first():
        logistics3 = Logistics(
            transaction_id=str(donation2.id),
            transaction_type='donation',
            sender=users['parent2'].id, # ReferenceField
            receiver=users['ngo'].id, # ReferenceField
            shipping_method='in_person',
            status='delivered', # Item received by NGO
            pickup_address='Parent2 Home',
            delivery_address='NGO Office',
            scheduled_pickup_date=datetime.utcnow() - timedelta(days=24),
            actual_pickup_date=datetime.utcnow() - timedelta(days=23),
            actual_delivery_date=datetime.utcnow() - timedelta(days=23),
            last_status_update=datetime.utcnow() - timedelta(days=23),
            notes="Hand delivered to NGO.",
            tracking_number=secrets.token_urlsafe(16)
        )
        logistics3.save()
        print("Created Logistics 3 (Donation).")
    else:
        print("Logistics 3 (Donation) already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_reviews(users, listings, swaps, orders):
    """
    Seeds sample reviews.
    """
    print("Seeding reviews...")

    # Review 1: Parent1 reviews Parent2 after completed swap (swap2)
    swap2 = swaps[1]
    if not Review.objects(reviewer=users['parent1'].id, reviewed_user=users['parent2'].id, transaction_id=str(swap2.id)).first():
        review1 = Review(
            reviewer=users['parent1'].id,
            reviewed_user=users['parent2'].id,
            comment="Smooth swap, great communication and item was as described!",
            rating=5,
            is_positive=True,
            communication_rating=5,
            logistics_rating=5,
            item_as_described=True,
            transaction_id=str(swap2.id),
            listing=listings['shorts'].id, # ReferenceField
            date_posted=datetime.utcnow() - timedelta(days=4)
        )
        review1.save()
        print("Created Review 1.")
    else:
        print("Review 1 already exists.")

    # Review 2: Parent2 reviews Parent1 after completed swap (swap2)
    if not Review.objects(reviewer=users['parent2'].id, reviewed_user=users['parent1'].id, transaction_id=str(swap2.id)).first():
        review2 = Review(
            reviewer=users['parent2'].id,
            reviewed_user=users['parent1'].id,
            comment="Item received was perfect, easy exchange. Highly recommend!",
            rating=5,
            is_positive=True,
            communication_rating=5,
            logistics_rating=5,
            item_as_described=True,
            transaction_id=str(swap2.id),
            listing=listings['blazer'].id, # ReferenceField
            date_posted=datetime.utcnow() - timedelta(days=4)
        )
        review2.save()
        print("Created Review 2.")
    else:
        print("Review 2 already exists.")

    # Review 3: Parent1 reviews Parent2 after purchase (order1)
    order1 = orders[0]
    if not Review.objects(reviewer=users['parent1'].id, reviewed_user=users['parent2'].id, transaction_id=str(order1.id)).first():
        review3 = Review(
            reviewer=users['parent1'].id,
            reviewed_user=users['parent2'].id,
            comment="Shoes were exactly as described. Quick delivery!",
            rating=4,
            is_positive=True,
            communication_rating=4,
            logistics_rating=5,
            item_as_described=True,
            transaction_id=str(order1.id),
            listing=listings['shoes'].id, # ReferenceField
            date_posted=datetime.utcnow() - timedelta(days=10)
        )
        review3.save()
        print("Created Review 3.")
    else:
        print("Review 3 already exists.")
    
    # No db.session.commit() needed here, .save() commits
    # Update user trust scores after reviews
    for user_obj in users.values():
        print(f"Updating trust score for {user_obj.username}...")
        update_user_trust_score(user_obj.id)
    # No db.session.commit() here, .save() commits within update_user_trust_score_manual



def seed_wishlist_items(users, listings):
    """
    Seeds sample wishlist items.
    """
    print("Seeding wishlist items...")

    # Parent1 wishes for Listing4 (shoes)
    if not WishlistItem.objects(user=users['parent1'].id, listing=listings['shoes'].id).first():
        wishlist1 = WishlistItem(
            user=users['parent1'].id,
            listing=listings['shoes'].id,
            date_added=datetime.utcnow() - timedelta(days=20)
        )
        wishlist1.save()
        print("Created Wishlist Item 1.")
    else:
        print("Wishlist Item 1 already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_saved_searches(users):
    """
    Seeds sample saved searches.
    """
    print("Seeding saved searches...")

    # Parent1 saves a search for school uniforms in Johannesburg
    search_params1 = "uniform_type=School+Uniform&location=Johannesburg"
    if not SavedSearch.objects(user=users['parent1'].id, search_query_params=search_params1).first():
        saved_search1 = SavedSearch(
            user=users['parent1'].id,
            name="School Uniforms JHB",
            search_query_params=search_params1,
            date_saved=datetime.utcnow() - timedelta(days=30)
        )
        saved_search1.save()
        print("Created Saved Search 1.")
    else:
        print("Saved Search 1 already exists.")

    # Parent2 saves a search for red sports kit
    search_params2 = "uniform_type=Sports+Kit&color=Red"
    if not SavedSearch.objects(user=users['parent2'].id, search_query_params=search_params2).first():
        saved_search2 = SavedSearch(
            user=users['parent2'].id,
            name="Red Sports Kit",
            search_query_params=search_params2,
            date_saved=datetime.utcnow() - timedelta(days=40)
        )
        saved_search2.save()
        print("Created Saved Search 2.")
    else:
        print("Saved Search 2 already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_reports(users, listings):
    """
    Seeds sample reports.
    """
    print("Seeding reports...")

    # Report 1: Parent1 reports Listing2 (shorts) for misleading info (simulated)
    if not Report.objects(reporter=users['parent1'].id, reported_entity_type='listing', reported_entity_id=str(listings['shorts'].id)).first():
        report1 = Report(
            reporter=users['parent1'].id,
            reported_entity_type='listing',
            reported_entity_id=str(listings['shorts'].id),
            reason_category='misleading_information',
            description="The description says 'Small' but it looks more like an 'XS'.",
            status='pending',
            date_reported=datetime.utcnow() - timedelta(days=2)
        )
        report1.save()
        print("Created Report 1.")
    else:
        print("Report 1 already exists.")

    # Report 2: Parent2 reports Parent1 for harassment (simulated)
    if not Report.objects(reporter=users['parent2'].id, reported_entity_type='user', reported_entity_id=str(users['parent1'].id)).first():
        report2 = Report(
            reported_entity_type='user',
            reported_entity_id=str(users['parent1'].id),
            reason_category='harassment',
        )
        report2.save()
        print("Created Report 2.")
    else:
        print("Report 2 already exists.")

    # No db.session.commit() needed here, .save() commits

def seed_disputes(users, listings):
    """
    Seeds sample disputes.
    """
    print("Seeding disputes...")

    # Dispute 1: Parent1 disputes Parent2 over shoes purchase (order1)
    # Assuming order1 is the first order created in seed_orders
    order1 = Order.objects(buyer=users['parent1'].id, listing=listings['shoes'].id).first()
    if order1 and not Dispute.objects(initiator=users['parent1'].id, respondent=users['parent2'].id, listing=listings['shoes'].id).first():
        dispute1 = Dispute(
            initiator=users['parent1'].id,
            respondent=users['parent2'].id,
            listing=listings['shoes'].id,
            reason="Shoes received had a tear not mentioned in the description.",
            status='open',
            date_raised=datetime.utcnow() - timedelta(days=8)
        )
        dispute1.save()
        print("Created Dispute 1.")
    else:
        print("Dispute 1 already exists or order not found.")

    # Dispute 2: Parent2 disputes Parent1 over a cancelled swap (simulated)
    # Assume a swap that was cancelled and caused a dispute
    if not Dispute.objects(initiator=users['parent2'].id, respondent=users['parent1'].id, reason="Swap cancelled last minute without explanation.").first():
        dispute2 = Dispute(
            initiator=users['parent2'].id,
            respondent=users['parent1'].id,
            listing=None, # Not directly tied to a specific listing if it's about cancellation
            reason="Swap cancelled last minute without explanation after arrangements were made.",
            status='under review',
            date_raised=datetime.utcnow() - timedelta(days=12)
        )
        dispute2.save()
        print("Created Dispute 2.")
    else:
        print("Dispute 2 already exists.")

    # No db.session.commit() needed here, .save() commits

# Main seeding function
def seed_all_data():
    app = create_app()
    with app.app_context():
        # Optional: Clear existing data before seeding
        clear_all_collections(app) 

        users = seed_users()
        forums = seed_forums() # Seed forums
        listings = seed_listings(users)
        seed_messages(users, listings)
        
        # Need to fetch objects after seeding to ensure they are available for relationships
        # For MongoEngine, objects are usually live, but re-fetching ensures consistency
        swaps_list = list(SwapRequest.objects.all())
        orders_list = list(Order.objects(is_premium_listing_purchase=False).all()) # Only actual sales
        premium_orders_list = list(Order.objects(is_premium_listing_purchase=True).all())
        donations_list = list(Donation.objects.all())

        seed_swaps(users, listings) # Re-run to ensure fresh swap objects if needed by logistics/reviews
        seed_orders(users, listings)
        seed_donations(users, listings)
        
        # Re-fetch lists after all relevant models are seeded to ensure latest state
        swaps_list = list(SwapRequest.objects.all())
        orders_list = list(Order.objects(is_premium_listing_purchase=False).all()) 
        premium_orders_list = list(Order.objects(is_premium_listing_purchase=True).all())
        donations_list = list(Donation.objects.all())

        seed_logistics(users, orders_list, swaps_list, donations_list)
        seed_reviews(users, listings, swaps_list, orders_list)
        seed_wishlist_items(users, listings)
        seed_saved_searches(users)
        seed_reports(users, listings)
        seed_disputes(users, listings)
        
        print("\nDatabase seeding complete! ✨")

if __name__ == "__main__":
    seed_all_data()