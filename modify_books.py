#!/usr/bin/env python3
"""
Cron job script to randomly modify books in the database.
This simulates a daily/bi-daily process that updates book prices, stock, etc.
Typically modifies 10-200 books to simulate realistic e-commerce changes.
"""

import sqlite3
import random
import argparse
from datetime import datetime


def get_random_books(cursor, count=50):
    """Get random books from the database"""
    cursor.execute("SELECT id, title, price, stock_quantity FROM books ORDER BY RANDOM() LIMIT ?", (count,))
    return cursor.fetchall()


def modify_book_price(cursor, book_id, current_price):
    """Randomly modify book price (realistic price changes)"""
    # Small price adjustments: +/- 5-15%
    change_percent = random.uniform(0.05, 0.15)
    direction = random.choice([1, -1])
    new_price = round(current_price * (1 + direction * change_percent), 2)
    
    # Ensure price stays reasonable ($5 minimum, $100 maximum)
    new_price = max(5.0, min(100.0, new_price))
    
    cursor.execute("""
        UPDATE books 
        SET price = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_price, book_id))
    
    return new_price


def modify_book_stock(cursor, book_id, current_stock):
    """Randomly modify book stock quantity (sales/restocking simulation)"""
    # Realistic stock changes: sales (-1 to -10) or restocking (+5 to +20)
    if random.random() < 0.7:  # 70% chance of sales (stock decrease)
        change = random.randint(-10, -1)
    else:  # 30% chance of restocking (stock increase)
        change = random.randint(5, 20)
    
    new_stock = max(0, current_stock + change)  # Don't go below 0
    
    cursor.execute("""
        UPDATE books 
        SET stock_quantity = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_stock, book_id))
    
    return new_stock


def modify_book_rating(cursor, book_id):
    """Slightly adjust book rating (new reviews)"""
    # Small rating changes: +/- 0.1 to 0.3
    current_rating = cursor.execute("SELECT average_rating FROM books WHERE id = ?", (book_id,)).fetchone()[0]
    if current_rating:
        change = random.uniform(-0.3, 0.3)
        new_rating = round(max(1.0, min(5.0, current_rating + change)), 2)
    else:
        new_rating = round(random.uniform(3.0, 4.5), 2)
    
    cursor.execute("""
        UPDATE books 
        SET average_rating = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_rating, book_id))
    
    return new_rating


def main():
    parser = argparse.ArgumentParser(description='Cron job to randomly modify books (simulates e-commerce changes)')
    parser.add_argument('--count', type=int, default=50, help='Number of books to modify (10-200 typical)')
    parser.add_argument('--db', default='bookstore.db', help='Database file path')
    parser.add_argument('--quiet', action='store_true', help='Minimal output for cron jobs')
    args = parser.parse_args()
    
    # Validate count range
    if args.count < 1 or args.count > 500:
        print("❌ Count should be between 1 and 500")
        return
    
    # Connect to database
    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    
    try:
        # Check if books exist
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        
        if book_count == 0:
            if not args.quiet:
                print("❌ No books found in database. Load books first with: curl -X POST http://localhost:5000/books/load-csv")
            return
        
        actual_count = min(args.count, book_count)
        
        if not args.quiet:
            print(f"📚 Found {book_count} books in database")
            print(f"🎲 Randomly modifying {actual_count} books (simulating e-commerce changes)...")
            print()
        
        # Get random books
        books = get_random_books(cursor, actual_count)
        
        modified_books = []
        price_changes = 0
        stock_changes = 0
        rating_changes = 0
        
        for book_id, title, current_price, current_stock in books:
            if not args.quiet:
                print(f"📖 {title}")
            
            modifications = []
            
            # 80% chance to modify price (common in e-commerce)
            if random.random() < 0.8:
                new_price = modify_book_price(cursor, book_id, current_price)
                modifications.append(f"Price: ${current_price:.2f} → ${new_price:.2f}")
                price_changes += 1
            
            # 60% chance to modify stock (sales/restocking)
            if random.random() < 0.6:
                new_stock = modify_book_stock(cursor, book_id, current_stock)
                modifications.append(f"Stock: {current_stock} → {new_stock}")
                stock_changes += 1
            
            # 20% chance to modify rating (new reviews)
            if random.random() < 0.2:
                new_rating = modify_book_rating(cursor, book_id)
                modifications.append(f"Rating: → {new_rating}⭐")
                rating_changes += 1
            
            if modifications and not args.quiet:
                print(f"   ✅ {', '.join(modifications)}")
                modified_books.append({
                    'id': book_id,
                    'title': title,
                    'changes': modifications
                })
            elif not args.quiet:
                print("   ⏭️  No changes")
            
            if not args.quiet:
                print()
        
        # Commit changes
        conn.commit()
        
        if args.quiet:
            # Minimal output for cron jobs
            print(f"Modified {len(modified_books)} books: {price_changes} prices, {stock_changes} stock, {rating_changes} ratings")
        else:
            print("🎉 E-commerce simulation complete!")
            print(f"📊 Summary:")
            print(f"   • {len(modified_books)} books modified")
            print(f"   • {price_changes} price changes")
            print(f"   • {stock_changes} stock changes") 
            print(f"   • {rating_changes} rating changes")
            print()
            print("💡 Check changed books with:")
            print("   curl http://localhost:5000/books/changed")
            print("   curl 'http://localhost:5000/books/changed?hours=1'  # last hour only")
        
    except Exception as e:
        if args.quiet:
            print(f"Error: {e}")
        else:
            print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main() 