import multiprocessing
import os

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'
bind = '0.0.0.0:8000'
accesslog = 'logs/app.log'
errorlog = 'logs/app.log'

def post_fork(server, worker):
    # Import the create_app function and initialize the app within the worker
    # This ensures that the app context and extensions are properly set up
    # for each worker process after forking.
    from app import create_app
    from app.extensions import db

    # Create a dummy app instance to get the app context
    # This is a common pattern to ensure extensions are initialized post-fork
    # without re-creating the entire app instance.
    app = create_app()
    with app.app_context():
        db.init_app(app) # Initialize MongoEngine here
    worker.log.info("MongoEngine initialized in worker process.")

