import os
from flask import render_template, request, redirect, url_for, jsonify, Blueprint, flash
from . import app, db  # Import db
from openai import OpenAI
from dotenv import load_dotenv
from .models import User, Book, users_books  # Import the User, Book models and linking table
from werkzeug.security import generate_password_hash

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

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle form submission here
        # For example, you can access form data using request.form
        return redirect(url_for('home'))  # Redirect after submission
    return render_template('form.html')

@app.route('/instructions', methods=['GET'])
def instructions():
    return render_template('instructions.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login form submission here
        # For example, you can access form data using request.form
        return redirect(url_for('home'))  # Redirect after submission
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
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
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

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
