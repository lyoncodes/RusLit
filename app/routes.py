import os
from flask import render_template, request, redirect, url_for, jsonify, Blueprint, flash, Flask, session  # Ensure Flask and session are imported
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from . import app, db  # Import db
from openai import OpenAI
from agents import Agent, Runner, WebSearchTool
from dotenv import load_dotenv
from .models import User, Book, Profile, users_books, friendships, LLMCache  # Import the User, Book models and linking table
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urljoin, quote_plus  # Add import for encoding special characters
import requests  # Add import for making HTTP requests
import csv  # Add import for CSV handling
import json
import time
import pymarc
from authlib.integrations.flask_client import OAuth
from concurrent.futures import ThreadPoolExecutor, as_completed  # Add import for ThreadPoolExecutor
from internetarchive import get_item, search_items, get_files
from .utils import get_user_books  # Import the helper function
from .config import (
    OPENAI_API_KEY,
    OPENAI_4O_ENDPOINT,
    GOOGLE_API_KEY,
    GOOGLE_BOOKS_ENDPOINT,
    PW_ENCODE,
    PW_HASH_METHOD,
    IA_BOOKS_COLLECTION,
    GOOGLE_CONSUMER_KEY,
    GOOGLE_CONSUMER_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_BASE_URL,
    GOOGLE_ACCESS_TOKEN_URL,
    GOOGLE_AUTH_ENDPOINT,
)


login_manager = LoginManager()
login_manager.init_app(app)

# Load environment variables from .env file
load_dotenv()
user_bp = Blueprint('user_bp', __name__)

# Use variables from config.py
token = OPENAI_API_KEY
endpoint = OPENAI_4O_ENDPOINT
books_token = GOOGLE_API_KEY
books_endpoint = GOOGLE_BOOKS_ENDPOINT
pw_encode = PW_ENCODE
pw_hash = PW_HASH_METHOD
ia_books_collection = IA_BOOKS_COLLECTION

# Google credentials
google_consumer_key = GOOGLE_CONSUMER_KEY
google_consumer_secret = GOOGLE_CONSUMER_SECRET
google_client_id = GOOGLE_CLIENT_ID
google_client_secret = GOOGLE_CLIENT_SECRET
google_base_url = GOOGLE_BASE_URL
google_access_token_url = GOOGLE_ACCESS_TOKEN_URL
google_auth_endpoint = GOOGLE_AUTH_ENDPOINT

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
    instructions="ou are an expert in world Literature, your role is to offer 50 relevant, specified recommendations based on the data you receive from the user's query. Diversify your selections from authors from multiple countries, and provide brief explanations for how each book relates to the user data. Always provide your entire response in a JSON object, with your suggestions always contained in an array of objects named 'recommendations', with each object's properties being title, author, description, and isbn.",
    handoffs=[
        search_agent,
        file_agent
    ],
    tools=[
        WebSearchTool()
    ]
)
# OAuth
oauth = OAuth(app)
# Google OAuth config
google = oauth.register(
    name='google',
    client_id=google_client_id,
    client_secret=google_client_secret,
    access_token_url=google_access_token_url,
    authorize_url=google_auth_endpoint,
    api_base_url=google_base_url,
    client_kwargs={'scope': 'email profile'}
)

# error log
error_log = open("error_log.txt", "a")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/', methods=['GET', 'POST'])
def home():
    profile = None
    if current_user.is_authenticated:
        profile = db.session.query(Profile).filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Handle form submission here
        # For example, you can access form data using request.form
        return redirect(url_for('home'))  # Redirect after submission
    
    return render_template('form.html', profile=profile)

