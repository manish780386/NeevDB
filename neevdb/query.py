"""
NeevDB - Query Engine
Parses and executes simple SQL-like query strings.

Supported syntax:
    SELECT * FROM table_name
    SELECT col1, col2 FROM table_name
    SELECT * FROM table_name WHERE field operator value
    SELECT * FROM table_name ORDER BY field
    SELECT * FROM table_name ORDER BY field DESC
    SELECT * FROM table_name LIMIT 10
    SELECT * FROM table_name WHERE age > 18 ORDER BY name LIMIT 5
"""

import re


class QueryParser:
    """Parses a raw SQL-like query string into structured components."""

    def parse(self, query: str) -> dict:
        """
        Parse a query string into a structured dictionary.

        Args:
            query: A SQL-like query string.

        Returns:
            A dictionary with keys: action, columns, table,
            where, order_by, order_dir, limit.

        Raises:
            SyntaxError: If the query format is not recognized.
        """
        query = query.strip()

        if not query.upper().startswith("SELECT"):
            raise SyntaxError("Only SELECT queries are supported right now.")

        parsed = {
            "action":    "SELECT",
            "columns":   "*",
            "table":     None,
            "where":     None,
            "order_by":  None,
            "order_dir": "ASC",
            "limit":     None,
        }

        # ── Extract LIMIT ──
        limit_match = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
        if limit_match:
            parsed["limit"] = int(limit_match.group(1))
            query = query[:limit_match.start()].strip()

        # ── Extract ORDER BY ──
        order_match = re.search(r"ORDER\s+BY\s+(\w+)(\s+DESC|\s+ASC)?", query, re.IGNORECASE)
        if order_match:
            parsed["order_by"] = order_match.group(1)
            direction = order_match.group(2)
            if direction and direction.strip().upper() == "DESC":
                parsed["order_dir"] = "DESC"
            query = query[:order_match.start()].strip()

        # ── Extract WHERE ──
        where_match = re.search(r"WHERE\s+(.+)", query, re.IGNORECASE)
        if where_match:
            parsed["where"] = where_match.group(1).strip()
            query = query[:where_match.start()].strip()

        # ── Extract FROM + table name ──
        from_match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
        if not from_match:
            raise SyntaxError("Query must include a FROM clause. Example: SELECT * FROM users")
        parsed["table"] = from_match.group(1)
        query = query[:from_match.start()].strip()

        # ── Extract columns ──
        columns_match = re.search(r"SELECT\s+(.+)", query, re.IGNORECASE)
        if columns_match:
            cols = columns_match.group(1).strip()
            if cols != "*":
                parsed["columns"] = [c.strip() for c in cols.split(",")]
            else:
                parsed["columns"] = "*"

        return parsed


class QueryExecutor:
    """Executes a parsed query against the database."""

    OPERATORS = {
        "=":  lambda a, b: str(a) == str(b),
        "==": lambda a, b: str(a) == str(b),
        "!=": lambda a, b: str(a) != str(b),
        ">":  lambda a, b: float(a) > float(b),
        "<":  lambda a, b: float(a) < float(b),
        ">=": lambda a, b: float(a) >= float(b),
        "<=": lambda a, b: float(a) <= float(b),
    }

    def execute(self, parsed: dict, records: list) -> list:
        """
        Execute a parsed query on a list of records.

        Args:
            parsed: The structured query dictionary from QueryParser.
            records: All records from the target table.

        Returns:
            A filtered, sorted, and limited list of result records.
        """
        results = list(records)

        # ── Apply WHERE filter ──
        if parsed["where"]:
            results = self._apply_where(results, parsed["where"])

        # ── Apply ORDER BY ──
        if parsed["order_by"]:
            results = self._apply_order(results, parsed["order_by"], parsed["order_dir"])

        # ── Apply LIMIT ──
        if parsed["limit"] is not None:
            results = results[:parsed["limit"]]

        # ── Apply column selection ──
        if parsed["columns"] != "*":
            results = self._apply_columns(results, parsed["columns"])

        return results

    def _apply_where(self, records: list, where_clause: str) -> list:
        """
        Filter records using a WHERE condition string.

        Args:
            records: List of record dictionaries.
            where_clause: A condition string like 'age > 18' or 'city = Mumbai'.

        Returns:
            Filtered list of records.

        Raises:
            SyntaxError: If the WHERE clause format is invalid.
        """
        # Match: field operator value (e.g. age > 18, name = Alice)
        match = re.match(r"(\w+)\s*(==|!=|>=|<=|>|<|=)\s*(.+)", where_clause)
        if not match:
            raise SyntaxError(f"Invalid WHERE clause: '{where_clause}'. Example: WHERE age > 18")

        field    = match.group(1)
        operator = match.group(2)
        value    = match.group(3).strip().strip('"').strip("'")

        compare = self.OPERATORS.get(operator)
        if not compare:
            raise SyntaxError(f"Unsupported operator: '{operator}'")

        filtered = []
        for record in records:
            if field not in record:
                continue
            try:
                if compare(record[field], value):
                    filtered.append(record)
            except (ValueError, TypeError):
                continue

        return filtered

    def _apply_order(self, records: list, field: str, direction: str) -> list:
        """
        Sort records by a given field.

        Args:
            records: List of record dictionaries.
            field: The field name to sort by.
            direction: 'ASC' for ascending, 'DESC' for descending.

        Returns:
            Sorted list of records.
        """
        reverse = direction.upper() == "DESC"
        try:
            return sorted(records, key=lambda r: r.get(field, ""), reverse=reverse)
        except TypeError:
            return records

    def _apply_columns(self, records: list, columns: list) -> list:
        """
        Keep only specified columns in each record.

        Args:
            records: List of record dictionaries.
            columns: List of column names to keep.

        Returns:
            Records with only the requested columns.
        """
        return [{col: record[col] for col in columns if col in record} for record in records]


class QueryEngine:
    """
    Main interface for the NeevDB query system.
    Combines the parser and executor into a single easy-to-use class.
    """

    def __init__(self):
        self.parser   = QueryParser()
        self.executor = QueryExecutor()

    def run(self, query: str, get_records_fn) -> list:
        """
        Parse and execute a query string.

        Args:
            query: A SQL-like query string.
            get_records_fn: A callable that takes a table name and returns its records.

        Returns:
            A list of result record dictionaries.

        Raises:
            SyntaxError: If the query is malformed.
            ValueError: If the table does not exist.
        """
        parsed  = self.parser.parse(query)
        records = get_records_fn(parsed["table"])
        results = self.executor.execute(parsed, records)

        print(f"[NeevDB] Query returned {len(results)} record(s).")
        return results