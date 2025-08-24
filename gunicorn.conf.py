import multiprocessing
import os
from mongoengine import connect # Import connect

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'
bind = '0.0.0.0:8000'
accesslog = 'logs/app.log'
errorlog = 'logs/app.log'

def post_fork(server, worker):
    from app import create_app
    from app.config import Config # Import Config to get MONGO_URI

    # Create a temporary app instance to access config
    temp_app = create_app()
    mongo_uri = temp_app.config['MONGO_URI']

    # Connect to MongoDB directly in the worker process
    connect(host=mongo_uri)
    worker.log.info("MongoDB reconnected in worker process.")

