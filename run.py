import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import app, db

    # Ensure database is created
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # Configure debug mode
    app.config['DEBUG'] = True
    app.config['TESTING'] = True

    # Run the application
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000)

except Exception as e:
    print("Error starting the application:")
    print(traceback.format_exc())
    sys.exit(1)
