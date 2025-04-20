import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from authlib.integrations.flask_client import OAuth
from .config import DATABASE_URI, SECRET_KEY

class Base(DeclarativeBase):
    pass

# Initialize the database
db = SQLAlchemy(model_class=Base)

# Initialize the Flask app
app = Flask(__name__)

# Set the secret key and database URI from config.py
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications for performance

# Initialize the database with the app
db.init_app(app)

# Initialize OAuth
oauth = OAuth(app)

# Import and register blueprints
from .routes import user_bp
app.register_blueprint(user_bp)

from .api_routes import api_bp
app.register_blueprint(api_bp)

# Ensure routes are loaded
from app import routes