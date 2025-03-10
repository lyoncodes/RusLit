from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize the database
db = SQLAlchemy()

app = Flask(__name__)
# Example: PostgreSQL connection URI
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1C3@pp11\.\@host:5432/dev"
# Disable track modifications if you don't need it
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

from .routes import user_bp
app.register_blueprint(user_bp)

from app import routes