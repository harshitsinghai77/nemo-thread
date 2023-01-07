import sqlite3

DB_NAME = "html_cache.db"


class SqliteContextManager:
    def __init__(self):
        self.db_name = DB_NAME

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
