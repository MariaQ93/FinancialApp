from flask_sqlalchemy import SQLAlchemy
from database import stock_transactions, portfolio_table, users_table
from tinydb import Query

db = SQLAlchemy()

class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(4), nullable=False)  # 'BUY' or 'SELL'
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

class HistoryAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, primary_key=True)
    total_value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    
# User model
# user has uid, username(email), hashed password, balance, and created_at, updated_at
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

# User functions

# Add a new user to the TinyDB
def add_user(username, password, email):
    # Check if the user already exists
    if users_table.get(Query().username == username):
        return {"error": "User already exists!"}
    
    # Insert new user with hashed password
    users_table.insert({
        'username': username,
        'password': password,
        'email': email,
        'created_at': datetime.utcnow().isoformat()
    })
    return {"message": "User created successfully!"}

# Cache to store user data
user_cache = {}

# Retrieve user from cache or database
def find_user_by_username(username):# Check if user is in cache
    if username in user_cache:
        return user_cache[username]
    
    # If not in cache, retrieve from database
    user = users_table.get(Query().username == username)
    
    # Store in cache if found
    if user:
        user_cache[username] = user
    
    return user

# List all users (for admin purposes, if needed)
def list_all_users():
    return users_table.all()