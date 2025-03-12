from . import db
from sqlalchemy import Integer, String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # Add username field
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Book(db.Model):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<Book {self.title} by {self.author}>"

class Profile(db.Model):
    __tablename__ = 'profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    novel: Mapped[bool] = mapped_column(default=False)
    short_story: Mapped[bool] = mapped_column(default=False)
    poetry: Mapped[bool] = mapped_column(default=False)
    satire: Mapped[bool] = mapped_column(default=False)
    romance: Mapped[bool] = mapped_column(default=False)
    psychological: Mapped[bool] = mapped_column(default=False)
    spiritual: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f"<Profile {self.user_id}>"

users_books = Table(
    'users_books',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True)
)

# Export user_books
__all__ = ['User', 'Book', 'Profile', 'users_books']
