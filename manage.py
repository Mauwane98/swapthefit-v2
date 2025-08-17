from app import create_app
from app.extensions import socketio # Import the SocketIO instance

# Create an application instance
app = create_app()

if __name__ == '__main__':
    # Run the app using SocketIO's run method.
    # This is crucial for enabling WebSocket functionality.
    # debug=True allows for automatic reloader and debugging features.
    # allow_unsafe_werkzeug=True is sometimes needed in development environments
    # when using eventlet/gevent with Werkzeug's reloader.
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
