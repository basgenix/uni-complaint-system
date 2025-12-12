"""
Notification Model
==================
Defines the Notification model for user notifications.
"""

from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    """
    Notification model representing user notifications.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to the user
        complaint_id: Foreign key to related complaint (optional)
        type: Notification type
        title: Notification title
        message: Notification message
        is_read: Whether the notification has been read
        created_at: Notification timestamp
    """
    
    __tablename__ = 'notifications'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey('complaints.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Notification Content
    type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Read Status
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Timestamp
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Valid Notification Types
    VALID_TYPES = [
        'complaint_submitted',
        'complaint_assigned',
        'status_changed',
        'new_response',
        'complaint_resolved',
        'complaint_closed',
        'system_message'
    ]
    
    def __init__(self, **kwargs):
        """Initialize notification with validated data."""
        super(Notification, self).__init__(**kwargs)
        
        # Validate type
        if self.type not in self.VALID_TYPES:
            self.type = 'system_message'
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
    
    def to_dict(self):
        """
        Convert notification object to dictionary.
        
        Returns:
            dict: Notification data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'complaint_id': self.complaint_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """String representation of Notification."""
        return f'<Notification {self.id}: {self.type} for User {self.user_id}>'
    
    @classmethod
    def create_notification(cls, user_id, notification_type, title, message, complaint_id=None):
        """
        Factory method to create a new notification.
        
        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            complaint_id: Related complaint ID (optional)
            
        Returns:
            Notification: New notification instance
        """
        notification = cls(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            complaint_id=complaint_id
        )
        db.session.add(notification)
        return notification