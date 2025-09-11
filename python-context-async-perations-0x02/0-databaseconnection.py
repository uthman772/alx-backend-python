import sqlite3

class DatabaseConnection:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

# Example usage
if __name__ == "__main__":
    # Setup: create a sample database and table if not exists
    with sqlite3.connect("example.db") as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
        cur.execute("INSERT OR IGNORE INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob')")
        conn.commit()

    # Use the custom context manager
    with DatabaseConnection("example.db") as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        print(results)