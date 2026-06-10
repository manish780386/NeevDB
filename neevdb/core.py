"""
NeevDB - Core Database Engine
The main interface for all database operations.
"""

from .storage import Storage
from .query import QueryEngine
from datetime import datetime


class NeevDB:
    """
    NeevDB - A lightweight file-based database engine.

    Supports tables, CRUD operations, filtering, and SQL-like queries.
    All data is persisted automatically to a JSON file.

    Example:
        db = NeevDB("mydata.json")
        db.create_table("users")
        db.insert("users", {"name": "Alice", "age": 25})
        results = db.query("SELECT * FROM users WHERE age > 18")
    """

    def __init__(self, filepath: str = "neevdb.json"):
        self.storage      = Storage(filepath)
        self.query_engine = QueryEngine()
        print(f"[NeevDB] Connected to database: {filepath}")

    # ──────────────────────────────────────────────
    # Table Operations
    # ──────────────────────────────────────────────

    def create_table(self, table_name: str) -> bool:
        data = self.storage.read()
        if table_name in data["tables"]:
            print(f"[NeevDB] Table '{table_name}' already exists.")
            return False
        data["tables"][table_name] = []
        self.storage.save(data)
        print(f"[NeevDB] Table '{table_name}' created.")
        return True

    def drop_table(self, table_name: str) -> bool:
        data = self.storage.read()
        if table_name not in data["tables"]:
            print(f"[NeevDB] Table '{table_name}' not found.")
            return False
        del data["tables"][table_name]
        self.storage.save(data)
        print(f"[NeevDB] Table '{table_name}' dropped.")
        return True

    def list_tables(self) -> list:
        data   = self.storage.read()
        tables = list(data["tables"].keys())
        print(f"[NeevDB] Tables: {tables}")
        return tables

    # ──────────────────────────────────────────────
    # CRUD Operations
    # ──────────────────────────────────────────────

    def insert(self, table_name: str, record: dict) -> dict:
        data = self.storage.read()
        if table_name not in data["tables"]:
            raise ValueError(f"Table '{table_name}' does not exist. Create it first.")
        existing_records      = data["tables"][table_name]
        new_id                = len(existing_records) + 1
        record["_id"]         = new_id
        record["_created_at"] = datetime.now().isoformat()
        data["tables"][table_name].append(record)
        self.storage.save(data)
        print(f"[NeevDB] Inserted record with _id={new_id} into '{table_name}'.")
        return record

    def find_all(self, table_name: str) -> list:
        data = self.storage.read()
        if table_name not in data["tables"]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        records = data["tables"][table_name]
        print(f"[NeevDB] Found {len(records)} records in '{table_name}'.")
        return records

    def find(self, table_name: str, condition) -> list:
        all_records = self.find_all(table_name)
        results     = [record for record in all_records if condition(record)]
        print(f"[NeevDB] {len(results)} record(s) matched the condition.")
        return results

    def update(self, table_name: str, condition, updates: dict) -> int:
        data = self.storage.read()
        if table_name not in data["tables"]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        updated_count = 0
        for record in data["tables"][table_name]:
            if condition(record):
                record.update(updates)
                updated_count += 1
        self.storage.save(data)
        print(f"[NeevDB] Updated {updated_count} record(s) in '{table_name}'.")
        return updated_count

    def delete(self, table_name: str, condition) -> int:
        data = self.storage.read()
        if table_name not in data["tables"]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        original_count             = len(data["tables"][table_name])
        data["tables"][table_name] = [
            record for record in data["tables"][table_name]
            if not condition(record)
        ]
        deleted_count = original_count - len(data["tables"][table_name])
        self.storage.save(data)
        print(f"[NeevDB] Deleted {deleted_count} record(s) from '{table_name}'.")
        return deleted_count

    def count(self, table_name: str) -> int:
        records = self.find_all(table_name)
        return len(records)

    # ──────────────────────────────────────────────
    # Query Engine
    # ──────────────────────────────────────────────

    def query(self, query_string: str) -> list:
        """
        Execute a SQL-like query string against the database.

        Supported syntax:
            SELECT * FROM table_name
            SELECT col1, col2 FROM table_name
            SELECT * FROM table_name WHERE field operator value
            SELECT * FROM table_name ORDER BY field
            SELECT * FROM table_name ORDER BY field DESC
            SELECT * FROM table_name LIMIT 10
            SELECT * FROM table_name WHERE age > 18 ORDER BY name LIMIT 5

        Args:
            query_string: A SQL-like query string.

        Returns:
            A list of matching record dictionaries.
        """
        return self.query_engine.run(query_string, self.find_all)