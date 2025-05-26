import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from authlib.integrations.flask_client import OAuth
from flask_cors import CORS
from .config import DATABASE_URI, SECRET_KEY

class Base(DeclarativeBase):
    pass

# Initialize the database
db = SQLAlchemy(model_class=Base)

# Initialize the Flask app
app = Flask(__name__)

# Enable CORS for all routes and origins (for development)
# CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Alternatively, restrict to specific origins (e.g., your React app's URL)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})  # Ensure this matches your React app's URL

# Set the secret key and database URI from config.py
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications for performance

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
(app)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize the database with the app
db.init_app(app)

# Initialize OAuth
oauth = OAuth(app)

# Import and register blueprints
from .routes import user_bp
app.register_blueprint(user_bp)

from .api_routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')  # Ensure the prefix is '/api'

# Ensure routes are loaded
from app import routes

# Print registered routes
print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)