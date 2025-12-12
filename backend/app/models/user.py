"""
User Model
==========
Defines the User model for students and administrators.
"""

from datetime import datetime
from app.extensions import db, bcrypt


class User(db.Model):
    """
    User model representing students and admin staff.
    
    Attributes:
        id: Primary key
        email: Unique email address
        password_hash: Bcrypt hashed password
        full_name: User's full name
        matric_number: Student matriculation number (unique, nullable for admins)
        department: User's department
        faculty: User's faculty
        phone: Phone number
        role: User role (student, admin, super_admin)
        is_active: Whether the account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Authentication Fields
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    matric_number = db.Column(db.String(30), unique=True, nullable=True, index=True)
    department = db.Column(db.String(100), nullable=True)
    faculty = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Role and Status
    role = db.Column(db.String(20), default='student', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    complaints = db.relationship(
        'Complaint',
        backref='student',
        lazy='dynamic',
        foreign_keys='Complaint.user_id',
        cascade='all, delete-orphan'
    )
    
    assigned_complaints = db.relationship(
        'Complaint',
        backref='assigned_admin',
        lazy='dynamic',
        foreign_keys='Complaint.assigned_to'
    )
    
    responses = db.relationship(
        'Response',
        backref='author',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    notifications = db.relationship(
        'Notification',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Valid roles
    VALID_ROLES = ['student', 'admin', 'super_admin']
    
    def __init__(self, **kwargs):
        """Initialize user with validated data."""
        super(User, self).__init__(**kwargs)
        
        # Validate role
        if self.role not in self.VALID_ROLES:
            self.role = 'student'
    
    def set_password(self, password):
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """
        Verify a password against the hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin privileges."""
        return self.role in ['admin', 'super_admin']
    
    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == 'super_admin'
    
    def to_dict(self, include_email=True):
        """
        Convert user object to dictionary.
        
        Args:
            include_email: Whether to include email in response
            
        Returns:
            dict: User data as dictionary
        """
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'matric_number': self.matric_number,
            'department': self.department,
            'faculty': self.faculty,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_email:
            data['email'] = self.email
            
        return data
    
    def __repr__(self):
        """String representation of User."""
        return f'<User {self.id}: {self.email} ({self.role})>'