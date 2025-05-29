import os
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, g
import logging
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['DATABASE'] = 'bookstore.db'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database helper functions
def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with book table"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Create books table (simplified - no sync tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn13 TEXT UNIQUE,
                isbn10 TEXT,
                title TEXT NOT NULL,
                subtitle TEXT,
                authors TEXT,
                categories TEXT,
                thumbnail TEXT,
                description TEXT,
                published_year INTEGER,
                average_rating REAL,
                num_pages INTEGER,
                ratings_count INTEGER,
                stock_quantity INTEGER DEFAULT 10,
                price REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT NULL
            )
        ''')
        
        # Create index on ISBN13 for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_isbn13 ON books(isbn13)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_updated ON books(last_updated)')
        
        db.commit()
        logger.info("Database initialized successfully")

def load_csv_data():
    """Load book data from CSV file into database"""
    try:
        # Read CSV file
        df = pd.read_csv('data/data.csv')
        
        # Clean column names (remove any extra spaces)
        df.columns = df.columns.str.strip()
        
        db = get_db()
        cursor = db.cursor()
        
        # Insert books from CSV
        books_inserted = 0
        for _, row in df.iterrows():
            try:
                # Calculate price based on rating (simple formula)
                rating = float(row.get('average_rating', 3.0)) if pd.notna(row.get('average_rating')) else 3.0
                price = round(rating * 5 + 5, 2)  # Price between $10-25 based on rating
                
                # DON'T set last_updated when loading from CSV - only when actually modifying
                cursor.execute('''
                    INSERT OR REPLACE INTO books 
                    (isbn13, isbn10, title, subtitle, authors, categories, 
                     thumbnail, description, published_year, average_rating, 
                     num_pages, ratings_count, stock_quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row.get('isbn13', '')).strip(),
                    str(row.get('isbn10', '')).strip(),
                    str(row.get('title', '')).strip(),
                    str(row.get('subtitle', '')).strip() if pd.notna(row.get('subtitle')) else None,
                    str(row.get('authors', '')).strip(),
                    str(row.get('categories', '')).strip(),
                    str(row.get('thumbnail', '')).strip() if pd.notna(row.get('thumbnail')) else None,
                    str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                    int(row.get('published_year', 0)) if pd.notna(row.get('published_year')) else None,
                    rating,
                    int(row.get('num_pages', 0)) if pd.notna(row.get('num_pages')) else None,
                    int(row.get('ratings_count', 0)) if pd.notna(row.get('ratings_count')) else None,
                    10,  # Default stock quantity
                    price
                ))
                books_inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert book: {e}")
                continue
        
        db.commit()
        logger.info(f"Successfully loaded {books_inserted} books from CSV")
        return books_inserted
        
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        return 0

# API Routes

@app.route("/")
def hello_world():
    """Health check endpoint"""
    return {
        "message": "Bookstore Flask API is running!",
        "code": 200,
        "endpoints": [
            "/books/changed - GET recently changed books (last 24 hours)",
            "/books/load-csv - POST load books from CSV - only on initial load"
        ]
    }

@app.route("/books/changed", methods=["GET"])
def get_changed_books():
    """Get books that have been actually modified (not just loaded from CSV)"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get hours parameter (default 24 hours)
        hours = int(request.args.get('hours', 24))
        
        # Get books that have been MODIFIED (have a last_updated timestamp)
        # CSV loading doesn't set last_updated, only actual modifications do
        cursor.execute('''
            SELECT id, isbn13, isbn10, title, subtitle, authors, categories, 
                   thumbnail, description, published_year, average_rating, 
                   num_pages, ratings_count, stock_quantity, price, last_updated
            FROM books 
            WHERE last_updated IS NOT NULL 
            AND last_updated > datetime('now', '-{} hours')
            ORDER BY last_updated DESC
        '''.format(hours))
        
        changed_books = []
        for row in cursor.fetchall():
            book_dict = dict(row)
            book_dict['changedAt'] = book_dict['last_updated']  # Add changedAt field
            changed_books.append(book_dict)
        
        # Get total count for info
        cursor.execute('SELECT COUNT(*) FROM books')
        total_books = cursor.fetchone()[0]
        
        return jsonify({
            "changed_books": changed_books,
            "count": len(changed_books),
            "total_books_in_db": total_books,
            "hours_checked": hours,
            "timestamp": datetime.now().isoformat(),
            "message": f"Found {len(changed_books)} books actually modified in last {hours} hours"
        })
        
    except Exception as e:
        logger.error(f"Error getting changed books: {e}")
        return jsonify({"error": "Failed to retrieve changed books"}), 500

@app.route("/books/load-csv", methods=["POST"])
def load_books_from_csv():
    """Load books from CSV file into database"""
    try:
        books_loaded = load_csv_data()
        return jsonify({
            "message": f"Successfully loaded {books_loaded} books from CSV",
            "books_loaded": books_loaded
        })
    except Exception as e:
        logger.error(f"Error loading books from CSV: {e}")
        return jsonify({"error": "Failed to load books from CSV"}), 500

# App teardown
@app.teardown_appcontext
def close_db_teardown(error):
    close_db()

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

