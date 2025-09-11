import sqlite3

class ExecuteQuery:
    def __init__(self, query, params=None, db_path=":memory:"):
        self.query = query
        self.params = params if params is not None else ()
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.query, self.params)
        return self.cursor.fetchall()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

# Example usage:
if __name__ == "__main__":
    # Setup test database and table
    with sqlite3.connect(":memory:") as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        c.executemany("INSERT INTO users (name, age) VALUES (?, ?)", [
            ("Alice", 30),
            ("Bob", 20),
            ("Charlie", 40),
        ])
        conn.commit()

    # Use the context manager to execute the query
    query = "SELECT * FROM users WHERE age > ?"
    params = (25,)
    with ExecuteQuery(query, params, db_path=":memory:") as result:
        print(result)