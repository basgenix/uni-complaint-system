"""
Complaint Model
===============
Defines the Complaint model for student complaints and requests.
"""

from datetime import datetime
import random
import string
from app.extensions import db


class Complaint(db.Model):
    """
    Complaint model representing student complaints and requests.
    
    Attributes:
        id: Primary key
        ticket_number: Unique ticket identifier (e.g., TKT-2024-ABC123)
        user_id: Foreign key to the student who submitted
        category: Type of complaint
        title: Brief title of the complaint
        description: Detailed description
        status: Current status of the complaint
        priority: Priority level
        assigned_to: Admin assigned to handle the complaint
        attachments: JSON field for file attachments
        admin_notes: Internal notes (visible only to admins)
        created_at: Submission timestamp
        updated_at: Last update timestamp
        resolved_at: Resolution timestamp
    """
    
    __tablename__ = 'complaints'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Ticket Information
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    assigned_to = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # Complaint Details
    category = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Status and Priority
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    priority = db.Column(db.String(20), default='medium', nullable=False, index=True)
    
    # Additional Fields
    attachments = db.Column(db.JSON, default=list)
    admin_notes = db.Column(db.Text, nullable=True)  # Internal notes for admins
    
    # Timestamps
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    responses = db.relationship(
        'Response',
        backref='complaint',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Response.created_at.asc()'
    )
    
    # Valid Categories for Nigerian Universities
    VALID_CATEGORIES = [
        'transcript',
        'registration',
        'fees_payment',
        'accommodation',
        'examination',
        'clearance',
        'scholarship',
        'library',
        'id_card',
        'course_registration',
        'result_issues',
        'certificate',
        'admission',
        'transfer',
        'medical',
        'security',
        'facilities',
        'academic_advising',
        'other'
    ]
    
    # Category Display Names
    CATEGORY_DISPLAY = {
        'transcript': 'Transcript Request',
        'registration': 'Registration Issues',
        'fees_payment': 'Fees & Payment',
        'accommodation': 'Accommodation/Hostel',
        'examination': 'Examination Issues',
        'clearance': 'Clearance',
        'scholarship': 'Scholarship',
        'library': 'Library Services',
        'id_card': 'ID Card',
        'course_registration': 'Course Registration',
        'result_issues': 'Result Issues',
        'certificate': 'Certificate Collection',
        'admission': 'Admission Issues',
        'transfer': 'Transfer Request',
        'medical': 'Medical/Health Services',
        'security': 'Security Issues',
        'facilities': 'Facilities & Maintenance',
        'academic_advising': 'Academic Advising',
        'other': 'Other'
    }
    
    # Valid Statuses
    VALID_STATUSES = ['pending', 'in_progress', 'resolved', 'closed', 'rejected']
    
    # Status Display Names
    STATUS_DISPLAY = {
        'pending': 'Pending',
        'in_progress': 'In Progress',
        'resolved': 'Resolved',
        'closed': 'Closed',
        'rejected': 'Rejected'
    }
    
    # Valid Priorities
    VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent']
    
    # Priority Display Names
    PRIORITY_DISPLAY = {
        'low': 'Low',
        'medium': 'Medium',
        'high': 'High',
        'urgent': 'Urgent'
    }
    
    def __init__(self, **kwargs):
        """Initialize complaint with validated data."""
        super(Complaint, self).__init__(**kwargs)
        
        # Generate ticket number if not provided
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        
        # Validate category
        if self.category not in self.VALID_CATEGORIES:
            self.category = 'other'
        
        # Validate status
        if self.status not in self.VALID_STATUSES:
            self.status = 'pending'
        
        # Validate priority
        if self.priority not in self.VALID_PRIORITIES:
            self.priority = 'medium'
        
        # Initialize attachments as empty list if None
        if self.attachments is None:
            self.attachments = []
    
    @staticmethod
    def generate_ticket_number():
        """
        Generate a unique ticket number.
        Format: TKT-YYYY-XXXXXX (e.g., TKT-2024-A3B5C7)
        
        Returns:
            str: Unique ticket number
        """
        year = datetime.utcnow().year
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TKT-{year}-{random_part}"
    
    def update_status(self, new_status):
        """
        Update complaint status with validation.
        
        Args:
            new_status: New status value
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        if new_status not in self.VALID_STATUSES:
            return False
        
        self.status = new_status
        
        # Set resolved_at timestamp when resolved or closed
        if new_status in ['resolved', 'closed'] and not self.resolved_at:
            self.resolved_at = datetime.utcnow()
        
        return True
    
    def get_category_display(self):
        """Get display name for category."""
        return self.CATEGORY_DISPLAY.get(self.category, self.category)
    
    def get_status_display(self):
        """Get display name for status."""
        return self.STATUS_DISPLAY.get(self.status, self.status)
    
    def get_priority_display(self):
        """Get display name for priority."""
        return self.PRIORITY_DISPLAY.get(self.priority, self.priority)
    
    def get_response_count(self):
        """Get the number of responses on this complaint."""
        return self.responses.count()
    
    def to_dict(self, include_responses=False, include_student=True):
        """
        Convert complaint object to dictionary.
        
        Args:
            include_responses: Whether to include responses
            include_student: Whether to include student information
            
        Returns:
            dict: Complaint data as dictionary
        """
        data = {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'user_id': self.user_id,
            'category': self.category,
            'category_display': self.get_category_display(),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'assigned_to': self.assigned_to,
            'attachments': self.attachments or [],
            'response_count': self.get_response_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
        
        # Include student information
        if include_student and self.student:
            data['student'] = {
                'id': self.student.id,
                'full_name': self.student.full_name,
                'matric_number': self.student.matric_number,
                'email': self.student.email,
                'department': self.student.department,
                'faculty': self.student.faculty
            }
        
        # Include assigned admin information
        if self.assigned_admin:
            data['assigned_admin'] = {
                'id': self.assigned_admin.id,
                'full_name': self.assigned_admin.full_name,
                'email': self.assigned_admin.email
            }
        else:
            data['assigned_admin'] = None
        
        # Include responses if requested
        if include_responses:
            data['responses'] = [
                response.to_dict() for response in self.responses.all()
            ]
        
        return data
    
    def __repr__(self):
        """String representation of Complaint."""
        return f'<Complaint {self.ticket_number}: {self.title[:30]}...>'