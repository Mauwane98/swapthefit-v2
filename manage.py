print("Starting manage.py script...")
from app import create_app

# Create an application instance
app = create_app()

if __name__ == '__main__':
    # Run the app using Flask's built-in development server.
    # This is for debugging purposes to isolate logging issues.
    # debug=True enables the reloader and debugger.
    print("Attempting to run Flask development server...")
    app.run(debug=True, use_reloader=False, use_debugger=False) 