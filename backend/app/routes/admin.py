"""
Admin Routes
============
Handles admin-specific operations like managing complaints and users.
"""

from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes import admin_bp
from app.models import User, Complaint, Response, Notification
from app.extensions import db
from app.utils.helpers import (
    validate_required_fields,
    create_success_response,
    create_error_response,
    sanitize_string,
    paginate_query,
    get_pagination_info
)


def get_current_admin():
    """
    Helper function to get current admin user.
    
    Returns:
        tuple: (user, error_response) - user if valid admin, error_response if not
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return None, create_error_response("User not found", status_code=404)
    
    if not user.is_active:
        return None, create_error_response("Account is deactivated", status_code=403)
    
    if not user.is_admin():
        return None, create_error_response(
            "Access denied. Admin privileges required.",
            status_code=403
        )
    
    return user, None


# ==================== COMPLAINT MANAGEMENT ====================

@admin_bp.route('/complaints', methods=['GET'])
@jwt_required()
def get_all_complaints():
    """
    Get all complaints with filtering, searching, and pagination.
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10, max: 100)
        - status: Filter by status
        - category: Filter by category
        - priority: Filter by priority
        - assigned_to: Filter by assigned admin ID
        - unassigned: Show only unassigned complaints (true/false)
        - search: Search in title, description, ticket number
        - start_date: Filter by start date (YYYY-MM-DD)
        - end_date: Filter by end date (YYYY-MM-DD)
        - sort_by: Sort field
        - sort_order: Sort order (asc, desc)
        
    Returns:
        JSON response with paginated complaints
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        # Build query
        query = Complaint.query
        
        # Apply filters
        status = request.args.get('status')
        if status and status in Complaint.VALID_STATUSES:
            query = query.filter_by(status=status)
        
        category = request.args.get('category')
        if category and category in Complaint.VALID_CATEGORIES:
            query = query.filter_by(category=category)
        
        priority = request.args.get('priority')
        if priority and priority in Complaint.VALID_PRIORITIES:
            query = query.filter_by(priority=priority)
        
        # Filter by assignment
        assigned_to = request.args.get('assigned_to', type=int)
        if assigned_to:
            query = query.filter_by(assigned_to=assigned_to)
        
        unassigned = request.args.get('unassigned', '').lower() == 'true'
        if unassigned:
            query = query.filter(Complaint.assigned_to.is_(None))
        
        # Date range filter
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Complaint.created_at >= start)
            except ValueError:
                pass
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                # Add one day to include the end date
                end = end.replace(hour=23, minute=59, second=59)
                query = query.filter(Complaint.created_at <= end)
            except ValueError:
                pass
        
        # Search
        search = request.args.get('search', '').strip()
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Complaint.title.ilike(search_term),
                    Complaint.description.ilike(search_term),
                    Complaint.ticket_number.ilike(search_term)
                )
            )
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        valid_sort_fields = ['created_at', 'updated_at', 'status', 'priority', 'category']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        sort_column = getattr(Complaint, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = paginate_query(query, page=page, per_page=per_page)
        
        complaints = [c.to_dict(include_responses=False) for c in pagination.items]
        
        return create_success_response(
            data={
                'complaints': complaints,
                'pagination': get_pagination_info(pagination)
            },
            message="Complaints retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve complaints: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>', methods=['GET'])
@jwt_required()
def get_complaint_details(complaint_id):
    """
    Get detailed information about a specific complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Returns:
        JSON response with complaint details including all responses
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        # Get all responses (including internal notes for admins)
        responses = Response.query.filter_by(
            complaint_id=complaint_id
        ).order_by(Response.created_at.asc()).all()
        
        complaint_data = complaint.to_dict(include_responses=False)
        complaint_data['responses'] = [r.to_dict() for r in responses]
        complaint_data['admin_notes'] = complaint.admin_notes
        
        return create_success_response(
            data={'complaint': complaint_data},
            message="Complaint retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve complaint: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>/status', methods=['PUT'])
@jwt_required()
def update_complaint_status(complaint_id):
    """
    Update the status of a complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - status: New status (required)
        - comment: Optional comment explaining the status change
        
    Returns:
        JSON response with updated complaint
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        data = request.get_json()
        
        if not data or 'status' not in data:
            return create_error_response("Status is required", status_code=400)
        
        new_status = sanitize_string(data['status'].lower(), 20)
        
        if new_status not in Complaint.VALID_STATUSES:
            return create_error_response(
                f"Invalid status. Valid options: {', '.join(Complaint.VALID_STATUSES)}",
                status_code=400
            )
        
        old_status = complaint.status
        
        # Update status
        if not complaint.update_status(new_status):
            return create_error_response("Failed to update status", status_code=400)
        
        # Add comment as response if provided
        comment = sanitize_string(data.get('comment'), 2000)
        if comment:
            response = Response(
                complaint_id=complaint_id,
                user_id=admin.id,
                message=f"Status changed from '{old_status}' to '{new_status}'. {comment}",
                is_internal=False
            )
            db.session.add(response)
        
        db.session.commit()
        
        # Notify student
        Notification.create_notification(
            user_id=complaint.user_id,
            notification_type='status_changed',
            title=f'Complaint Status Updated',
            message=f'Your complaint "{complaint.title}" status changed to {new_status.upper()}.',
            complaint_id=complaint.id
        )
        db.session.commit()
        
        return create_success_response(
            data={'complaint': complaint.to_dict()},
            message=f"Status updated to '{new_status}'"
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update status: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>/priority', methods=['PUT'])
@jwt_required()
def update_complaint_priority(complaint_id):
    """
    Update the priority of a complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - priority: New priority level (required)
        
    Returns:
        JSON response with updated complaint
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        data = request.get_json()
        
        if not data or 'priority' not in data:
            return create_error_response("Priority is required", status_code=400)
        
        new_priority = sanitize_string(data['priority'].lower(), 20)
        
        if new_priority not in Complaint.VALID_PRIORITIES:
            return create_error_response(
                f"Invalid priority. Valid options: {', '.join(Complaint.VALID_PRIORITIES)}",
                status_code=400
            )
        
        complaint.priority = new_priority
        db.session.commit()
        
        return create_success_response(
            data={'complaint': complaint.to_dict()},
            message=f"Priority updated to '{new_priority}'"
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update priority: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>/assign', methods=['PUT'])
@jwt_required()
def assign_complaint(complaint_id):
    """
    Assign a complaint to an admin.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - admin_id: ID of the admin to assign (required, use null to unassign)
        
    Returns:
        JSON response with updated complaint
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        data = request.get_json()
        
        if data is None:
            return create_error_response("No data provided", status_code=400)
        
        admin_id = data.get('admin_id')
        
        if admin_id is not None:
            # Verify the admin exists and is an admin
            assigned_admin = User.query.get(admin_id)
            
            if not assigned_admin:
                return create_error_response("Admin not found", status_code=404)
            
            if not assigned_admin.is_admin():
                return create_error_response(
                    "Can only assign to admin users",
                    status_code=400
                )
            
            complaint.assigned_to = admin_id
            
            # Notify assigned admin
            Notification.create_notification(
                user_id=admin_id,
                notification_type='complaint_assigned',
                title='New Complaint Assigned',
                message=f'Complaint "{complaint.title}" has been assigned to you.',
                complaint_id=complaint.id
            )
            
            message = f"Complaint assigned to {assigned_admin.full_name}"
        else:
            complaint.assigned_to = None
            message = "Complaint unassigned"
        
        db.session.commit()
        
        return create_success_response(
            data={'complaint': complaint.to_dict()},
            message=message
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to assign complaint: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>/responses', methods=['POST'])
@jwt_required()
def add_admin_response(complaint_id):
    """
    Add an admin response to a complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - message: Response message (required)
        - is_internal: Whether this is an internal note (optional, default: false)
        
    Returns:
        JSON response with created response
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        message = sanitize_string(data.get('message'), 5000)
        if not message or len(message) < 2:
            return create_error_response(
                "Message is required",
                status_code=400
            )
        
        is_internal = data.get('is_internal', False)
        
        response = Response(
            complaint_id=complaint_id,
            user_id=admin.id,
            message=message,
            is_internal=is_internal
        )
        
        db.session.add(response)
        
        # If status is pending, change to in_progress
        if complaint.status == 'pending':
            complaint.status = 'in_progress'
        
        db.session.commit()
        
        # Notify student (only for non-internal responses)
        if not is_internal:
            Notification.create_notification(
                user_id=complaint.user_id,
                notification_type='new_response',
                title='New Response on Your Complaint',
                message=f'Admin responded to your complaint "{complaint.title}".',
                complaint_id=complaint.id
            )
            db.session.commit()
        
        return create_success_response(
            data={'response': response.to_dict()},
            message="Response added successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to add response: {str(e)}",
            status_code=500
        )


@admin_bp.route('/complaints/<int:complaint_id>/notes', methods=['PUT'])
@jwt_required()
def update_admin_notes(complaint_id):
    """
    Update internal admin notes for a complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - notes: Internal notes (required)
        
    Returns:
        JSON response with updated complaint
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        complaint.admin_notes = sanitize_string(data.get('notes'), 5000)
        db.session.commit()
        
        return create_success_response(
            data={'complaint': complaint.to_dict()},
            message="Notes updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update notes: {str(e)}",
            status_code=500
        )


# ==================== USER MANAGEMENT (Super Admin Only) ====================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Get all users with filtering and pagination (Super Admin only).
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10)
        - role: Filter by role
        - is_active: Filter by active status
        - search: Search by name, email, matric number
        
    Returns:
        JSON response with paginated users
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        if not admin.is_super_admin():
            return create_error_response(
                "Access denied. Super admin privileges required.",
                status_code=403
            )
        
        query = User.query
        
        # Filter by role
        role = request.args.get('role')
        if role and role in User.VALID_ROLES:
            query = query.filter_by(role=role)
        
        # Filter by active status
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            query = query.filter_by(is_active=is_active)
        
        # Search
        search = request.args.get('search', '').strip()
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.matric_number.ilike(search_term)
                )
            )
        
        query = query.order_by(User.created_at.desc())
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = paginate_query(query, page=page, per_page=per_page)
        
        users = [u.to_dict() for u in pagination.items]
        
        return create_success_response(
            data={
                'users': users,
                'pagination': get_pagination_info(pagination)
            },
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve users: {str(e)}",
            status_code=500
        )


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    """
    Get detailed information about a user (Super Admin only).
    
    Path Parameters:
        - user_id: ID of the user
        
    Returns:
        JSON response with user details
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        if not admin.is_super_admin():
            return create_error_response(
                "Access denied. Super admin privileges required.",
                status_code=403
            )
        
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response("User not found", status_code=404)
        
        # Get user statistics
        complaints_count = Complaint.query.filter_by(user_id=user_id).count()
        
        user_data = user.to_dict()
        user_data['complaints_count'] = complaints_count
        
        return create_success_response(
            data={'user': user_data},
            message="User retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve user: {str(e)}",
            status_code=500
        )


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['PUT'])
@jwt_required()
def toggle_user_active(user_id):
    """
    Activate or deactivate a user account (Super Admin only).
    
    Path Parameters:
        - user_id: ID of the user
        
    Returns:
        JSON response with updated user
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        if not admin.is_super_admin():
            return create_error_response(
                "Access denied. Super admin privileges required.",
                status_code=403
            )
        
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response("User not found", status_code=404)
        
        # Prevent deactivating yourself
        if user.id == admin.id:
            return create_error_response(
                "Cannot deactivate your own account",
                status_code=400
            )
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        
        return create_success_response(
            data={'user': user.to_dict()},
            message=f"User {status} successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update user: {str(e)}",
            status_code=500
        )


@admin_bp.route('/admins', methods=['GET'])
@jwt_required()
def get_admin_list():
    """
    Get list of all admin users (for assignment dropdown).
    
    Returns:
        JSON response with list of admins
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        admins = User.query.filter(
            User.role.in_(['admin', 'super_admin']),
            User.is_active == True
        ).order_by(User.full_name.asc()).all()
        
        admin_list = [
            {
                'id': a.id,
                'full_name': a.full_name,
                'email': a.email,
                'role': a.role
            }
            for a in admins
        ]
        
        return create_success_response(
            data={'admins': admin_list},
            message="Admins retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve admins: {str(e)}",
            status_code=500
        )