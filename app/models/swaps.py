from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

class SwapRequest:
    """
    Represents a swap request between two users for two listings.
    """

    def __init__(self, proposer_id, receiver_id, requested_listing_id, offered_listing_id, status='pending', date_proposed=None, _id=None):
        self.proposer_id = proposer_id
        self.receiver_id = receiver_id
        self.requested_listing_id = requested_listing_id
        self.offered_listing_id = offered_listing_id
        self.status = status
        self.date_proposed = date_proposed or datetime.utcnow()
        if _id:
            self.id = str(_id)
        else:
            self.id = None

    @staticmethod
    def get_by_proposer(user_id):
        swaps_data = mongo.db.swap_requests.find({'proposer_id': user_id})
        return [SwapRequest(**data) for data in swaps_data]

    @staticmethod
    def get_by_receiver(user_id):
        swaps_data = mongo.db.swap_requests.find({'receiver_id': user_id})
        return [SwapRequest(**data) for data in swaps_data]

    def save(self):
        if self.id:
            mongo.db.swap_requests.update_one({'_id': ObjectId(self.id)}, {'$set': self.__dict__})
        else:
            result = mongo.db.swap_requests.insert_one(self.__dict__)
            self.id = str(result.inserted_id)

    def __repr__(self):
        return f'<SwapRequest {self.id} from {self.proposer_id} to {self.receiver_id}>'