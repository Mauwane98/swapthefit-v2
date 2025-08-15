from app.extensions import mongo
import datetime
from bson.objectid import ObjectId

class Listing:
    """Listing Model"""

    @staticmethod
    def create(owner_id, title, description, category, school, size, condition, images):
        """Creates and saves a new listing."""
        listing_data = {
            "owner_id": ObjectId(owner_id),
            "title": title,
            "description": description,
            "category": category,
            "school": school,
            "size": size,
            "condition": condition,
            "status": "available",
            "images": images,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        return mongo.db.listings.insert_one(listing_data)

    @staticmethod
    def find_by_owner(owner_id):
        """Finds all listings by a specific owner."""
        return mongo.db.listings.find({"owner_id": ObjectId(owner_id)})

    @staticmethod
    def find_all_available():
        """Finds all listings that are currently available."""
        return mongo.db.listings.find({"status": "available"}).sort("created_at", -1)

    @staticmethod
    def find_by_id(listing_id):
        """Finds a single listing by its ID."""
        return mongo.db.listings.find_one({"_id": ObjectId(listing_id)})

    @staticmethod
    def update(listing_id, data):
        """Updates a listing with new data."""
        data['updated_at'] = datetime.datetime.utcnow()
        return mongo.db.listings.update_one(
            {'_id': ObjectId(listing_id)},
            {'$set': data}
        )

    @staticmethod
    def delete_by_id(listing_id):
        """Deletes a listing by its ID."""
        return mongo.db.listings.delete_one({'_id': ObjectId(listing_id)})
        
    @staticmethod
    def find_all_with_owner_info():
        """
        Finds all listings and joins them with owner information.
        Uses a MongoDB aggregation pipeline for efficiency.
        """
        pipeline = [
            {'$sort': {'created_at': -1}},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'owner_id',
                    'foreignField': '_id',
                    'as': 'owner_info'
                }
            },
            {'$unwind': '$owner_info'}
        ]
        return mongo.db.listings.aggregate(pipeline)
