from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

class Review:
    """
    Represents a review given by one user to another.
    """

    def __init__(self, rating, reviewer_id, reviewed_user_id, comment=None, date_posted=None, _id=None):
        self.rating = rating
        self.comment = comment
        self.date_posted = date_posted or datetime.utcnow()
        self.reviewer_id = reviewer_id
        self.reviewed_user_id = reviewed_user_id
        if _id:
            self.id = str(_id)
        else:
            self.id = None

    @staticmethod
    def get_by_reviewed_user(user_id):
        reviews_data = mongo.db.reviews.find({'reviewed_user_id': user_id})
        return [Review(**data) for data in reviews_data]

    @staticmethod
    def get_average_rating(user_id):
        pipeline = [
            {'$match': {'reviewed_user_id': user_id}},
            {'$group': {'_id': None, 'averageRating': {'$avg': '$rating'}}}
        ]
        result = list(mongo.db.reviews.aggregate(pipeline))
        return result[0]['averageRating'] if result else 0

    @staticmethod
    def has_reviewed(reviewer_id, reviewed_user_id):
        return mongo.db.reviews.find_one({'reviewer_id': reviewer_id, 'reviewed_user_id': reviewed_user_id}) is not None

    def save(self):
        if self.id:
            mongo.db.reviews.update_one({'_id': ObjectId(self.id)}, {'$set': self.__dict__})
        else:
            result = mongo.db.reviews.insert_one(self.__dict__)
            self.id = str(result.inserted_id)

    def __repr__(self):
        return f'<Review {self.reviewer_id} -> {self.reviewed_user_id}: {self.rating} stars>'