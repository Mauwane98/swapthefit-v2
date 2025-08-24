from datetime import datetime
from app.extensions import db
from mongoengine.fields import StringField, DateTimeField, ReferenceField, ListField, IntField

class Forum(db.Document):
    name = StringField(max_length=100, required=True, unique=True)
    description = StringField(max_length=500)
    created_at = DateTimeField(default=datetime.utcnow)
    last_post_at = DateTimeField(default=datetime.utcnow)
    topic_count = IntField(default=0)
    post_count = IntField(default=0)

    meta = {
        'collection': 'forums',
        'indexes': [
            'name',
            'created_at'
        ]
    }

    def __repr__(self):
        return f"<Forum {self.name}>"

class Topic(db.Document):
    title = StringField(max_length=200, required=True)
    forum = ReferenceField(Forum, required=True)
    author = ReferenceField('User', required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    last_post_at = DateTimeField(default=datetime.utcnow)
    post_count = IntField(default=0)
    views = IntField(default=0)

    meta = {
        'collection': 'topics',
        'indexes': [
            'forum',
            'author',
            'created_at',
            'last_post_at'
        ]
    }

    def __repr__(self):
        return f"<Topic {self.title} in {self.forum.name}>"

class Post(db.Document):
    content = StringField(required=True)
    topic = ReferenceField(Topic, required=True)
    author = ReferenceField('User', required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'posts',
        'indexes': [
            'topic',
            'author',
            'created_at'
        ]
    }

    def __repr__(self):
        return f"<Post by {self.author.username} in {self.topic.title}>"
