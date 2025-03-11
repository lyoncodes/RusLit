import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
pw = os.getenv("DB_CONN")

class Base(DeclarativeBase):
    pass
# Initialize the database
db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
# Example: PostgreSQL connection URI
app.config['SQLALCHEMY_DATABASE_URI'] = pw
# Disable track modifications if you don't need it
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

from .routes import user_bp
app.register_blueprint(user_bp)

from app import routes