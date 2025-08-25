import multiprocessing
import os
from mongoengine import connect
from dotenv import load_dotenv # Import load_dotenv
from app.config import Config # Import Config class

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
bind = "0.0.0.0:$PORT"
accesslog = 'logs/app.log'
errorlog = 'logs/app.log'

def post_fork(server, worker):
    # Load environment variables for the worker process
    load_dotenv()
    # Access config directly from the Config class
    mongo_uri = Config.MONGO_URI

    # Connect to MongoDB directly in the worker process
    connect(host=mongo_uri)
    worker.log.info("MongoDB reconnected in worker process.")
    worker.log.info(f"Attempting to bind to port: {os.environ.get('PORT')}")

