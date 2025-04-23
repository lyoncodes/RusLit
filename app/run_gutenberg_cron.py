import os
import sys

# Ensure the project directory is in PYTHONPATH
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from app import app  # Import the Flask app instance
from app.tasks.gutenberg_ingest import update_books_from_gutendex  # Import the Gutendex ingestion function

# Run the Gutendex ingestion task within the app context
if __name__ == "__main__":
    with app.app_context():
        update_books_from_gutendex()
