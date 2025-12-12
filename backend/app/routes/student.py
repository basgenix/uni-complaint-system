"""
Student Routes
==============
Handles student-specific operations like submitting and tracking complaints.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes import student_bp
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


def get_current_student():
    """
    Helper function to get current student user.
    
    Returns:
        tuple: (user, error_response) - user if valid, error_response if not
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return None, create_error_response("User not found", status_code=404)
    
    if not user.is_active:
        return None, create_error_response("Account is deactivated", status_code=403)
    
    if user.role != 'student':
        return None, create_error_response(
            "Access denied. This endpoint is for students only.",
            status_code=403
        )
    
    return user, None


@student_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    Get all available complaint categories.
    
    Returns:
        JSON response with list of categories
    """
    categories = [
        {'value': key, 'label': value}
        for key, value in Complaint.CATEGORY_DISPLAY.items()
    ]
    
    return create_success_response(
        data={'categories': categories},
        message="Categories retrieved successfully"
    )


@student_bp.route('/priorities', methods=['GET'])
@jwt_required()
def get_priorities():
    """
    Get all available priority levels.
    
    Returns:
        JSON response with list of priorities
    """
    priorities = [
        {'value': key, 'label': value}
        for key, value in Complaint.PRIORITY_DISPLAY.items()
    ]
    
    return create_success_response(
        data={'priorities': priorities},
        message="Priorities retrieved successfully"
    )


@student_bp.route('/complaints', methods=['GET'])
@jwt_required()
def get_my_complaints():
    """
    Get all complaints for current student with filtering and pagination.
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10, max: 100)
        - status: Filter by status
        - category: Filter by category
        - priority: Filter by priority
        - search: Search in title and description
        - sort_by: Sort field (created_at, updated_at, status, priority)
        - sort_order: Sort order (asc, desc)
        
    Returns:
        JSON response with paginated complaints
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Build query
        query = Complaint.query.filter_by(user_id=user.id)
        
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
        
        valid_sort_fields = ['created_at', 'updated_at', 'status', 'priority']
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
        
        # Prepare response
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


@student_bp.route('/complaints', methods=['POST'])
@jwt_required()
def create_complaint():
    """
    Create a new complaint.
    
    Request Body:
        - category: Complaint category (required)
        - title: Complaint title (required)
        - description: Detailed description (required)
        - priority: Priority level (optional, default: medium)
        
    Returns:
        JSON response with created complaint
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['category', 'title', 'description']
        is_valid, missing = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return create_error_response(
                f"Missing required fields: {', '.join(missing)}",
                status_code=400
            )
        
        # Validate category
        category = sanitize_string(data['category'].lower(), 50)
        if category not in Complaint.VALID_CATEGORIES:
            return create_error_response(
                f"Invalid category. Valid options: {', '.join(Complaint.VALID_CATEGORIES)}",
                status_code=400
            )
        
        # Validate title
        title = sanitize_string(data['title'], 200)
        if not title or len(title) < 5:
            return create_error_response(
                "Title must be at least 5 characters long",
                status_code=400
            )
        
        # Validate description
        description = sanitize_string(data['description'], 5000)
        if not description or len(description) < 20:
            return create_error_response(
                "Description must be at least 20 characters long",
                status_code=400
            )
        
        # Validate priority (optional)
        priority = sanitize_string(data.get('priority', 'medium').lower(), 20)
        if priority not in Complaint.VALID_PRIORITIES:
            priority = 'medium'
        
        # Create complaint
        complaint = Complaint(
            user_id=user.id,
            category=category,
            title=title,
            description=description,
            priority=priority,
            status='pending'
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        # Create notification for the student
        Notification.create_notification(
            user_id=user.id,
            notification_type='complaint_submitted',
            title='Complaint Submitted Successfully',
            message=f'Your complaint "{title}" has been submitted. Ticket: {complaint.ticket_number}',
            complaint_id=complaint.id
        )
        db.session.commit()
        
        return create_success_response(
            data={'complaint': complaint.to_dict()},
            message=f"Complaint submitted successfully. Your ticket number is {complaint.ticket_number}",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to create complaint: {str(e)}",
            status_code=500
        )


@student_bp.route('/complaints/<int:complaint_id>', methods=['GET'])
@jwt_required()
def get_complaint_details(complaint_id):
    """
    Get detailed information about a specific complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Returns:
        JSON response with complaint details and responses
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Get complaint
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        # Check ownership
        if complaint.user_id != user.id:
            return create_error_response(
                "Access denied. You can only view your own complaints.",
                status_code=403
            )
        
        # Get responses (excluding internal notes)
        responses = Response.query.filter_by(
            complaint_id=complaint_id,
            is_internal=False
        ).order_by(Response.created_at.asc()).all()
        
        complaint_data = complaint.to_dict(include_responses=False)
        complaint_data['responses'] = [r.to_dict() for r in responses]
        
        return create_success_response(
            data={'complaint': complaint_data},
            message="Complaint retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve complaint: {str(e)}",
            status_code=500
        )