@app.route('/instructions', methods=['GET'])
@login_required
def instructions():
    return render_template('instructions.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password_hash, password):
                print("Password hash matches")
                login_user(user)
                flash('Logged in successfully.')
                
                next = request.args.get('next')
                if not is_safe_url(next):
                    return "Record not found", 400

                return redirect(next or url_for('home'))
            else:
                print("Password hash does not match")
        else:
            print("User not found")
        flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/login-with-google', methods=['GET', 'POST'])
def login_google():
    redirect_uri = url_for('auth_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google', methods=['GET', 'POST'])
def auth_google():
    token = google.authorize_access_token()
    session['google_token'] = token  # Store the token in Flask's session
    resp = google.get('userinfo')
    user_info = resp.json()

    if not user_info or 'email' not in user_info:
        flash("Google login failed.", "danger")
        return redirect(url_for('login'))

    google_id = user_info['id']
    google_profile_link = f"https://profiles.google.com/{google_id}"

    print(user_info)
    user = User.query.filter_by(email=user_info['email']).first()

    if not user:
        user = User(username=user_info['email'], email=user_info['email'], google_id=user_info['id'])
        db.session.add(user)
        db.session.commit()

    profile = Profile.query.filter_by(user_id=user.id).first()

    if not profile:
        profile = Profile(
            user_id=user.id,
            profile_picture=user_info.get('picture'),
            google_profile_link=google_profile_link
        )
        db.session.add(profile)
    else:
        profile.profile_picture = user_info.get('picture')
        profile.google_profile_link = google_profile_link

    db.session.commit()
    login_user(user)
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password using pbkdf2:sha256
        password_hash = generate_password_hash(password, method=pw_hash)
        print(f"Generated password hash: {password_hash}")
        
        # Create a new user
        new_user = User(
            full_name=f"{first_name} {last_name}",
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        # Add the new user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully!')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/user/<id>/profile', methods=['GET', 'POST'])
@login_required
def profile(id):
    user = User.query.get(id)
    profile = Profile.query.filter_by(user_id=id).first()
    
    # Directly query the users_books table
    user_books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == id).all()

    users_friends = db.session.query(User).join(friendships, User.id == friendships.c.friend_id).filter(friendships.c.user_id == id).all()

    if request.method == 'POST':
        novel = request.form.get('novel') == 'on'
        short_story = request.form.get('short_story') == 'on'
        poetry = request.form.get('poetry') == 'on'
        satire = request.form.get('satire') == 'on'
        romance = request.form.get('romance') == 'on'
        psychological = request.form.get('psychological') == 'on'
        spiritual = request.form.get('spiritual') == 'on'
        social = request.form.get('social') == 'on'
        existential = request.form.get('existential') == 'on'
        political = request.form.get('political') == 'on'
        nihilistic = request.form.get('nihilistic') == 'on'
        ethical = request.form.get('ethical') == 'on'
        
        if profile:
            profile.genre_novel = novel
            profile.genre_short_story = short_story
            profile.genre_poetry = poetry
            profile.genre_satire = satire
            profile.genre_romance = romance
            profile.genre_psychological = psychological
            profile.genre_spiritual = spiritual
            profile.interest_social = social
            profile.interest_psychological = psychological
            profile.interest_existential = existential
            profile.interest_political = political
            profile.interest_nihilistic = nihilistic
            profile.interest_ethical = ethical
        else:
            profile = Profile(
                user_id=current_user.id,
                genre_novel=novel,
                genre_short_story=short_story,
                genre_poetry=poetry,
                genre_satire=satire,
                genre_romance=romance,
                genre_psychological=psychological,
                genre_spiritual=spiritual,
                interest_social=social,
                interest_psychological=psychological,
                interest_existential=existential,
                interest_political=political,
                interest_nihilistic=nihilistic,
                interest_ethical=ethical
            )
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', id=current_user.id))
    
    if request.method == 'GET':
        searchString = request.args.get('searchString')
        search_results = None

        if searchString:
            searchString = searchString.replace(" ", "+")
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    requests.get, 
                    f"{books_endpoint}volumes/?q={searchString}&key={books_token}"
                )
                response = future.result()
            if response.status_code == 200:
                search_results = response.json()
                search_results = search_results.get('items', [])
                for item in search_results:
                    item['volumeInfo']['description'] = item['volumeInfo'].get('description', 'No description available')
            else:
                flash('Error fetching data from Google Books API', 'danger')
        if search_results:
            search_results = search_results[:20]  # Limit the number of search results to 20
        else:
            search_results = []

        if user:
            return render_template(
                'profile.html', 
                user=user, 
                profile=profile, 
                books=user_books, 
                search_results=search_results,
                friends=users_friends
            )
        else:
            return {"error": "User not found"}, 404

@app.route('/profile_list', methods=['GET'])
@login_required
def profile_search():
    searchString = request.args.get('searchString')
    search_results = None
    return render_template(
        'profileList.html',
        profile=profile,
        search_results=search_results
     )

