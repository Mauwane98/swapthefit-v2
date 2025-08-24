from flask import Flask
from flask_mongoengine import MongoEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
import mongomock

app.config['MONGODB_SETTINGS'] = {
    'db': 'testdb',
    'mongo_client_class': mongomock.MongoClient,
    'alias': 'default',
}

db = MongoEngine(app)

from flask_wtf import FlaskForm
from wtforms import StringField

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
import mongomock

app.config['MONGODB_SETTINGS'] = {
    'db': 'testdb',
    'mongo_client_class': mongomock.MongoClient,
    'alias': 'default',
}

db = MongoEngine(app)

class User(db.Document):
    name = db.StringField()
    email = db.StringField()
    # The following line causes the error
    from mongoengine.fields import ReferenceField
from wtforms import StringField

class MyForm(FlaskForm):
    name = StringField('Name')

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    try:
        with app.app_context():
            User.drop_collection()
            User(name='test', email='test@example.com').save()
        print("App initialized successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
