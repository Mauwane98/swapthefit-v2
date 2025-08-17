from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

class Wishlist:
    """
    Represents an item in a user's wishlist.
    """

    def __init__(self, user_id, listing_id, date_added=None, _id=None):
        self.user_id = user_id
        self.listing_id = listing_id
        self.date_added = date_added or datetime.utcnow()
        if _id:
            self.id = str(_id)
        else:
            self.id = None

    @staticmethod
    def get_by_user_id(user_id):
        wishlist_data = mongo.db.wishlist.find({'user_id': user_id})
        return [Wishlist(**data) for data in wishlist_data]

    def save(self):
        if self.id:
            mongo.db.wishlist.update_one({'_id': ObjectId(self.id)}, {'$set': self.__dict__})
        else:
            result = mongo.db.wishlist.insert_one(self.__dict__)
            self.id = str(result.inserted_id)
            
    @staticmethod
    def remove(user_id, listing_id):
        mongo.db.wishlist.delete_one({'user_id': user_id, 'listing_id': listing_id})


    def __repr__(self):
        return f'<Wishlist {self.user_id} - {self.listing_id}>'