from app.extensions import mongo
import datetime
from bson.objectid import ObjectId

class Message:
    """Message Model"""

    @staticmethod
    def create(sender_id, receiver_id, listing_id, content):
        """Creates and saves a new message."""
        message_data = {
            "sender_id": ObjectId(sender_id),
            "receiver_id": ObjectId(receiver_id),
            "listing_id": ObjectId(listing_id),
            "content": content,
            "is_read": False,
            "created_at": datetime.datetime.utcnow()
        }
        return mongo.db.messages.insert_one(message_data)

    @staticmethod
    def find_by_receiver(receiver_id):
        """Finds all messages sent to a specific user."""
        # This is a complex query that requires joining data from other collections
        # We use an aggregation pipeline to achieve this.
        pipeline = [
            {'$match': {'receiver_id': ObjectId(receiver_id)}},
            {'$sort': {'created_at': -1}},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'sender_id',
                    'foreignField': '_id',
                    'as': 'sender_info'
                }
            },
            {
                '$lookup': {
                    'from': 'listings',
                    'localField': 'listing_id',
                    'foreignField': '_id',
                    'as': 'listing_info'
                }
            },
            {'$unwind': '$sender_info'},
            {'$unwind': '$listing_info'}
        ]
        return mongo.db.messages.aggregate(pipeline)
