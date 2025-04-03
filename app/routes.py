import os
from flask import render_template, request, redirect, url_for, jsonify, Blueprint, flash, Flask, session  # Ensure Flask and session are imported
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from . import app, db  # Import db
from openai import OpenAI
from dotenv import load_dotenv
from .models import User, Book, Profile, users_books  # Import the User, Book models and linking table
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urljoin
import requests  # Add import for making HTTP requests
import csv  # Add import for CSV handling
import json
from authlib.integrations.flask_client import OAuth


login_manager = LoginManager()
login_manager.init_app(app)

# Load environment variables from .env file
load_dotenv()
user_bp = Blueprint('user_bp', __name__)
token = os.environ.get("OPENAI_API_KEY")
endpoint = os.environ.get("OPENAI_4o_ENDPOINT")
books_token = os.environ.get("GOOGLE_BOOKS_API_KEY")
books_endpoint = os.environ.get("GOOGLE_BOOKS_ENDPOINT")
pw_encode = os.environ.get("PW_ENCODE")
pw_hash = os.environ.get("PW_HASH_METHOD")

google_consumer_key = os.environ.get("GOOGLE_CONSUMER_KEY")
google_consumer_secret = os.environ.get("GOOGLE_CONSUMER_SECRET")
google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
google_base_url = os.environ.get("GOOGLE_BASE_URL")
google_access_token_url = os.environ.get("GOOGLE_ACCESS_TOKEN_URL")
google_auth_endpoint = os.environ.get("GOOGLE_AUTH_ENDPOINT")

