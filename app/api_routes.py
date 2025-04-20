from flask import Blueprint, jsonify, request
from concurrent.futures import ThreadPoolExecutor, as_completed
from internetarchive import get_item, search_items
from .utils import get_user_books
from .config import (
    GOOGLE_API_KEY,
    GOOGLE_BOOKS_ENDPOINT,
    IA_BOOKS_COLLECTION,
)
import requests

api_bp = Blueprint('api_bp', __name__)

# Use variables from config.py
books_token = GOOGLE_API_KEY
books_endpoint = GOOGLE_BOOKS_ENDPOINT
ia_books_collection = IA_BOOKS_COLLECTION

@api_bp.route('/api/find/<isbn>', methods=['GET'])
def fetch_google_book_data(isbn):
    # Fetch book details from Google Books API
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            requests.get, 
            f"{books_endpoint}volumes/?q=isbn:{isbn}&key={books_token}"
        )
        response = future.result()
    if response.status_code == 200:
        search_results = response.json()
        search_results = search_results.get('items', [])
        for item in search_results:
            item['volumeInfo']['description'] = item['volumeInfo'].get('description', 'No description available')
        return jsonify(search_results)
    else:
        return jsonify({"error": "Error fetching data from Google Books API"}), response.status_code

@api_bp.route('/api/book_metadata/<title>/<author>', methods=['GET'])
def fetch_book_meta(title, author):
    # Format the title and author
    formatted_title = title.replace("&", "+").replace("amp;", "")
    formatted_author = author.replace(" ", "+")
    page = int(request.args.get('page', 1))
    rows_per_page = 10
    start = (page - 1) * rows_per_page

    # Fetch book details from Archive.org
    search_string = f"collection:\"{ia_books_collection}\" AND description:\"{formatted_author}\" AND language:\"eng\""
    search_results = list(search_items(search_string))
    paginated_results = search_results[start:start + rows_per_page]

    def fetch_meta(id):
        item = get_item(id)
        metadata = item.metadata
        isbn = metadata.get("isbn", "Unknown ISBN")
        if isinstance(isbn, list) and len(isbn) > 0:
            isbn = isbn[1]
        return {
            "title": metadata.get("title", "Unknown Title"),
            "creator": metadata.get("creator", "Unknown Creator"),
            "isbn": isbn,
            "identifier": metadata.get("identifier-access", "Unknown Identifier"),
            "subject": metadata.get("subject", "Unknown Subject"),
            "pdf_available": metadata.get("pdf_module_version", "no .pdf")
        }

    items = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_meta, result['identifier']) for result in paginated_results]
        for future in as_completed(futures):
            try:
                item = future.result()
                items.append(item)
            except Exception as e:
                print(f"Error fetching metadata: {e}")

    return jsonify({
        "page": page,
        "items": items,
        "total_results": len(search_results),
        "total_pages": (len(search_results) + rows_per_page - 1) // rows_per_page
    })
