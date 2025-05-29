# Bookstore Flask API

A simple Flask API that simulates an e-commerce book database with periodic updates. Designed to provide changed book data to Next.js e-shop servers via polling.

## 🎯 Purpose

-   **Cron Job**: Runs every 12 hours to modify 10-200 books (prices, stock, ratings)
-   **API Endpoint**: Provides recently changed books (last 24 hours) for Next.js to poll
-   **No Sync Tracking**: This server doesn't care about external systems - just provides recent changes

## ⚡ Quick Start

1. **Install & Run:**

    ```bash
    uv sync
    python app.py
    ```

2. **Load Initial Data:**

    ```bash
    curl -X POST http://localhost:5000/books/load-csv
    ```

3. **Simulate E-commerce Changes:**

    ```bash
    python modify_books.py --count 50
    ```

4. **Check Recent Changes:**
    ```bash
    curl http://localhost:5000/books/changed
    ```

## 📡 API Endpoints

### `GET /books/changed`

Returns books modified in the last 24 hours (configurable).

**Parameters:**

-   `hours` (optional) - Hours to look back (default: 24)

**Example:**

```bash
# Last 24 hours (default)
curl http://localhost:5000/books/changed

# Last 1 hour only
curl "http://localhost:5000/books/changed?hours=1"

# Last week
curl "http://localhost:5000/books/changed?hours=168"
```

**Response:**

```json
{
    "changed_books": [
        {
            "id": 42,
            "title": "The Great Gatsby",
            "authors": "F. Scott Fitzgerald",
            "price": 18.99,
            "stock_quantity": 15,
            "changedAt": "2024-01-15T14:30:00",
            "isbn13": "9780743273565"
        }
    ],
    "count": 1,
    "hours_checked": 24,
    "total_books_in_db": 6810,
    "message": "Found 1 books changed in last 24 hours"
}
```

### `POST /books/load-csv`

Loads books from the CSV file (run once initially).

## 🤖 Automated Updates

### Cron Job Setup

Add to your crontab to run every 12 hours:

```bash
crontab -e
# Add this line:
0 */12 * * * /path/to/your/project/cron_job.sh >> /var/log/bookstore_cron.log 2>&1
```

Or use the provided script:

```bash
./cron_job.sh  # Test the cron job manually
```

### Manual Updates

Simulate realistic e-commerce changes:

```bash
# Modify 50 books (realistic daily changes)
python modify_books.py --count 50

# Larger update (bi-weekly inventory)
python modify_books.py --count 150

# Quiet mode for cron jobs
python modify_books.py --count 80 --quiet
```

## 🏗️ For Your Next.js Server

### Polling Setup

Your Next.js server should poll the endpoint every few minutes:

```javascript
// pages/api/poll-book-changes.js
export default async function handler(req, res) {
    try {
        const response = await fetch(
            "http://your-flask-server:5000/books/changed"
        );
        const data = await response.json();

        if (data.changed_books.length > 0) {
            console.log(`Processing ${data.count} changed books`);

            // Update your Next.js database with the changed books
            for (const book of data.changed_books) {
                await updateBookInYourDatabase(book);
            }
        }

        res.json({
            processed: data.count,
            message: `Processed ${data.count} book changes`,
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}
```

### Cron Job for Next.js

In your Next.js project, set up a cron job:

```bash
# Every 5 minutes during business hours
*/5 9-17 * * * curl -X POST http://your-nextjs-server.com/api/poll-book-changes
```

## 📊 What Gets Changed

The cron job simulates realistic e-commerce changes:

-   **Prices**: ±5-15% adjustments (80% of books)
-   **Stock**: Sales (-1 to -10) or restocking (+5 to +20) (60% of books)
-   **Ratings**: Small adjustments from new reviews (20% of books)

## 🗃️ Database

SQLite database with simple book table:

-   `id`, `title`, `authors`, `price`, `stock_quantity`
-   `last_updated` - Tracks when book was last modified
-   Books appear in `/books/changed` when modified recently

## 🔄 Typical Workflow

1. **Initial Setup**: Load CSV data once
2. **Cron Job**: Runs every 12 hours, modifies 10-200 books
3. **Next.js Polling**: Checks for changes every few minutes
4. **Data Sync**: Next.js updates its database with recent changes

Perfect for keeping multiple e-commerce sites in sync! 🛍️
