from .models import Book, users_books
from flask_login import current_user

def get_user_books(user_id):
    """
    Fetches all books associated with a user.
    """
    from . import db  # Import db here to avoid circular imports
    return db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == user_id).all()
