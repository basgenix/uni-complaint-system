"""
Helper Functions
================
Contains utility functions used throughout the application.
"""

import re
from datetime import datetime
from flask import request, jsonify


def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object to string.
    
    Args:
        dt: Datetime object
        format_string: Format string
        
    Returns:
        str: Formatted datetime string or None
    """
    if dt is None:
        return None
    return dt.strftime(format_string)


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 120:
        return False, "Email must be less than 120 characters"
    
    return True, None


def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def paginate_query(query, page=1, per_page=10, max_per_page=100):
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page
        
    Returns:
        Pagination: SQLAlchemy pagination object
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Ensure per_page is within bounds
    per_page = min(max(1, per_page), max_per_page)
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_pagination_info(pagination):
    """
    Extract pagination information.
    
    Args:
        pagination: SQLAlchemy pagination object
        
    Returns:
        dict: Pagination information
    """
    return {
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'total_items': pagination.total,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'next_page': pagination.next_num if pagination.has_next else None,
        'prev_page': pagination.prev_num if pagination.has_prev else None
    }


def get_request_pagination():
    """
    Get pagination parameters from request.
    
    Returns:
        tuple: (page, per_page)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return page, per_page


def create_success_response(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def create_error_response(message="An error occurred", errors=None, status_code=400):
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: Additional error details
        status_code: HTTP status code
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': False,
        'message': message
    }
    
    if errors is not None:
        response['errors'] = errors
    
    return jsonify(response), status_code


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    if not data:
        return False, required_fields
    
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing.append(field)
    
    return len(missing) == 0, missing


def sanitize_string(value, max_length=None):
    """
    Sanitize a string value.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    if value is None:
        return None
    
    # Convert to string and strip whitespace
    value = str(value).strip()
    
    # Truncate if necessary
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value