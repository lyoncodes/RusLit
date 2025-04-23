from . import db
from sqlalchemy import Integer, String, Table, Column, ForeignKey, Boolean
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
    google_id: Mapped[str] = mapped_column(String, nullable=False)

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

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Change id to String
    isbn: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<Book {self.title} by {self.author}>"

class Profile(db.Model):
    __tablename__ = 'profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    locale: Mapped[str] = mapped_column(String, nullable=False)
    profile_picture: Mapped[str] = mapped_column(String, nullable=False)
    google_profile_link: Mapped[str] = mapped_column(String, nullable=False)
    genre_novel: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_short_story: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_poetry: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_satire: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_romance: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_psychological: Mapped[bool] = mapped_column(Boolean, default=False)
    genre_spiritual: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_psychological: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_spiritual: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_social: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_existential: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_political: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_nihilistic: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_ethical: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Profile {self.user_id}>"

class BookFormat(db.Model):
    __tablename__ = 'book_formats'

    book_id: Mapped[int] = mapped_column(Integer, ForeignKey('books.id'), primary_key=True)
    format: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String, nullable=False)  # Add the missing 'url' column

    def __repr__(self):
        return f"<BookFormat book_id={self.book_id} format={self.format}>"

users_books = Table(
    'users_books',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
    Column('created_at', db.DateTime, nullable=False, default=datetime.utcnow)  # Use db.DateTime here
)

user_profiles = Table(
    'user_profiles',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('profile_id', Integer, ForeignKey('profiles.id'), primary_key=True)
)

friendships = Table(
    'friendships',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', db.DateTime, nullable=False, default=datetime.utcnow)
)

class LLMCache(db.Model):
    __tablename__ = 'llm_cache'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    response: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"<LLMCache id={self.id} prompt={self.prompt[:30]}...>"


# Export user_books
__all__ = ['User', 'Book', 'Profile', 'BookFormat', 'users_books', 'users_profiles', 'LLMCache']