@app.route('/submit_form', methods=['POST'])
async def submit_form():
    # Process the form data here
    form_data = request.form.to_dict()

    # Get the user's internal bookshelf
    user_books = []
    if current_user.is_authenticated:
        user_books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == current_user.id).all()
        user_books = ', '.join([f"{book.title} by {book.author}" for book in user_books])

    # build_query_text builds a prompt based off form & user data
    def build_query_text(form_data, profile):
        genre_tags = []
        realm_tags = []
        philosophy_tags = []
        prompt = ""

        # genres
        if profile.genre_novel:
            genre_tags.append("Novels")
        if profile.genre_short_story:
            genre_tags.append("Short Stories")
        if profile.genre_poetry:
            genre_tags.append("Poetry")
        if profile.genre_satire:
            genre_tags.append("Satire")

        if len(genre_tags):
            if len(genre_tags) == 1:
                prompt += f"Recommend a list of {genre_tags[0]}"
            elif len(genre_tags) == 2:
                prompt += f"Recommend a list of {genre_tags[0]} and {genre_tags[1]}"
            else:
                genre_tags[len(genre_tags) - 1] = f"and {genre_tags[len(genre_tags) - 1]}"
                prompt += f"Recommend a list of {', '.join(genre_tags)}"
        else:
            prompt += "Recommend a list of literature"

        # realms & disciplines
        if profile.interest_social:
            philosophy_tags.append("sociological")
        if profile.interest_existential:
            philosophy_tags.append("existential")
        if profile.interest_political:
            philosophy_tags.append("political")
        if profile.interest_nihilistic:
            philosophy_tags.append("nihilistic")
        if profile.interest_ethical:
            philosophy_tags.append("ethical")

        if profile.genre_romance:
            realm_tags.append("romantic")
        if profile.genre_psychological:
            realm_tags.append("psychological")
        if profile.genre_spiritual:
            realm_tags.append("spiritual")

        if len(realm_tags) and len(philosophy_tags):
            tags = realm_tags + philosophy_tags
            prompt += f" Focus results on works with {', '.join(tags)} themes"
        elif len(realm_tags) and len(philosophy_tags) == 0:
            prompt += f" Focus results on works that are {', '.join(realm_tags)} in nature"
        elif len(philosophy_tags) and len(realm_tags) == 0:
            prompt += f" Focus results on works with {', '.join(philosophy_tags)} themes"

        if form_data.get('realm'):
            prompt += f" and {form_data['realm']}"

        prompt += ","

        # reading time
        if form_data.get('mediaLength'):
            if form_data['mediaLength'] == "short":
                duration = "between 1 to 3 hours"
            if form_data['mediaLength'] == "medium":
                duration = "between 4 to 10 hours"
            if form_data['mediaLength'] == "long":
                duration = "longer than 10 hours"
            prompt += f" which should take an advanced reader {duration} to complete"

        prompt += "."

        if form_data.get('includeBookshelf'):
            prompt += f" The reader's bookshelf contains {user_books}, so base your results on these titles but exclude them from your recommendations."

        prompt += " Thank you!"

        # Add any additional form data to the prompt
        return prompt

    def format_json_from_response(response):
        if response.startswith("```json"):
            response = response.replace("```json", "").replace("```", "").strip()
        print(response)
        return json.loads(response)

    if current_user.is_authenticated:
        profile = db.session.query(Profile).filter_by(user_id=current_user.id).first()

    formatted_content = build_query_text(form_data, profile)

    # Check if the prompt already exists in the cache
    cached_response = db.session.query(LLMCache).filter_by(prompt=formatted_content).first()
    if cached_response:
        print("Cache hit for prompt.")
        return jsonify({
            "response": json.loads(cached_response.response),  # Return cached response
        })

    try:
        # Create a request to the client.chat.completions object
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in world Literature bot, your role is to offer 50 relevant, specified recommendations. Diversify your selections from authors from multiple countries, and provide brief explanations for how each book relates to the user's query. Always provide your entire response in a JSON object, with your suggestions always contained in an array of objects named 'recommendations', with each object's properties being title, author, description, and isbn. Thank you for your help!",
                    "metadata": {
                        "tags": ["World Literature", "Recommendations"]
                    },
                },
                {
                    "role": "user",
                    "content": formatted_content
                }
            ],
        )

        # Log the raw response for debugging
        print("Raw OpenAI Response:", response)

        # Ensure the response contains choices
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("OpenAI response is empty or malformed.")

        # Extract and sanitize the response content
        gpt_res = response.choices[0].message.content

        # Log the response content
        print("OpenAI Response Content:", gpt_res)

        # Sanitize and parse the response
        loaded_json = format_json_from_response(gpt_res)

        # Check if the response is a valid JSON object
        if not isinstance(loaded_json, dict):
            raise ValueError("OpenAI response is not a valid JSON object.")
        # Check if the response contains the expected keys
        if not all(key in loaded_json for key in ["recommendations"]):
            raise ValueError("OpenAI response is missing expected keys.")
        # Log the formatted JSON response
        print("Formatted JSON Response:", json.dumps(loaded_json, indent=4))

        # Store the response in the cache
        new_cache_entry = LLMCache(
            prompt=formatted_content,
            response=json.dumps(loaded_json)
        )
        db.session.add(new_cache_entry)
        db.session.commit()

        return jsonify({
            "response": loaded_json,
        })

    except Exception as e:
        print(f"Error fetching data from OpenAI: {e}")
        return jsonify({"error": "Failed to fetch data from OpenAI", "details": str(e)}), 500

