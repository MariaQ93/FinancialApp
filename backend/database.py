from tinydb import TinyDB, Query

# Initialize the database
db = TinyDB('stocks.json')
Stock = Query()

# Tables
stock_transactions = db.table('stock_transactions')
portfolio_table = db.table('portfolio')
history_asset_table = db.table('history_asset')
users_table = db.table('users')  # For user authentication
