"""
Application Entry Point
=======================
This file is the entry point for running the Flask application.
"""

import os
from app import create_app
from app.extensions import db

# Create the application instance
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """
    Add objects to the Flask shell context.
    This allows you to access these objects directly in 'flask shell'.
    """
    from app.models import User, Complaint, Response, Notification
    return {
        'db': db,
        'User': User,
        'Complaint': Complaint,
        'Response': Response,
        'Notification': Notification
    }


if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )