import eventlet
eventlet.monkey_patch(all=True)

from app import create_app

app = create_app()
