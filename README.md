# Bookstore Flask REST API

A simplified Flask-based REST API for managing book data from CSV files and providing changed book data to Next.js e-shop servers via polling.

## Features

-   **SQLite Database**: Stores book data with change tracking
-   **CSV Data Import**: Load book data from CSV files
-   **Change Tracking**: Tracks which books have been modified since last sync
-   **Simple Polling Endpoint**: Single endpoint for Next.js server to poll for changes

## Quick Start

1. **Install Dependencies**:

    ```bash
    uv sync
    ```

2. **Run the API**:

    ```bash
    python app.py
    ```

3. **Load CSV Data**:

    ```bash
    curl -X POST http://localhost:5000/books/load-csv
    ```

4. **Check for changed books** (what your Next.js server will poll):
    ```bash
    curl http://localhost:5000/books/changed
    ```

## API Endpoints

### Health Check

-   `GET /` - API status and endpoint list

### Core Endpoints

-   `GET /books/changed` - Get books that have changed since last sync
-   `POST /books/load-csv` - Load books from CSV file into database
-   `POST /books/mark-synced` - Mark books as synced (after Next.js processes them)

## Usage Flow

1. **Load data**: `POST /books/load-csv` to load your CSV data
2. **Poll for changes**: Next.js server calls `GET /books/changed` on a cron schedule
3. **Process & mark synced**: Next.js processes the books and calls `POST /books/mark-synced`

## Example Usage

### Load Books from CSV

```bash
curl -X POST http://localhost:5000/books/load-csv
```

### Get Changed Books (for Next.js to poll)

```bash
curl http://localhost:5000/books/changed
```

Response:

```json
{
    "changed_books": [
        {
            "id": 1,
            "isbn13": "9780002005883",
            "title": "Gilead",
            "authors": "Marilynne Robinson",
            "price": 24.25,
            "stock_quantity": 10,
            "last_updated": "2024-01-01T12:00:00"
        }
    ],
    "count": 1,
    "total_books_in_db": 1000,
    "timestamp": "2024-01-01T12:00:00",
    "message": "Found 1 books that need syncing"
}
```

### Mark Books as Synced (after Next.js processes them)

```bash
curl -X POST http://localhost:5000/books/mark-synced \
  -H "Content-Type: application/json" \
  -d '{"book_ids": [1, 2, 3]}'
```

## Next.js Cron Job Example

Your Next.js server should poll the `/books/changed` endpoint:

```javascript
// pages/api/sync-books.js
export default async function handler(req, res) {
    try {
        // 1. Get changed books from Flask API
        const response = await fetch(
            "http://your-flask-server:5000/books/changed"
        );
        const data = await response.json();

        if (data.changed_books.length === 0) {
            return res.json({ message: "No books to sync" });
        }

        // 2. Process books (update your Next.js database)
        const processedIds = [];
        for (const book of data.changed_books) {
            // Update your database here
            await updateBookInDatabase(book);
            processedIds.push(book.id);
        }

        // 3. Mark books as synced in Flask API
        await fetch("http://your-flask-server:5000/books/mark-synced", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ book_ids: processedIds }),
        });

        res.json({
            message: `Synced ${processedIds.length} books`,
            synced_count: processedIds.length,
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}
```

## Database Schema

The SQLite database contains a `books` table with:

-   `id` - Primary key
-   `isbn13` - ISBN-13 (unique)
-   `title`, `authors`, `categories` - Book info
-   `price`, `stock_quantity` - E-commerce fields
-   `last_updated` - When book was last modified
-   `synced_at` - When book was last synced to Next.js

Books appear in `/books/changed` when `synced_at` is NULL or `last_updated > synced_at`.

## Development

-   Database file: `bookstore.db` (auto-created)
-   Port: 5000
-   Books get automatic pricing based on rating (rating × 5 + 5)
