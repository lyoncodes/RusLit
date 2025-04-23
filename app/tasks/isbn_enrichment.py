import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import requests
from flask import Flask  # Import Flask to manually create the app
from app import db  # Import db to bind it to the app
from app.models import Book  # Ensure the import path matches your project structure
from sqlalchemy import or_
from dotenv import load_dotenv  # Import dotenv to load .env variables

# Load environment variables from .env file
load_dotenv()

# Get GOOGLE_BOOKS_ENDPOINT from environment variables
GOOGLE_BOOKS_ENDPOINT = os.getenv('GOOGLE_BOOKS_ENDPOINT')
GOOGLE_BOOKS_API = GOOGLE_BOOKS_ENDPOINT
GOOGLE_KEY = os.getenv('GOOGLE_API_KEY')

print(f"database uri: {os.getenv('DATABASE_URI')}")

def create_app():
    """
    Manually create and configure the Flask application.
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')  # Use the correct key for SQLAlchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional: Disable track modifications for performance
    db.init_app(app)
    return app

def get_isbn(title, author):
    # Replace spaces in the title with '+' signs
    formatted_title = title.replace(" ", "+")
    # Extract the author's last name (first string before the comma)
    last_name = author.split(",")[0] if "," in author else author
    # Construct the query string
    query = f"{formatted_title}+inauthor:{last_name}"
    response = requests.get(f"{GOOGLE_BOOKS_ENDPOINT}volumes?q={query}&key={GOOGLE_KEY}")
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        items = response.json().get('items', [])
        if items:
            identifiers = items[0]['volumeInfo'].get('industryIdentifiers', [])
            for identifier in identifiers:
                print(identifier)
                if identifier['type'] == 'ISBN_13':
                    return identifier['identifier']
    return None

def enrich_books_with_isbn():
    books = Book.query.filter(or_(Book.isbn == None, Book.isbn == '')).all()
    print(books)
    for book in books:
        print(book.title)
        isbn = get_isbn(book.title, book.author)
        if isbn:
            book.isbn = isbn
            print(f"Updated {book.title} with ISBN {isbn}")
    db.session.commit()

if __name__ == '__main__':
    app = create_app()  # Manually create the Flask application
    with app.app_context():  # Push the application context
        enrich_books_with_isbn()
