"""
API Routes Package
==================
This package contains all API route blueprints.
"""

from flask import Blueprint

# Create blueprints with URL prefixes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Import route handlers (this registers the routes with blueprints)
from app.routes import auth
from app.routes import student
from app.routes import admin
from app.routes import dashboard

# Export blueprints
__all__ = ['auth_bp', 'student_bp', 'admin_bp', 'dashboard_bp']