import requests
from app import db  # Use absolute import for db
from app.models import Book, BookFormat  # Use absolute import for models
from app.tasks.isbn_enrichment import enrich_books_with_isbn  # Import the isbn_enrichment function

GUTENDEX_API_URL = "https://gutendex.com/books"

def fetch_books_from_gutendex(page=1):
    """
    Fetches books from the Gutendex API.
    """
    try:
        response = requests.get(GUTENDEX_API_URL, params={"page": page})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from Gutendex API: {e}")
        return None

def update_books_from_gutendex():
    """
    Updates the database with books and formats from the Gutendex API.
    """
    page = 1
    while True:
        data = fetch_books_from_gutendex(page)
        if not data or "results" not in data:
            break

        for book in data["results"]:
            # Extract book details
            book_id = str(book.get("id"))  # Ensure book_id is a string
            title = book.get("title")
            authors = book.get("authors", [])
            author = authors[0]["name"] if authors else "Unknown"
            formats = book.get("formats", {})

            # Skip books without a valid title or author
            if not title or author == "Unknown":
                print(f"Skipping book {book_id} due to missing title or author.")
                continue

            # Add or update the book in the database
            db_book = Book.query.get(book_id)
            if not db_book:
                db_book = Book(id=book_id, title=title, author=author)
                db.session.add(db_book)
            else:
                db_book.title = title
                db_book.author = author

            # Add or update formats
            for format_type, format_url in formats.items():  # Corrected order of items
                if not format_url or not format_type:
                    continue
                existing_format = BookFormat.query.filter_by(book_id=book_id, format=format_type).first()
                if not existing_format:
                    db.session.add(BookFormat(book_id=book_id, format=format_type, url=format_url))
                else:
                    existing_format.url = format_url  # Update the URL if it already exists

        db.session.commit()
        print(f"Processed page {page}.")

        # Check if there are more pages
        if not data.get("next"):
            break
        page += 1

    print("Starting ISBN enrichment...")
    enrich_books_with_isbn()  # Call the ISBN enrichment script after processing books
    print("ISBN enrichment complete.")

    print("Database update complete.")
