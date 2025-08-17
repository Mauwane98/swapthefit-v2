from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

class Listing:
    """
    Represents a school item listing in the marketplace.
    """

    def __init__(self, item_name, description, price, size, condition, school_name, user_id, image_url=None, date_posted=None, _id=None):
        self.item_name = item_name
        self.description = description
        self.price = price
        self.size = size
        self.condition = condition
        self.school_name = school_name
        self.image_url = image_url
        self.date_posted = date_posted or datetime.utcnow()
        self.user_id = user_id
        if _id:
            self.id = str(_id)
        else:
            self.id = None

    @staticmethod
    def get_all():
        listings_data = mongo.db.listings.find()
        return [Listing(**data) for data in listings_data]

    @staticmethod
    def get_by_id(listing_id):
        listing_data = mongo.db.listings.find_one({'_id': ObjectId(listing_id)})
        if listing_data:
            return Listing(**listing_data)
        return None

    @staticmethod
    def get_by_user_id(user_id):
        listings_data = mongo.db.listings.find({'user_id': user_id}).sort('date_posted', -1)
        return [Listing(**data) for data in listings_data]

    def save(self):
        if self.id:
            mongo.db.listings.update_one({'_id': ObjectId(self.id)}, {'$set': self.__dict__})
        else:
            result = mongo.db.listings.insert_one(self.__dict__)
            self.id = str(result.inserted_id)

    def delete(self):
        mongo.db.listings.delete_one({'_id': ObjectId(self.id)})

    def __repr__(self):
        return f"Listing('{self.item_name}', '{self.date_posted}')"