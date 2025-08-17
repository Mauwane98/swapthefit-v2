from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

class Notification:
    """
    Represents a notification for a user.
    """

    def __init__(self, message, user_id, link=None, is_read=False, timestamp=None, _id=None):
        self.message = message
        self.is_read = is_read
        self.timestamp = timestamp or datetime.utcnow()
        self.link = link
        self.user_id = user_id
        if _id:
            self.id = str(_id)
        else:
            self.id = None

    @staticmethod
    def get_by_user_id(user_id):
        notifications_data = mongo.db.notifications.find({'user_id': user_id})
        return [Notification(**data) for data in notifications_data]

    def save(self):
        if self.id:
            mongo.db.notifications.update_one({'_id': ObjectId(self.id)}, {'$set': self.__dict__})
        else:
            result = mongo.db.notifications.insert_one(self.__dict__)
            self.id = str(result.inserted_id)
            
    @staticmethod
    def mark_as_read(notification_id):
        mongo.db.notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'is_read': True}})

    @staticmethod
    def count_unread(user_id):
        return mongo.db.notifications.count_documents({'user_id': user_id, 'is_read': False})

    def __repr__(self):
        return f'<Notification {self.message}>'