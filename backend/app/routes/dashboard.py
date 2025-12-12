"""
Dashboard Routes
================
Handles analytics, statistics, and reporting endpoints.
"""

from datetime import datetime, timedelta
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, extract
from app.routes import dashboard_bp
from app.models import User, Complaint, Response
from app.extensions import db
from app.utils.helpers import (
    create_success_response,
    create_error_response
)


def get_current_admin():
    """
    Helper function to get current admin user.
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


@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """
    Get overview statistics for the dashboard.
    
    Returns:
        JSON response with overview statistics
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        # Total counts
        total_complaints = Complaint.query.count()
        total_students = User.query.filter_by(role='student').count()
        total_admins = User.query.filter(
            User.role.in_(['admin', 'super_admin'])
        ).count()
        
        # Status counts
        pending_count = Complaint.query.filter_by(status='pending').count()
        in_progress_count = Complaint.query.filter_by(status='in_progress').count()
        resolved_count = Complaint.query.filter_by(status='resolved').count()
        closed_count = Complaint.query.filter_by(status='closed').count()
        rejected_count = Complaint.query.filter_by(status='rejected').count()
        
        # Unassigned complaints
        unassigned_count = Complaint.query.filter(
            Complaint.assigned_to.is_(None),
            Complaint.status.in_(['pending', 'in_progress'])
        ).count()
        
        # Today's statistics
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        new_today = Complaint.query.filter(
            Complaint.created_at >= today_start
        ).count()
        
        resolved_today = Complaint.query.filter(
            Complaint.resolved_at >= today_start
        ).count()
        
        # This week's statistics
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        
        new_this_week = Complaint.query.filter(
            Complaint.created_at >= week_start_dt
        ).count()
        
        resolved_this_week = Complaint.query.filter(
            Complaint.resolved_at >= week_start_dt
        ).count()
        
        # Average resolution time (in hours) for resolved complaints
        resolved_complaints = Complaint.query.filter(
            Complaint.resolved_at.isnot(None)
        ).all()
        
        if resolved_complaints:
            total_hours = sum(
                (c.resolved_at - c.created_at).total_seconds() / 3600
                for c in resolved_complaints
            )
            avg_resolution_time = round(total_hours / len(resolved_complaints), 1)
        else:
            avg_resolution_time = 0
        
        # Recent complaints
        recent_complaints = Complaint.query.order_by(
            Complaint.created_at.desc()
        ).limit(5).all()
        
        return create_success_response(
            data={
                'overview': {
                    'total_complaints': total_complaints,
                    'total_students': total_students,
                    'total_admins': total_admins,
                    'unassigned_count': unassigned_count,
                    'avg_resolution_time_hours': avg_resolution_time
                },
                'status_counts': {
                    'pending': pending_count,
                    'in_progress': in_progress_count,
                    'resolved': resolved_count,
                    'closed': closed_count,
                    'rejected': rejected_count
                },
                'today': {
                    'new': new_today,
                    'resolved': resolved_today
                },
                'this_week': {
                    'new': new_this_week,
                    'resolved': resolved_this_week
                },
                'recent_complaints': [c.to_dict() for c in recent_complaints]
            },
            message="Dashboard overview retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve dashboard data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/charts/status', methods=['GET'])
@jwt_required()
def get_status_chart_data():
    """
    Get complaint distribution by status for pie chart.
    
    Returns:
        JSON response with status distribution
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        status_data = db.session.query(
            Complaint.status,
            func.count(Complaint.id).label('count')
        ).group_by(Complaint.status).all()
        
        data = [
            {
                'status': status,
                'label': Complaint.STATUS_DISPLAY.get(status, status),
                'count': count
            }
            for status, count in status_data
        ]
        
        return create_success_response(
            data={'chart_data': data},
            message="Status chart data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/charts/category', methods=['GET'])
@jwt_required()
def get_category_chart_data():
    """
    Get complaint distribution by category for bar chart.
    
    Returns:
        JSON response with category distribution
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        category_data = db.session.query(
            Complaint.category,
            func.count(Complaint.id).label('count')
        ).group_by(Complaint.category).order_by(
            func.count(Complaint.id).desc()
        ).all()
        
        data = [
            {
                'category': category,
                'label': Complaint.CATEGORY_DISPLAY.get(category, category),
                'count': count
            }
            for category, count in category_data
        ]
        
        return create_success_response(
            data={'chart_data': data},
            message="Category chart data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/charts/priority', methods=['GET'])
@jwt_required()
def get_priority_chart_data():
    """
    Get complaint distribution by priority.
    
    Returns:
        JSON response with priority distribution
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        priority_data = db.session.query(
            Complaint.priority,
            func.count(Complaint.id).label('count')
        ).group_by(Complaint.priority).all()
        
        data = [
            {
                'priority': priority,
                'label': Complaint.PRIORITY_DISPLAY.get(priority, priority),
                'count': count
            }
            for priority, count in priority_data
        ]
        
        return create_success_response(
            data={'chart_data': data},
            message="Priority chart data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/charts/trend', methods=['GET'])
@jwt_required()
def get_trend_chart_data():
    """
    Get complaint trend over time for line chart.
    
    Query Parameters:
        - days: Number of days to look back (default: 30, max: 365)
        
    Returns:
        JSON response with daily complaint counts
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        days = request.args.get('days', 30, type=int)
        days = min(max(7, days), 365)  # Between 7 and 365 days
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily counts
        daily_data = db.session.query(
            func.date(Complaint.created_at).label('date'),
            func.count(Complaint.id).label('count')
        ).filter(
            Complaint.created_at >= start_date
        ).group_by(
            func.date(Complaint.created_at)
        ).order_by(
            func.date(Complaint.created_at)
        ).all()
        
        # Create a complete date range
        data = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        daily_counts = {str(d): c for d, c in daily_data}
        
        while current_date <= end_date:
            date_str = str(current_date)
            data.append({
                'date': date_str,
                'count': daily_counts.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        return create_success_response(
            data={'chart_data': data},
            message="Trend chart data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/charts/monthly', methods=['GET'])
@jwt_required()
def get_monthly_chart_data():
    """
    Get monthly complaint counts for the current year.
    
    Returns:
        JSON response with monthly complaint counts
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        current_year = datetime.utcnow().year
        
        monthly_data = db.session.query(
            extract('month', Complaint.created_at).label('month'),
            func.count(Complaint.id).label('count')
        ).filter(
            extract('year', Complaint.created_at) == current_year
        ).group_by(
            extract('month', Complaint.created_at)
        ).order_by(
            extract('month', Complaint.created_at)
        ).all()
        
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        monthly_counts = {int(m): c for m, c in monthly_data}
        
        data = [
            {
                'month': i + 1,
                'month_name': month_names[i],
                'count': monthly_counts.get(i + 1, 0)
            }
            for i in range(12)
        ]
        
        return create_success_response(
            data={'chart_data': data, 'year': current_year},
            message="Monthly chart data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/reports/summary', methods=['GET'])
@jwt_required()
def get_summary_report():
    """
    Generate a summary report with comprehensive statistics.
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        
    Returns:
        JSON response with summary report data
    """
    try:
        admin, error = get_current_admin()
        if error:
            return error
        
        # Parse dates
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return create_error_response(
                    "Invalid start_date format. Use YYYY-MM-DD",
                    status_code=400
                )
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                return create_error_response(
                    "Invalid end_date format. Use YYYY-MM-DD",
                    status_code=400
                )
        else:
            end_date = datetime.utcnow()
        
        # Query complaints within date range
        base_query = Complaint.query.filter(
            Complaint.created_at >= start_date,
            Complaint.created_at <= end_date
        )
        
        total = base_query.count()
        
        # Status breakdown
        status_breakdown = {}
        for status in Complaint.VALID_STATUSES:
            count = base_query.filter_by(status=status).count()
            status_breakdown[status] = count
        
        # Category breakdown
        category_breakdown = {}
        for category in Complaint.VALID_CATEGORIES:
            count = base_query.filter_by(category=category).count()
            if count > 0:
                category_breakdown[category] = count
        
        # Priority breakdown
        priority_breakdown = {}
        for priority in Complaint.VALID_PRIORITIES:
            count = base_query.filter_by(priority=priority).count()
            priority_breakdown[priority] = count
        
        # Resolution statistics
        resolved_complaints = base_query.filter(
            Complaint.resolved_at.isnot(None)
        ).all()
        
        if resolved_complaints:
            resolution_times = [
                (c.resolved_at - c.created_at).total_seconds() / 3600
                for c in resolved_complaints
            ]
            avg_resolution = round(sum(resolution_times) / len(resolution_times), 1)
            min_resolution = round(min(resolution_times), 1)
            max_resolution = round(max(resolution_times), 1)
        else:
            avg_resolution = 0
            min_resolution = 0
            max_resolution = 0
        
        return create_success_response(
            data={
                'report': {
                    'period': {
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    },
                    'total_complaints': total,
                    'status_breakdown': status_breakdown,
                    'category_breakdown': category_breakdown,
                    'priority_breakdown': priority_breakdown,
                    'resolution_stats': {
                        'resolved_count': len(resolved_complaints),
                        'avg_hours': avg_resolution,
                        'min_hours': min_resolution,
                        'max_hours': max_resolution
                    }
                }
            },
            message="Summary report generated successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to generate report: {str(e)}",
            status_code=500
        )


@dashboard_bp.route('/reports/admin-performance', methods=['GET'])
@jwt_required()
def get_admin_performance():
    """
    Get performance statistics for each admin.
    
    Returns:
        JSON response with admin performance data
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
        
        # Get all admins
        admins = User.query.filter(
            User.role.in_(['admin', 'super_admin']),
            User.is_active == True
        ).all()
        
        performance_data = []
        
        for a in admins:
            assigned_count = Complaint.query.filter_by(assigned_to=a.id).count()
            resolved_count = Complaint.query.filter(
                Complaint.assigned_to == a.id,
                Complaint.status.in_(['resolved', 'closed'])
            ).count()
            pending_count = Complaint.query.filter(
                Complaint.assigned_to == a.id,
                Complaint.status.in_(['pending', 'in_progress'])
            ).count()
            
            response_count = Response.query.filter_by(
                user_id=a.id,
                is_internal=False
            ).count()
            
            performance_data.append({
                'admin_id': a.id,
                'admin_name': a.full_name,
                'email': a.email,
                'assigned_total': assigned_count,
                'resolved': resolved_count,
                'pending': pending_count,
                'responses_given': response_count,
                'resolution_rate': round(
                    (resolved_count / assigned_count * 100) if assigned_count > 0 else 0, 1
                )
            })
        
        # Sort by resolution rate descending
        performance_data.sort(key=lambda x: x['resolution_rate'], reverse=True)
        
        return create_success_response(
            data={'performance': performance_data},
            message="Admin performance data retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve performance data: {str(e)}",
            status_code=500
        )