@student_bp.route('/complaints/<int:complaint_id>/responses', methods=['POST'])
@jwt_required()
def add_response_to_complaint(complaint_id):
    """
    Add a response/comment to a complaint.
    
    Path Parameters:
        - complaint_id: ID of the complaint
        
    Request Body:
        - message: Response message (required)
        
    Returns:
        JSON response with created response
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Get complaint
        complaint = Complaint.query.get(complaint_id)
        
        if not complaint:
            return create_error_response("Complaint not found", status_code=404)
        
        # Check ownership
        if complaint.user_id != user.id:
            return create_error_response(
                "Access denied. You can only respond to your own complaints.",
                status_code=403
            )
        
        # Check if complaint is closed or rejected
        if complaint.status in ['closed', 'rejected']:
            return create_error_response(
                "Cannot add response to a closed or rejected complaint.",
                status_code=400
            )
        
        data = request.get_json()
        
        if not data:
            return create_error_response("No data provided", status_code=400)
        
        # Validate message
        message = sanitize_string(data.get('message'), 5000)
        if not message or len(message) < 5:
            return create_error_response(
                "Message must be at least 5 characters long",
                status_code=400
            )
        
        # Create response
        response = Response(
            complaint_id=complaint_id,
            user_id=user.id,
            message=message,
            is_internal=False
        )
        
        db.session.add(response)
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


@student_bp.route('/complaints/<string:ticket_number>/track', methods=['GET'])
@jwt_required()
def track_complaint_by_ticket(ticket_number):
    """
    Track a complaint by ticket number.
    
    Path Parameters:
        - ticket_number: Ticket number of the complaint
        
    Returns:
        JSON response with complaint status
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Find complaint by ticket number
        complaint = Complaint.query.filter_by(
            ticket_number=ticket_number.upper()
        ).first()
        
        if not complaint:
            return create_error_response(
                "Complaint not found with this ticket number",
                status_code=404
            )
        
        # Check ownership
        if complaint.user_id != user.id:
            return create_error_response(
                "Access denied. You can only track your own complaints.",
                status_code=403
            )
        
        return create_success_response(
            data={'complaint': complaint.to_dict(include_responses=True)},
            message="Complaint found"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to track complaint: {str(e)}",
            status_code=500
        )


@student_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_student_stats():
    """
    Get statistics for current student's complaints.
    
    Returns:
        JSON response with complaint statistics
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Get counts by status
        total = Complaint.query.filter_by(user_id=user.id).count()
        pending = Complaint.query.filter_by(user_id=user.id, status='pending').count()
        in_progress = Complaint.query.filter_by(user_id=user.id, status='in_progress').count()
        resolved = Complaint.query.filter_by(user_id=user.id, status='resolved').count()
        closed = Complaint.query.filter_by(user_id=user.id, status='closed').count()
        rejected = Complaint.query.filter_by(user_id=user.id, status='rejected').count()
        
        # Get recent complaints
        recent_complaints = Complaint.query.filter_by(user_id=user.id)\
            .order_by(Complaint.created_at.desc())\
            .limit(5)\
            .all()
        
        # Get unread notifications count
        unread_notifications = Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).count()
        
        return create_success_response(
            data={
                'statistics': {
                    'total': total,
                    'pending': pending,
                    'in_progress': in_progress,
                    'resolved': resolved,
                    'closed': closed,
                    'rejected': rejected
                },
                'recent_complaints': [c.to_dict() for c in recent_complaints],
                'unread_notifications': unread_notifications
            },
            message="Statistics retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve statistics: {str(e)}",
            status_code=500
        )


@student_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get notifications for current student.
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10)
        - unread_only: Show only unread notifications (default: false)
        
    Returns:
        JSON response with paginated notifications
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        # Build query
        query = Notification.query.filter_by(user_id=user.id)
        
        # Filter unread only
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Order by created_at desc
        query = query.order_by(Notification.created_at.desc())
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = paginate_query(query, page=page, per_page=per_page)
        
        notifications = [n.to_dict() for n in pagination.items]
        
        return create_success_response(
            data={
                'notifications': notifications,
                'pagination': get_pagination_info(pagination)
            },
            message="Notifications retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve notifications: {str(e)}",
            status_code=500
        )


@student_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    """
    Mark a notification as read.
    
    Path Parameters:
        - notification_id: ID of the notification
        
    Returns:
        JSON response with success message
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return create_error_response("Notification not found", status_code=404)
        
        if notification.user_id != user.id:
            return create_error_response("Access denied", status_code=403)
        
        notification.mark_as_read()
        db.session.commit()
        
        return create_success_response(message="Notification marked as read")
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update notification: {str(e)}",
            status_code=500
        )


@student_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_as_read():
    """
    Mark all notifications as read.
    
    Returns:
        JSON response with success message
    """
    try:
        user, error = get_current_student()
        if error:
            return error
        
        Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return create_success_response(message="All notifications marked as read")
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            f"Failed to update notifications: {str(e)}",
            status_code=500
        )