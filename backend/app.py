from flask import Flask, jsonify, request
import yfinance as yf
from tinydb import TinyDB, Query
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from database import stock_transactions, portfolio_table, users_table, history_asset_table
from flask_cors import CORS
from datetime import datetime, timezone
import pandas as pd
import math
from cachetools import TTLCache
from models import StockTransaction, Portfolio, HistoryAsset, User, find_user_by_username

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret-key' 

CORS(app, supports_credentials=True)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Create a cache with a TTL of 5 minutes and a maximum size of 100 items
stock_cache = TTLCache(maxsize=100, ttl=300)

def get_cached_stock_list(tickers):
    result = []
    query_list = []
    for ticker in tickers:
        if ticker in stock_cache:
            result.append(stock_cache[ticker])
        else:
            query_list.append(ticker)
    
    query_res = yf.Tickers(' '.join(query_list))
            
    for ticker in query_res.tickers:
        # Get stock information
        stock = query_res.tickers[ticker]
        stock_cache[ticker] = stock
        result.append(stock)
    
    return result
    

def get_cached_stock(ticker):
    if ticker in stock_cache:
        return stock_cache[ticker]
    stock = yf.Ticker(ticker)
    stock_cache[ticker] = stock
    return stock

# Endpoint: User Signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['email']
    password = data['password']

    # Check if the user already exists
    user = find_user_by_username(username)
    if user:
        return jsonify({"error": "User already exists!"}), 400

    # Hash the password and store the user
    # When users first sign up, they start with a balance of $10000
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    # users_table.insert({'username': username, 'password': hashed_password, 'balance': 10000})
    users_table.insert(
        {
            'username': username, 
            'password': hashed_password, 
            'balance': 10000, 
            'created_at': datetime.now(timezone.utc).isoformat()
            })
    
    # Create JWT token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# Endpoint: User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['email']
    password = data['password']

    # Find the user in the database
    user = find_user_by_username(username)
    if not user:
        return jsonify({"error": "User does not exist!"}), 400

    # Verify the password
    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid password!"}), 400

    # Create JWT token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token, email=username)

# Endpoint: Get User Transactions (Requires Authentication)
@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user = find_user_by_username(current_user)
    transactions = stock_transactions.search(Query().uid == user.doc_id)
    total_num_trans = len(transactions)
    start = (page - 1) * per_page
    end = start + per_page
    
    page_trans = transactions[start:end]
    for transaction in page_trans:
        transaction['price'] = round(transaction['price'], 2)
        transaction['created_at'] = transaction['created_at'].split('T')[0]
    
    result = {
        "total": total_num_trans,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_num_trans / per_page),
        "data": page_trans
    }
    
    return jsonify(result)

# Endpoint: Get User Portfolio (Requires Authentication)
@app.route('/portfolio', methods=['GET'])
@jwt_required()
def view_portfolio():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_user = get_jwt_identity()
    print("current_user", current_user)
    user = find_user_by_username(current_user)
    print("user", user)
    # get all the stocks in the user's portfolio
    portfolios = portfolio_table.search(Query().uid == user.doc_id)
    total_num_companies = len(portfolios)
    start = (page - 1) * per_page
    end = start + per_page
    
    page_portfolios = portfolios[start:end]
    stock_data = []
    for portfolio in page_portfolios:
        ticker = portfolio['ticker']
        quantity = portfolio['total_quantity']
        stock = get_cached_stock(ticker)
        current_price = stock.history(period="1d")['Close'][0]
        stock_info = stock.info
        previous_close = stock_info.get('regularMarketPreviousClose', 'N/A')  # Previous Close Price
        day_change = current_price - previous_close if current_price != 'N/A' and previous_close != 'N/A' else 'N/A'  # Change in a day
        day_change_percent = (day_change / previous_close) * 100 if day_change != 'N/A' and previous_close != 'N/A' else 'N/A'
        created_at = portfolio.get('created_at')
        updated_at = portfolio.get('updated_at')
        timestamp = updated_at if updated_at else created_at
        stock_data.append({
            'ticker': ticker,
            'company_name': stock.info.get('longName', 'N/A'),
            'timestamp': timestamp.split('T')[0],
            'quantity': quantity,
            'day_change': round(day_change, 2),
            'day_change_percent': day_change_percent,
            'price': round(current_price, 2),
            'total_value': round(current_price * quantity, 2)
        })
    
    

    result = {
        "total": total_num_companies,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_num_companies / per_page),
        "data": stock_data
    }
    
    return jsonify(result)

