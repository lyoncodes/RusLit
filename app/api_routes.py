from flask import Blueprint, jsonify, request, redirect, url_for, session
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from agents import Agent, Runner, WebSearchTool
import json
import csv
from internetarchive import get_item, search_items
from .utils import get_user_books, get_books_by_lastname
from .config import (
    GOOGLE_API_KEY,
    GOOGLE_BOOKS_ENDPOINT,
    IA_BOOKS_COLLECTION,
    OPENAI_API_KEY,
    OPENAI_4O_ENDPOINT,
    PW_ENCODE,
)
from werkzeug.security import check_password_hash
from .models import User, Book, users_books  # Ensure Book and users_books are imported
from . import db  # Ensure db is imported
import requests
from .agent_lib import LiteraryGuardrail

# Use variables from config.py
books_token = GOOGLE_API_KEY
books_endpoint = GOOGLE_BOOKS_ENDPOINT
ia_books_collection = IA_BOOKS_COLLECTION
pw_encode = PW_ENCODE
token = OPENAI_API_KEY
endpoint = OPENAI_4O_ENDPOINT

#agent tools
def handle_pdf(file):
    print('wow!')
    # Handle PDF file processing here
    # For example, you can use PyMuPDF or pdfminer to extract text from the PDF
    pass

def process_csv(file):
    file_content = ""
    if file:
        if file.filename.endswith('.csv'):
            try:
                file_content = []
                # Decode the binary stream to text
                csv_reader = csv.reader(file.stream.read().decode(pw_encode).splitlines())
                for row in csv_reader:
                    if len(row) >= 2:  # Ensure row has at least title and author
                        file_content.append(f"{row[0]} by {row[1]}")
                file_content = ', '.join(file_content)
                return file_content
            except Exception as e:
                print(f"Error processing CSV file: {e}")
                return jsonify({"error": "Failed to process CSV file", "details": str(e)}), 400

#models
model_name = "gpt-4o"
client = OpenAI(
    base_url=endpoint,
    api_key=token,
)
search_agent = Agent(
    name="search_agent",
    instructions="An agent that searches the web for full epub versions of the isbns provided in the query.",
    tools=[
        WebSearchTool()
    ],
)
file_agent = Agent(
    name="file_agent",
    instructions="An agent that examines records in the application database, as well as .pdf, text, epub, and other media types to find supporting information for a user's argument.",
    tools=[
        WebSearchTool(),
        handle_pdf,
        process_csv,
        get_user_books
    ]
)
book_agent = Agent(
    name="book_agent",
    instructions="You are an expert in world Literature, your role is to offer 50 relevant, specified recommendations based on the data you receive from the user's query. Diversify your selections from authors from multiple countries, and provide brief explanations for how each book relates to the user data. Always provide your entire response in a JSON object, with your suggestions always contained in an array of objects named 'recommendations', with each object's properties being title, author, description, and isbn.",
    handoffs=[
        search_agent,
        file_agent
    ],
    tools=[
        WebSearchTool(),
    ],
    input_guardrails=[LiteraryGuardrail.LiteraryGuardrail()],
)

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/prompt', methods=['POST'])
async def handle_prompt():
    """
    Handles a prompt request.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Prepare arguments for the guardrail
    input = data.get('prompt', "")

    guardrail = LiteraryGuardrail.LiteraryGuardrail()

    result = await guardrail.run(book_agent, input, context = {})

    print("Guardrail Response:", result)

    return jsonify({"message": "Prompt received", "response": "res"})

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

@api_bp.route('/book_metadata/<title>/<author>', methods=['GET'])
def fetch_book_meta(title, author):
    print(f"Received title: {title}, author: {author}")
    # Extract the author's last name (first value before the comma)
    last_name = author.split(",")[0] if "," in author else author.split(" ")[-1]
    formatted_title = title.replace("&", "+").replace("amp;", "")
    page = int(request.args.get('page', 1))
    rows_per_page = 10
    start = (page - 1) * rows_per_page

    search_string = f"description:\"{last_name}\" AND collection:\"{ia_books_collection}\""
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

    ia_items = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_meta, result['identifier']) for result in paginated_results]
        for future in as_completed(futures):
            try:
                item = future.result()
                ia_items.append(item)
            except Exception as e:
                print(f"Error fetching metadata: {e}")

    # Fetch books from the local database using the author's last name
    local_books = get_books_by_lastname(last_name)

    local_results = [
        {
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn
        }
        for book in local_books
    ]

    combined_results = {
        "page": page,
        "internet_archive": ia_items,
        "local_books": local_results,
        "total_results": len(search_results),
        "total_pages": (len(search_results) + rows_per_page - 1) // rows_per_page
    }
    print(f"Combined results: {combined_results}")  # Debug combined results

    return jsonify(combined_results)

@api_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id  # Store user ID in session
        return jsonify({"message": "Login successful", "user": {"id": user.id, "username": user.username}})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@api_bp.route('/login-with-google', methods=['GET'])
def login_with_google():
    """
    Redirects to Google OAuth login.
    """
    # Replace with your Google OAuth logic
    google_login_url = url_for('google_login', _external=True)
    return redirect(google_login_url)

@api_bp.route('/user/<id>/books', methods=['GET'])
def get_user_books_api(id):
    """
    Retrieves all books associated with a user by their ID.
    """
    user = User.query.get(id)
    if user:
        books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == id).all()
        books_data = [{"id": book.id, "isbn": book.isbn, "title": book.title, "author": book.author} for book in books]
        return jsonify(books_data)
    else:
        return jsonify({"error": "User not found"}), 404

@api_bp.route('/session', methods=['GET'])
def get_session():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                "id": user.id,
                "username": user.username,
                "email": user.email  # Ensure email is included if needed
            })
    return jsonify({"error": "No active session"}), 401