#models
model_name = "gpt-4o"
client = OpenAI(
    base_url=endpoint,
    api_key=token,
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
    
    user_books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == id).all()

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
        mbti_istj = request.form.get('istj') == 'istj'
        mbti_isfj = request.form.get('isfj') == 'isfj'
        mbti_infj = request.form.get('infj') == 'infj'
        mbti_intj = request.form.get('intj') == 'intj'
        mbti_istp = request.form.get('istp') == 'on'
        mbti_isfp = request.form.get('isfp') == 'on'
        mbti_infp = request.form.get('infp') == 'on'
        mbti_intp = request.form.get('intp') == 'on'
        mbti_estp = request.form.get('estp') == 'on'
        mbti_esfp = request.form.get('esfp') == 'on'
        mbti_enfp = request.form.get('enfp') == 'on'
        mbti_entp = request.form.get('entp') == 'on'
        mbti_estj = request.form.get('estj') == 'on'
        mbti_esfj = request.form.get('esfj') == 'on'
        mbti_enfj = request.form.get('enfj') == 'on'
        mbti_entj = request.form.get('entj') == 'on'
        
        if profile:
            profile.genre_novel = novel
            profile.genre_short_story = short_story
            profile.genre_poetry = poetry
            profile.genre_satire = satire
            profile.genre_romance = romance
            profile.genre_psychological = psychological
            profile.genre_spiritual = spiritual
            profile.interest_social = social
            profile.interest_existential = existential
            profile.interest_political = political
            profile.interest_nihilistic = nihilistic
            profile.interest_ethical = ethical
            profile.mbti_istj = mbti_istj
            profile.mbti_isfj = mbti_isfj
            profile.mbti_infj = mbti_infj
            profile.mbti_intj = mbti_intj
            profile.mbti_istp = mbti_istp
            profile.mbti_isfp = mbti_isfp
            profile.mbti_infp = mbti_infp
            profile.mbti_intp = mbti_intp
            profile.mbti_estp = mbti_estp
            profile.mbti_esfp = mbti_esfp
            profile.mbti_enfp = mbti_enfp
            profile.mbti_entp = mbti_entp
            profile.mbti_estj = mbti_estj
            profile.mbti_esfj = mbti_esfj
            profile.mbti_enfj = mbti_enfj
            profile.mbti_entj = mbti_entj
        else:
            profile = Profile(
                user_id=current_user.id,
                genre_novel=novel,
                genre_short_story=short_story,
                genre_poetry=poetry,
                genre_satire=satire,
                genre_romance=romance,
                interest_psychological=psychological,
                interest_spiritual=spiritual,
                interest_social=social,
                interest_existential=existential,
                interest_political=political,
                interest_nihilistic=nihilistic,
                interest_ethical=ethical,
                mbti_istj=mbti_istj,
                mbti_isfj=mbti_isfj,
                mbti_infj=mbti_infj,
                mbti_intj=mbti_intj,
                mbti_istp=mbti_istp,
                mbti_isfp=mbti_isfp,
                mbti_infp=mbti_infp,
                mbti_intp=mbti_intp,
                mbti_estp=mbti_estp,
                mbti_esfp=mbti_esfp,
                mbti_enfp=mbti_enfp,
                mbti_entp=mbti_entp,
                mbti_estj=mbti_estj,
                mbti_esfj=mbti_esfj,
                mbti_enfj=mbti_enfj,
                mbti_entj=mbti_entj
            )
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', id=current_user.id))
    
    if user:
        return render_template('profile.html', user=user, profile=profile, books=user_books)  # Updated variable
    else:
        return {"error": "User not found"}, 404

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Process the form data here
    # capture form data
    form_data = request.form.to_dict()
    
    # capture file data if file uploaded
    file = request.files.get('file')
    
    # Save the file if it exists and process its content
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
            except Exception as e:
                print(f"Error processing CSV file: {e}")
                return jsonify({"error": "Failed to process CSV file", "details": str(e)}), 400
        else:
            # Handle other file types if necessary
            pass
    
    # Get the user's internal bookshelf
    user_books = []
    if current_user.is_authenticated:
        user_books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == current_user.id).all()
        user_books = ', '.join([f"{book.title} by {book.author}" for book in user_books])
    
    # build_query_text builds a prompt based off form & user data
    def build_query_text(form_data, file_content, profile):
        genre_tags = []
        realm_tags = []
        mbpti_tags = []
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
            if (len(genre_tags) == 1):
                prompt += f"Recommend a list of classic Russian {genre_tags[0]}"
            elif (len(genre_tags) == 2):
                prompt += f"Recommend a list of classic Russian {genre_tags[0]} and {genre_tags[1]}"
            else:
                genre_tags[len(genre_tags) - 1] = f"and {genre_tags[len(genre_tags) - 1]}"
                prompt += f"Recommend a list of classic Russian {', '.join(genre_tags)}"
        else:
            prompt += "Recommend a list of classic Russian literature"

        # mbti
        if profile.mbti_istj:
            mbpti_tags.append("ISTJ")
        if profile.mbti_isfj:
            mbpti_tags.append("ISFJ")
        if profile.mbti_infj:
            mbpti_tags.append("INFJ")
        if profile.mbti_intj:
            mbpti_tags.append("INTJ")
        if profile.mbti_istp:
            mbpti_tags.append("ISTP")
        if profile.mbti_isfp:
            mbpti_tags.append("ISFP")
        if profile.mbti_infp:
            mbpti_tags.append("INFP")
        if profile.mbti_intp:
            mbpti_tags.append("INTP")
        if profile.mbti_estp:
            mbpti_tags.append("ESTP")
        if profile.mbti_esfp:
            mbpti_tags.append("ESFP")
        if profile.mbti_enfp:
            mbpti_tags.append("ENFP")
        if profile.mbti_entp:
            mbpti_tags.append("ENTP")
        if profile.mbti_estj:
            mbpti_tags.append("ESTJ")
        if profile.mbti_esfj:
            mbpti_tags.append("ESFJ")
        if profile.mbti_enfj:
            mbpti_tags.append("ENFJ")
        if profile.mbti_entj:
            mbpti_tags.append("ENTJ")
        
        if len(mbpti_tags):
            if (len(mbpti_tags) == 1):
                prompt += f" for readers with an MBTI personality type of {mbpti_tags[0]}."
            elif len(mbpti_tags) == 2:
                prompt += f" for readers with MBTI personality types of {mbpti_tags[0]} and {mbpti_tags[1]}."
            else:
                mbpti_tags[len(mbpti_tags) - 1] = f"and {mbpti_tags[len(mbpti_tags) - 1]}"
                prompt += f" for readers with MBTI personality types of {', '.join(mbpti_tags)}."

        #realms & disciplines
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

        if (len(realm_tags) & len(philosophy_tags)):
            tags = realm_tags + philosophy_tags
            prompt += f" Focus results on works with {', '.join(tags)} themes"
        elif len(realm_tags):
            prompt += f" Focus results on works that are {', '.join(realm_tags)} in nature"
        elif len(philosophy_tags):
            prompt += f" Focus results on works with {', '.join(philosophy_tags)} themes"
        
        if form_data.get('realm'):
            prompt += f" that are {form_data['realm']} in nature"
        
        # reading time
        if form_data.get('mediaLength'):
            if form_data['mediaLength'] == "short":
                time = "between 1 to 3 hours"
            if form_data['mediaLength'] == "medium":
                time = "between 4 to 10 hours"
            if form_data['mediaLength'] == "long":
                time = "longer than 10 hours"
            prompt += f" and will take an advanced reader {time} to complete"

        prompt += "."


        if form_data.get('includeBookshelf'):
            prompt += f" The reader has already read {user_books}, so exclude these titles from your recommendations."

        # if file_content:
        #     prompt += f" {file_content}."

        
        prompt += " Thank you!"   
        
        # Add any additional form data to the prompt
        return prompt
    
    # format_json_from_response converts the response to a JSON object
    def format_json_from_response(response):
        response = response.replace("\n", "")
        clean_json = response.replace("```json", "").replace("```", "").strip()
        loaded_json = json.loads(clean_json)
        return loaded_json
    
    if current_user.is_authenticated:
        profile = db.session.query(Profile).filter_by(user_id=current_user.id).first()

    formatted_content = build_query_text(form_data, file_content, profile)
    print(formatted_content)
    try:
        # Create a request to the client.chat.completions object
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system", 
                    "content": "As an expert Russian Literature bot, your role is to offer relevant, specified recommendations. Ensure your search results are limited to works by Russian authors, with suggestions that are both non-obvious and expansive. Provide each response in a JSON object containing a title, author, and description. Thank you for your help!",
                    "metadata": {
                        "tags": ["Russian Literature", "Recommendations"]
                    },
                },
                {
                    "role": "user", 
                    "content": formatted_content
                }
            ],
        )
        
        # Log the full response for debugging
        print("OpenAI Response:", len(response.choices))

        # Ensure the response contains choices
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("OpenAI response is empty or malformed.")

        # Convert the JSON string
        gpt_res = response.choices[0].message.content
        loaded_json = format_json_from_response(gpt_res)
        
        return jsonify({
            "response": loaded_json,
            "file_data": file_content
        })

    except Exception as e:
        print(f"Error fetching data from OpenAI: {e}")
        return jsonify({"error": "Failed to fetch data from OpenAI", "details": str(e)}), 500


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

# users save books to their profile
@user_bp.route('/user/<id>/books', methods=['GET'])
def get_user_books(id):
    user = User.query.get(id)
    if user:
        books = db.session.query(Book).join(users_books, Book.id == users_books.c.book_id).filter(users_books.c.user_id == id).all()
        books_data = [{"id": book.id, "isbn": book.isbn, "title": book.title, "author": book.author} for book in books]
        return jsonify(books_data)