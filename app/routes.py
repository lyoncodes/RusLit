import os
from flask import render_template, request, redirect, url_for, jsonify, Blueprint, flash
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from . import app, db  # Import db
from openai import OpenAI
from dotenv import load_dotenv
from .models import User, Book, users_books  # Import the User, Book models and linking table
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urljoin

login_manager = LoginManager()
login_manager.init_app(app)

# Load environment variables from .env file
load_dotenv()
user_bp = Blueprint('user_bp', __name__)
token = os.getenv("GITHUB_TOKEN")
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
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
    if request.method == 'POST':
        # Handle form submission here
        # For example, you can access form data using request.form
        return redirect(url_for('home'))  # Redirect after submission
    return render_template('form.html')

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password using pbkdf2:sha256
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
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
    if request.method == 'POST':
        genre = request.form.get('genre')
        novel = request.form.get('novel') == 'on'
        short_story = request.form.get('short_story') == 'on'
        poetry = request.form.get('poetry') == 'on'
        satire = request.form.get('satire') == 'on'
        romance = request.form.get('romance') == 'on'
        psychological = request.form.get('psychological') == 'on'
        spiritual = request.form.get('spiritual') == 'on'
        
        profile = Profile.query.filter_by(user_id=current_user.id).first()
        if profile:
            profile.novel = novel
            profile.short_story = short_story
            profile.poetry = poetry
            profile.satire = satire
            profile.romance = romance
            profile.psychological = psychological
            profile.spiritual = spiritual
        else:
            profile = Profile(
                user_id=current_user.id,
                novel=novel,
                short_story=short_story,
                poetry=poetry,
                satire=satire,
                romance=romance,
                psychological=psychological,
                spiritual=spiritual
            )
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', id=current_user.id))
    
    if user:
        return render_template('profile.html', user=user)
    else:
        return {"error": "User not found"}, 404

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Process the form data here
    form_data = request.form.to_dict()
    file = request.files.get('file')
    file_content = ""
    
    # Save the file if it exists and process its content
    if file:
        file_path = os.path.join('', file.filename)
        file.save(file_path)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            file_content = ', '.join(line.strip() for line in lines)
    
    # handle the file content 
    def format_content(form_data, file_content):
        prompt = ''
        if len(file_content):
            prompt += f"Based off the following titles: {file_content}, "
            
        if form_data.get('classification'):
            prompt += f"recommend a list of {form_data['classification']} from Russian Literature."

        if form_data.get('satire'):
            prompt += f" Focus search results on {form_data['satire']}"

        if form_data.get('realm') == "psychology":
            form_data['realm'] = "psychological"
        else:
            form_data['realm'] = "spiritual"
        
        prompt += f" works that explore {form_data['realm']} themes."
        return prompt
    
    formatted_content = format_content(form_data, file_content)
    # Process the form data here
    # Create a request to the client.chat.completions object
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system", 
                "content": "As an expert Russian Literature bot, your role is to offer relevant, specified recommendations. Ensure your search results are limited to works by Russian authors, with suggestions that are both non-obvious and expansive.",
                "metadata" : {
                    "tags": ["Russian Literature", "Recommendations"]
                },
            },
            {
                "role": "user", 
                "content": formatted_content
            }
        ],
    )
    
    # Print the response from OpenAI
    answer = response.choices[0].message.content
    # Parse the response into a custom object
    response_lines = answer.split('\n')
    response_data = []
    current_title = ""
    current_description = ""
    print(response_lines)
    for line in response_lines:
        if line.startswith("###"):
            if current_title:
                response_data.append({"title": current_title, "description": current_description})
            current_title = line.replace("Title:", "").strip()
            current_description = ""
        elif line.startswith("Description:"):
            current_description = line.replace("Description:", "").strip()
        else:
            current_description += " " + line.strip()
    
    if current_title:
        response_data.append({"title": current_title, "description": current_description})
    
    return jsonify({
        "response": response_data,
        "file_data": file_content
    })

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
    else:
        return {"error": "User not found"}, 404

from app.models import Profile
