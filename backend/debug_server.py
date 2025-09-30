#!/usr/bin/env python3
"""
Debug server that runs in development mode with detailed error messages
Run with: python3 debug_server.py
"""

import os
import sys

# Force development mode for detailed errors
os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    from app import create_app

    print("="*60)
    print("STARTING DEBUG SERVER")
    print("="*60)
    print("Mode: DEVELOPMENT (detailed errors enabled)")
    print("Port: 5000")
    print("Host: 0.0.0.0")
    print("")
    print("Test with:")
    print("  curl -X POST http://localhost:5000/api/orders \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"customer_email\":\"test@gmail.com\",\"package_id\":\"chatgpt_plus_1_month\",\"full_name\":\"Test\",\"phone_number\":\"+628123456789\"}'")
    print("")
    print("="*60)
    print("")

    app = create_app('development')

    # Initialize database
    print("Initializing database...")
    try:
        from models import db
        with app.app_context():
            db.create_all()
            print("✓ Database tables created/verified")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("  Continuing anyway... API will show detailed error")

    print("")
    print("Starting server...")
    print("="*60)
    print("")

    # Run server with debug mode
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid double startup
    )