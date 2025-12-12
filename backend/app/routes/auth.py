"""
Authentication Routes
=====================
Handles user registration, login, logout, and profile management.
"""

from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app.routes import auth_bp
from app.models import User
from app.extensions import db
from app.utils.helpers import (
    validate_email,
    validate_password,
    validate_required_fields,
    create_success_response,
    create_error_response,
    sanitize_string
)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new student account.
    
    Request Body:
        - email: User email (required)
        - password: User password (required)
        - full_name: User's full name (required)
        - matric_number: Student matric number (required)
        - department: Student's department (required)
        - faculty: Student's faculty (optional)
        - phone: Phone number (optional)
        
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'matric_number', 'department']
        is_valid, missing = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return create_error_response(
                f"Missing required fields: {', '.join(missing)}",
                status_code=400
            )
        
        # Validate email
        email_valid, email_error = validate_email(data['email'])
        if not email_valid:
            return create_error_response(email_error, status_code=400)
        
        # Validate password
        password_valid, password_error = validate_password(data['password'])
        if not password_valid:
            return create_error_response(password_error, status_code=400)
        
        # Sanitize inputs
        email = sanitize_string(data['email'].lower(), 120)
        full_name = sanitize_string(data['full_name'], 100)
        matric_number = sanitize_string(data['matric_number'].upper(), 30)
        department = sanitize_string(data['department'], 100)
        faculty = sanitize_string(data.get('faculty'), 100)
        phone = sanitize_string(data.get('phone'), 20)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return create_error_response(
                "An account with this email already exists",
                status_code=409
            )
        
        # Check if matric number already exists
        if User.query.filter_by(matric_number=matric_number).first():
            return create_error_response(
                "An account with this matric number already exists",
                status_code=409
            )
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            matric_number=matric_number,
            department=department,
            faculty=faculty,
            phone=phone,
            role='student'
        )
        user.set_password(data['password'])
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return create_success_response(
            data={
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            },
            message="Registration successful",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Registration failed: {str(e)}",
            status_code=500
        )


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return tokens.
    
    Request Body:
        - email: User email (required)
        - password: User password (required)
        
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate required fields
        is_valid, missing = validate_required_fields(data, ['email', 'password'])
        if not is_valid:
            return create_error_response(
                f"Missing required fields: {', '.join(missing)}",
                status_code=400
            )
        
        email = sanitize_string(data['email'].lower(), 120)
        password = data['password']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            return create_error_response(
                "Invalid email or password",
                status_code=401
            )
        
        # Check if account is active
        if not user.is_active:
            return create_error_response(
                "Your account has been deactivated. Please contact support.",
                status_code=403
            )
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return create_success_response(
            data={
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            },
            message="Login successful"
        )
        
    except Exception as e:
        return create_error_response(
            f"Login failed: {str(e)}",
            status_code=500
        )


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current logged-in user's profile.
    
    Returns:
        JSON response with user data
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response("User not found", status_code=404)
        
        if not user.is_active:
            return create_error_response(
                "Your account has been deactivated",
                status_code=403
            )
        
        return create_success_response(data={'user': user.to_dict()})
        
    except Exception as e:
        return create_error_response(
            f"Failed to get user: {str(e)}",
            status_code=500
        )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Refresh access token using refresh token.
    
    Returns:
        JSON response with new access token
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return create_error_response(
                "Invalid or inactive user",
                status_code=401
            )
        
        access_token = create_access_token(identity=user_id)
        
        return create_success_response(
            data={'access_token': access_token},
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Token refresh failed: {str(e)}",
            status_code=500
        )


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update current user's profile.
    
    Request Body:
        - full_name: User's full name (optional)
        - department: User's department (optional)
        - faculty: User's faculty (optional)
        - phone: Phone number (optional)
        
    Returns:
        JSON response with updated user data
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response("User not found", status_code=404)
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Update allowed fields only
        if 'full_name' in data and data['full_name']:
            user.full_name = sanitize_string(data['full_name'], 100)
        
        if 'department' in data:
            user.department = sanitize_string(data['department'], 100)
        
        if 'faculty' in data:
            user.faculty = sanitize_string(data['faculty'], 100)
        
        if 'phone' in data:
            user.phone = sanitize_string(data['phone'], 20)
        
        db.session.commit()
        
        return create_success_response(
            data={'user': user.to_dict()},
            message="Profile updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Profile update failed: {str(e)}",
            status_code=500
        )


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user's password.
    
    Request Body:
        - current_password: Current password (required)
        - new_password: New password (required)
        
    Returns:
        JSON response with success message
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response("User not found", status_code=404)
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate required fields
        is_valid, missing = validate_required_fields(
            data, 
            ['current_password', 'new_password']
        )
        if not is_valid:
            return create_error_response(
                f"Missing required fields: {', '.join(missing)}",
                status_code=400
            )
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return create_error_response(
                "Current password is incorrect",
                status_code=400
            )
        
        # Validate new password
        password_valid, password_error = validate_password(data['new_password'])
        if not password_valid:
            return create_error_response(password_error, status_code=400)
        
        # Check that new password is different
        if data['current_password'] == data['new_password']:
            return create_error_response(
                "New password must be different from current password",
                status_code=400
            )
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return create_success_response(message="Password changed successfully")
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Password change failed: {str(e)}",
            status_code=500
        )


@auth_bp.route('/register-admin', methods=['POST'])
@jwt_required()
def register_admin():
    """
    Register a new admin account (Super Admin only).
    
    Request Body:
        - email: Admin email (required)
        - password: Admin password (required)
        - full_name: Admin's full name (required)
        - role: Admin role - 'admin' or 'super_admin' (required)
        - department: Admin's department (optional)
        - phone: Phone number (optional)
        
    Returns:
        JSON response with admin user data
    """
    try:
        # Check if current user is super admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_super_admin():
            return create_error_response(
                "Only super admins can create admin accounts",
                status_code=403
            )
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'role']
        is_valid, missing = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return create_error_response(
                f"Missing required fields: {', '.join(missing)}",
                status_code=400
            )
        
        # Validate role
        if data['role'] not in ['admin', 'super_admin']:
            return create_error_response(
                "Role must be 'admin' or 'super_admin'",
                status_code=400
            )
        
        # Validate email
        email_valid, email_error = validate_email(data['email'])
        if not email_valid:
            return create_error_response(email_error, status_code=400)
        
        # Validate password
        password_valid, password_error = validate_password(data['password'])
        if not password_valid:
            return create_error_response(password_error, status_code=400)
        
        # Sanitize inputs
        email = sanitize_string(data['email'].lower(), 120)
        full_name = sanitize_string(data['full_name'], 100)
        department = sanitize_string(data.get('department'), 100)
        phone = sanitize_string(data.get('phone'), 20)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return create_error_response(
                "An account with this email already exists",
                status_code=409
            )
        
        # Create admin user
        admin = User(
            email=email,
            full_name=full_name,
            department=department,
            phone=phone,
            role=data['role'],
            matric_number=None  # Admins don't have matric numbers
        )
        admin.set_password(data['password'])
        
        # Save to database
        db.session.add(admin)
        db.session.commit()
        
        return create_success_response(
            data={'user': admin.to_dict()},
            message=f"{data['role'].replace('_', ' ').title()} account created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Admin registration failed: {str(e)}",
            status_code=500
        )