@app.route('/book_detail/<author>/<title>', methods=['GET'])
def book_details(author, title):
    # render template
    return render_template('bookDetails.html', author=author, title=title)

@app.route('/api/find/<isbn>', methods=['GET'])
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
        print(json.dumps(search_results, indent=4))
        return jsonify(search_results)
    else:
        return jsonify({"error": "Error fetching data from Google Books API"}), response.status_code

@app.route('/api/book_metadata/<title>/<author>', methods=['GET'])
def fetch_book_meta(title, author):
    # Format the title by replacing spaces with '+' and encoding special characters
    formatted_title = title.replace("&", "+").replace("amp;", "")
    formatted_author = author.replace(" ", "+")
    # Default to page 1
    page = int(request.args.get('page', 1))
    # Number of results per page
    rows_per_page = 10
    # Calculate the starting index
    start = (page - 1) * rows_per_page

    # Fetch book details from Archive.org
    search_string = f"collection:\"{ia_books_collection}\" AND description:\"{formatted_author}\" AND language:\"eng\""
    # convert to list
    print(search_string)
    search_results = list(search_items(search_string))

    # Slice results for pagination
    paginated_results = search_results[start:start + rows_per_page]

    def fetch_meta(id):
        item = get_item(id)
        metadata = item.metadata
        # Pretty-print metadata to the console
        print(json.dumps(metadata, indent=4))

        isbn = metadata.get("isbn", "Unknown ISBN")
        if (isinstance(isbn, list) and len(isbn) > 0):
            isbn = isbn[1]
        

        return {
            "title": metadata.get("title", "Unknown Title"),
            "creator": metadata.get("creator", "Unknown Creator"),
            "isbn": isbn,
            "identifier": metadata.get("identifier-access", "Unknown Identifier"),
            "subject": metadata.get("subject", "Unknown Subject"),
            "pdf_available": metadata.get("pdf_module_version", "no .pdf")  # Include the PDF availability in the response
        }
    
    items = []

    # Concurrent data fetching
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_meta, result['identifier']) for result in paginated_results]
        for future in as_completed(futures):
            try:
                item = future.result()
                items.append(item)
            except Exception as e:
                print(f"Error fetching metadata: {e}")
                error_log.write(f"{time.ctime()}: Error fetching metadata: {e}\n")
                error_log.flush()
    
    return jsonify({
        "page": page,
        "items": items,
        "total_results": len(search_results),  # Total number of results
        "total_pages": (len(search_results) + rows_per_page - 1) // rows_per_page  # Calculate total pages
    })

# --- User routes --- #
@user_bp.route('/user/<email>', methods=['GET'])
def get_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat()
        }
    else:
        return {"error": "User not found"}, 404

@user_bp.route('/user/<id>/books', methods=['GET'])
def get_user_books(id):
    user = User.query.get(id)
    if user:
        books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == id).all()
        books_data = [{"id": book.id, "isbn": book.isbn, "title": book.title, "author": book.author} for book in books]
        return jsonify(books_data)

@app.route('/add_book_to_profile', methods=['POST'])
@login_required
def add_book_to_profile():
    book_data = request.json  # Expecting JSON data from the client
    book_id = book_data.get('id')
    title = book_data.get('title')
    author = book_data.get('author')
    isbn = book_data.get('isbn')

    if not book_id or not title or not author:
        return jsonify({"error": "Missing required book data"}), 400

    # Check if the book already exists in the database
    book = Book.query.filter_by(id=book_id).first()
    if not book:
        # Create a new book entry
        book = Book(id=book_id, title=title, author=author, isbn=isbn)
        db.session.add(book)
        db.session.commit()

    # Check if the user already has this book in their profile
    user_book = db.session.query(users_books).filter_by(user_id=current_user.id, book_id=book.id).first()
    if not user_book:
        # Add the book to the user's profile
        db.session.execute(users_books.insert().values(user_id=current_user.id, book_id=book.id))
        db.session.commit()
        return jsonify({"message": "Book added to profile successfully"}), 200
    else:
        return jsonify({"message": "Book already exists in the user's profile"}), 200
