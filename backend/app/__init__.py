"""
Application Factory
===================
Creates and configures the Flask application instance.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import get_config
from app.extensions import db, migrate, jwt, bcrypt, cors


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(get_config())
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Create upload folder if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    return app


def initialize_extensions(app):
    """
    Initialize Flask extensions.
    
    Args:
        app: Flask application instance
    """
    # Initialize database
    db.init_app(app)
    
    # Initialize migrations
    migrate.init_app(app, db)
    
    # Initialize JWT
    jwt.init_app(app)
    
    # Initialize Bcrypt
    bcrypt.init_app(app)
    
    # Initialize CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired',
            'error': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token',
            'error': 'invalid_token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Authorization token is missing',
            'error': 'authorization_required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has been revoked',
            'error': 'token_revoked'
        }), 401


def register_blueprints(app):
    """
    Register Flask blueprints.
    
    Args:
        app: Flask application instance
    """
    from app.routes import auth_bp, student_bp, admin_bp, dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'success': True,
            'message': 'API is running',
            'status': 'healthy'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'success': True,
            'message': 'University Complaints Management System API',
            'version': '1.0.0',
            'documentation': '/api/docs'
        }), 200


def register_error_handlers(app):
    """
    Register error handlers.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'error': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'message': 'Unauthorized access',
            'error': str(error)
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'message': 'Access forbidden',
            'error': str(error)
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error': str(error)
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': str(error)
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(error)
        }), 500


def register_commands(app):
    """
    Register CLI commands.
    
    Args:
        app: Flask application instance
    """
    
    @app.cli.command('create-db')
    def create_db():
        """Create database tables."""
        db.create_all()
        print('Database tables created successfully!')
    
    @app.cli.command('drop-db')
    def drop_db():
        """Drop all database tables."""
        db.drop_all()
        print('Database tables dropped!')
    
    @app.cli.command('seed-db')
    def seed_db():
        """Seed database with sample data."""
        from app.models import User, Complaint, Response
        
        # Create super admin
        if not User.query.filter_by(email='admin@university.edu.ng').first():
            admin = User(
                email='admin@university.edu.ng',
                full_name='System Administrator',
                role='super_admin',
                department='ICT Department'
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            print('Super admin created: admin@university.edu.ng / Admin@123')
        
        # Create regular admin
        if not User.query.filter_by(email='staff@university.edu.ng').first():
            staff = User(
                email='staff@university.edu.ng',
                full_name='John Adebayo',
                role='admin',
                department='Student Affairs'
            )
            staff.set_password('Staff@123')
            db.session.add(staff)
            print('Admin created: staff@university.edu.ng / Staff@123')
        
        # Create sample student
        if not User.query.filter_by(email='student@university.edu.ng').first():
            student = User(
                email='student@university.edu.ng',
                full_name='Chioma Okonkwo',
                matric_number='UNI/2021/001',
                department='Computer Science',
                faculty='Science',
                role='student',
                phone='08012345678'
            )
            student.set_password('Student@123')
            db.session.add(student)
            print('Student created: student@university.edu.ng / Student@123')
        
        db.session.commit()
        print('Database seeded successfully!')
    
    @app.cli.command('create-admin')
    def create_admin():
        """Create a super admin user interactively."""
        import getpass
        
        print('\n=== Create Super Admin ===\n')
        
        email = input('Email: ').strip()
        full_name = input('Full Name: ').strip()
        password = getpass.getpass('Password: ')
        confirm_password = getpass.getpass('Confirm Password: ')
        
        if password != confirm_password:
            print('Error: Passwords do not match!')
            return
        
        if len(password) < 8:
            print('Error: Password must be at least 8 characters!')
            return
        
        if User.query.filter_by(email=email).first():
            print(f'Error: User with email {email} already exists!')
            return
        
        admin = User(
            email=email,
            full_name=full_name,
            role='super_admin'
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f'\nSuper admin created successfully!')
        print(f'Email: {email}')