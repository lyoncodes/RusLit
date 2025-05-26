from .models import Book, users_books
from flask_login import current_user
from sqlalchemy import or_

def get_user_books(user_id):
    """
    Fetches all books associated with a user.
    """
    from . import db  # Import db here to avoid circular imports
    return db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == user_id).all()

def get_books_by_lastname(last_name):
    """
    Fetches all books from the local database that match the author's last name.
    """
    from . import db  # Import db here to avoid circular imports
    books = db.session.query(Book).filter(Book.author.ilike(f"%{last_name}%")).all()
    print(f"Books found for last name '{last_name}': {books}")  # Debug query results
    return books
