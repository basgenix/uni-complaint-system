"""
Flask Extensions Module
=======================
This module initializes all Flask extensions.
Extensions are initialized here and imported into the app factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# Database ORM
db = SQLAlchemy()

# Database Migrations
migrate = Migrate()

# JWT Authentication
jwt = JWTManager()

# Password Hashing
bcrypt = Bcrypt()

# Cross-Origin Resource Sharing
cors = CORS()