# Endpoint: Buy Stock
@app.route('/buy', methods=['POST'])
@jwt_required()
def buy_stock():
    data = request.json
    ticker = data['ticker']
    quantity = data['quantity']

    # Fetch current stock price
    stock = get_cached_stock(ticker)
    price = stock.history(period="1d")['Close'][0]
    
    # Check if the user has enough balance
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    if user['balance'] < (price * quantity):
        return jsonify({"message": "Not enough balance"}), 400

    # Record the transaction in TinyDB
    stock_transactions.insert({
        'uid': user.doc_id,
        'ticker': ticker,
        'action': 'BUY',
        'quantity': quantity,
        'price': price,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Update the user's balance
    new_balance = user['balance'] - (price * quantity)
    users_table.update({'balance': new_balance}, Query().username == current_user)
    
    # Update or add to the portfolio
    portfolio_item = portfolio_table.get((Query().ticker == ticker) & (Query().uid == user.doc_id))
    if portfolio_item:
        portfolio_table.update({'total_quantity': portfolio_item['total_quantity'] + quantity , 'updated_at': datetime.now(timezone.utc).isoformat()}, (Query().ticker == ticker) & (Query().uid == user.doc_id))
    else:
        portfolio_table.insert({'uid': user.doc_id ,'ticker': ticker, 'total_quantity': quantity, 'created_at': datetime.now(timezone.utc).isoformat()})

    return jsonify({"message": "Stock purchased successfully!"})

# Endpoint: Sell Stock
@app.route('/sell', methods=['POST'])
@jwt_required()
def sell_stock():
    data = request.json
    ticker = data['ticker']
    quantity = data['quantity']

    # Check portfolio for available stock
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    portfolio_item = portfolio_table.get((Query().ticker == ticker) & (Query().uid == user.doc_id))
    if not portfolio_item or portfolio_item['total_quantity'] < quantity:
        return jsonify({"message": "Not enough stock to sell"}), 400

    # Fetch current stock price
    stock = get_cached_stock(ticker)
    price = stock.history(period="1d")['Close'][0]

    # Record the transaction in TinyDB
    stock_transactions.insert({
        'uid': user.doc_id,
        'ticker': ticker,
        'action': 'SELL',
        'quantity': quantity,
        'price': price,
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    # Update the user's balance
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    new_balance = user['balance'] + (price * quantity)
    users_table.update({'balance': new_balance}, Query().username == current_user)
    
    # Update the portfolio
    new_quantity = portfolio_item['total_quantity'] - quantity
    if new_quantity == 0:
        portfolio_table.remove((Query().ticker == ticker) & (Query().uid == user.doc_id))
    else:
        portfolio_table.update({'total_quantity': new_quantity, 'updated_at': datetime.now(timezone.utc).isoformat()}, (Query().ticker == ticker) & (Query().uid == user.doc_id))

    return jsonify({"message": "Stock sold successfully!"})


# Endpoint: Get Stock Price, not using path parameters
@app.route('/stock', methods=['GET'])
def get_stock():
    ticker = request.args.get('stock')
    stock = get_cached_stock(ticker)
    # print everything in the stock object
    data = stock.history(period="1d")
    if len(data['Close']) > 0:
        return jsonify({
            "ticker": ticker,
            "price": data['Close'][0]
        })
    else:
        return jsonify({
            "ticker": ticker,
            "price": "N/A"
        })

# Endpoint: List by stock sambol
@app.route('/listBySymbol', methods=['GET'])
def get_stock_by_symbol():
    symbol = request.args.get('symbol')
    stock = get_cached_stock(symbol)
    stock_info = stock.info

    result = {
        "total": 0,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
    }
    
    # Extract relevant data
    company_name = stock_info.get('longName', 'N/A')
    history_price = stock.history(period="1d")
    
    if len(history_price['Close']) <= 0:
        return jsonify(result)
    
    current_price = history_price['Close'][0]
    previous_close = stock_info.get('regularMarketPreviousClose', 'N/A')
    day_change = current_price - previous_close if current_price != 'N/A' and previous_close != 'N/A' else 'N/A'
    day_change_percent = (day_change / previous_close) * 100 if day_change != 'N/A' and previous_close != 'N/A' else 'N/A'
    volume = stock_info.get('volume', 'N/A')
    
    stock_data = {
        'ticker': symbol,
        'company_name': company_name,
        'current_price': current_price,
        'day_change': day_change,
        'day_change_percent': day_change_percent,
        'volume': volume
    }
    
    result = {
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1,
        "data": stock_data
    }
    
    return jsonify(result)
        

# Endpoint: Get top stocks by sector
@app.route('/listBySector', methods=['GET'])
def get_sectors():
    sector = request.args.get('sector')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    sector_data = yf.Sector(sector)
    print(sector_data.overview.get('companies_count'))
    top_companies_df = sector_data.top_companies
    
    # sector_data.top_companies is a DataFrame. You can iterate over it to get the top companies in the sector
    companies = top_companies_df.index.tolist()
    total_num_companies = len(companies)
    start = (page - 1) * per_page
    end = start + per_page
    page_companies = companies[start:end]
    
    stock_list = get_cached_stock_list(page_companies)
    
    stock_data = []
    for stock in stock_list:
        # Get stock information
        stock_info = stock.info

        # Extract relevant data
        ticker = stock_info.get('symbol', 'N/A')  # Ticker Symbol
        company_name = stock_info.get('longName', 'N/A')  # Company Name
        history_price = stock.history(period="1d")
        current_price = history_price['Close'][0]  # Current Price
        previous_close = stock_info.get('regularMarketPreviousClose', 'N/A')  # Previous Close Price
        day_change = current_price - previous_close if current_price != 'N/A' and previous_close != 'N/A' else 0  # Change in a day
        day_change_percent = (day_change / previous_close) * 100 if day_change != 'N/A' and previous_close != 'N/A' else 0
        volume = stock_info.get('volume', 'N/A')  # Volume
        historical_data = stock.history(period="1mo")
        historical_dates = historical_data.index.strftime('%Y-%m-%d').tolist()
        historical_prices = historical_data['Close'].round(2).tolist()
        stock_data.append({
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price.round(2),
            'day_change': day_change,
            'day_change_percent': day_change_percent,
            "historical_dates": historical_dates,
            "historical_prices": historical_prices,
            'volume': volume
        })

    result = {
        "total": total_num_companies,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_num_companies / per_page),
        "data": stock_data
    }
    
    return jsonify(result)

# Endpoint: get users' balance
@app.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    return jsonify({"balance": user['balance']})

# Endpoint: deposit money
@app.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    data = request.json
    amount = data['amount']
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    new_balance = user['balance'] + amount if 'balance' in user else amount
    users_table.update({'balance': new_balance}, Query().username == current_user)
    return jsonify({"message": "Deposit successful!"})

# Endpoint: withdraw money
@app.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    data = request.json
    amount = data['amount']
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    if user['balance'] < amount:
        return jsonify({"error": "Not enough balance"}), 400
    new_balance = user['balance'] - amount
    users_table.update({'balance': new_balance}, Query().username == current_user)
    return jsonify({"message": "Withdrawal successful!"})

# Endpoint: get user total asset value (balance + stock value) every day
@app.route('/asset', methods=['GET'])
@jwt_required()
def get_asset():
    current_user = get_jwt_identity()
    print("current_user", current_user)
    user = find_user_by_username(current_user)
    print("user", user)
    balance = user['balance']
    total_value = balance
    labels = []
    values = []
    
    # get history asset value
    history_asset = history_asset_table.search(Query().uid == user.doc_id)
    for asset in history_asset:
        labels.append(asset['date'])
        values.append(asset['total_value'])
    
    # get today date as yyyy-mm-dd
    now = datetime.now().isoformat()
    today = now.split('T')[0]
    
    labels.append(today)
    portfolio = portfolio_table.search(Query().uid == user.doc_id)
    for stock in portfolio:
        ticker = stock['ticker']
        quantity = stock['total_quantity']
        stock = get_cached_stock(ticker)
        price = stock.history(period="1d")['Close'][0]
        total_value += price * quantity
    values.append(total_value)
    
    result = {"labels": labels, "values": values}
    return jsonify(result)

# Endpoint: update user's portfolio every day
@app.route('/updatePortfolio', methods=['POST'])
def update_portfolio():
    username = request.json.get('username')
    date = request.json.get('date')
    user = find_user_by_username(username)
    total_value = request.json.get('total_value')
    user_id = user.doc_id
    history_asset_table.upsert({'uid': user_id, 'total_value': total_value, 'date': date}, (Query().uid == user_id) & (Query().date == date))
    return jsonify({"message": "Portfolio updated successfully!"})

# Endpoint: get a user's watchlist
@app.route('/watchlist', methods=['GET'])
@jwt_required()
def get_watchlist():
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    watchlist = user.get('watchlist', [])
    result = []
    for symbol in watchlist:
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        price = stock.history(period="1d")['Close'][0]
        result.append({
            'symbol': symbol,
            'price': round(price, 2)
        })
        
    return jsonify(result)

# Endpoint: add a stock to a user's watchlist
@app.route('/watchlist', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    data = request.json
    symbol = data['symbol']
    watchlist = user.get('watchlist', [])
    if symbol not in watchlist:
        watchlist.append(symbol)
        users_table.update({'watchlist': watchlist}, Query().username == current_user)
    return jsonify({"message": "Stock added to watchlist!"})

# Endpoint: remove a stock from a user's watchlist
@app.route('/watchlist', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist():
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    symbol = request.args.get('symbol')
    watchlist = user.get('watchlist', [])
    if symbol in watchlist:
        watchlist.remove(symbol)
        users_table.update({'watchlist': watchlist}, Query().username == current_user)
    return jsonify({"message": "Stock removed from watchlist!"})

# Endpoint: get user's asset constituents
@app.route('/assetConstituents', methods=['GET'])
@jwt_required()
def get_asset_constitution():
    current_user = get_jwt_identity()
    user = find_user_by_username(current_user)
    portfolio = portfolio_table.search(Query().uid == user.doc_id)
    balance = user['balance']
    result = []
    
    result.append({
        'name': 'balance',
        'value': balance
    })
    for stock in portfolio:
        ticker = stock['ticker']
        quantity = stock['total_quantity']
        stock = get_cached_stock(ticker)
        price = stock.history(period="1d")['Close'][0]
        total_value = price * quantity
        result.append({
            'name': ticker,
            'value': total_value
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
