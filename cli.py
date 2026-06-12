"""
NeevDB - Command Line Interface (CLI)
An interactive terminal shell for NeevDB.

Usage:
    python cli.py
    python cli.py mydata.json

Commands:
    SELECT * FROM table_name
    SELECT * FROM table_name WHERE field > value
    SELECT * FROM table_name ORDER BY field
    SELECT * FROM table_name LIMIT 5
    CREATE TABLE table_name
    DROP TABLE table_name
    SHOW TABLES
    INSERT INTO table_name key=value key2=value2
    DELETE FROM table_name WHERE field = value
    HELP
    EXIT
"""

import sys
import os

# Allow running cli.py from the root NeevDB folder
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from neevdb import NeevDB


# ──────────────────────────────────────────────
# Color Helpers (Windows + Mac + Linux support)
# ──────────────────────────────────────────────

class Color:
    """ANSI color codes for terminal output."""
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"

def green(text):  return f"{Color.GREEN}{text}{Color.RESET}"
def red(text):    return f"{Color.RED}{text}{Color.RESET}"
def yellow(text): return f"{Color.YELLOW}{text}{Color.RESET}"
def cyan(text):   return f"{Color.CYAN}{text}{Color.RESET}"
def bold(text):   return f"{Color.BOLD}{text}{Color.RESET}"
def dim(text):    return f"{Color.DIM}{text}{Color.RESET}"


# ──────────────────────────────────────────────
# Result Printer
# ──────────────────────────────────────────────

def print_table(records: list):
    """
    Print a list of records as a formatted table in the terminal.

    Args:
        records: List of record dictionaries to display.
    """
    if not records:
        print(yellow("  No records found."))
        return

    # Collect all column names (preserve order, _id first)
    all_keys = []
    for record in records:
        for key in record:
            if key not in all_keys:
                all_keys.append(key)

    # Move _id and _created_at to end for cleaner display
    priority = [k for k in all_keys if k not in ("_id", "_created_at")]
    meta     = [k for k in all_keys if k in ("_id", "_created_at")]
    columns  = priority + meta

    # Calculate column widths
    col_widths = {}
    for col in columns:
        max_val = max(
            len(str(col)),
            max((len(str(r.get(col, ""))) for r in records), default=0)
        )
        col_widths[col] = max_val + 2

    # Print header
    header = "  " + "  ".join(bold(col.ljust(col_widths[col])) for col in columns)
    separator = "  " + "  ".join("─" * col_widths[col] for col in columns)
    print(cyan(separator))
    print(header)
    print(cyan(separator))

    # Print rows
    for record in records:
        row = "  " + "  ".join(
            str(record.get(col, "")).ljust(col_widths[col])
            for col in columns
        )
        print(row)

    print(cyan(separator))
    print(dim(f"  {len(records)} row(s)"))


# ──────────────────────────────────────────────
# INSERT Parser
# ──────────────────────────────────────────────

def parse_insert(command: str, db: NeevDB):
    """
    Parse and execute an INSERT INTO command.

    Syntax: INSERT INTO table_name key=value key2="multi word value"

    Args:
        command: The full INSERT command string.
        db: The active NeevDB instance.
    """
    import re

    # Match: INSERT INTO table_name ...
    match = re.match(r"INSERT\s+INTO\s+(\w+)\s+(.+)", command, re.IGNORECASE)
    if not match:
        print(red("  Syntax error. Usage: INSERT INTO table_name key=value age=21"))
        return

    table_name  = match.group(1)
    fields_str  = match.group(2)

    # Parse key=value pairs (supports quoted strings)
    record = {}
    pairs  = re.findall(r'(\w+)=(".*?"|\'.*?\'|\S+)', fields_str)

    if not pairs:
        print(red("  No fields found. Usage: INSERT INTO users name=Alice age=25"))
        return

    for key, value in pairs:
        # Strip surrounding quotes
        value = value.strip('"').strip("'")
        # Auto-convert to int or float if possible
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        record[key] = value

    try:
        inserted = db.insert(table_name, record)
        print(green(f"  Inserted record with _id={inserted['_id']} into '{table_name}'."))
    except ValueError as e:
        print(red(f"  Error: {e}"))


# ──────────────────────────────────────────────
# DELETE Parser
# ──────────────────────────────────────────────

def parse_delete(command: str, db: NeevDB):
    """
    Parse and execute a DELETE FROM command.

    Syntax: DELETE FROM table_name WHERE field = value

    Args:
        command: The full DELETE command string.
        db: The active NeevDB instance.
    """
    import re

    match = re.match(r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*(==|!=|>=|<=|>|<|=)\s*(.+)", command, re.IGNORECASE)
    if not match:
        print(red("  Syntax error. Usage: DELETE FROM table_name WHERE field = value"))
        return

    table_name = match.group(1)
    field      = match.group(2)
    operator   = match.group(3)
    value      = match.group(4).strip().strip('"').strip("'")

    operators = {
        "=":  lambda a, b: str(a) == str(b),
        "==": lambda a, b: str(a) == str(b),
        "!=": lambda a, b: str(a) != str(b),
        ">":  lambda a, b: float(a) > float(b),
        "<":  lambda a, b: float(a) < float(b),
        ">=": lambda a, b: float(a) >= float(b),
        "<=": lambda a, b: float(a) <= float(b),
    }

    compare = operators.get(operator)

    def condition(record):
        if field not in record:
            return False
        try:
            return compare(record[field], value)
        except (ValueError, TypeError):
            return False

    try:
        deleted = db.delete(table_name, condition)
        print(green(f"  Deleted {deleted} record(s) from '{table_name}'."))
    except ValueError as e:
        print(red(f"  Error: {e}"))


# ──────────────────────────────────────────────
# Help Menu
# ──────────────────────────────────────────────

def print_help():
    """Display the help menu with all available commands."""
    print(f"""
{cyan("─" * 52)}
{bold("  NeevDB — Available Commands")}
{cyan("─" * 52)}

  {yellow("SELECT")}
    SELECT * FROM users
    SELECT * FROM users WHERE age > 18
    SELECT name, city FROM users
    SELECT * FROM users ORDER BY age DESC
    SELECT * FROM users LIMIT 5
    SELECT * FROM users WHERE age > 18 ORDER BY name LIMIT 3

  {yellow("INSERT")}
    INSERT INTO users name=Alice age=25 city=Mumbai

  {yellow("DELETE")}
    DELETE FROM users WHERE name = Alice
    DELETE FROM users WHERE age < 18

  {yellow("TABLES")}
    CREATE TABLE users
    DROP TABLE users
    SHOW TABLES

  {yellow("OTHER")}
    HELP       — show this menu
    CLEAR      — clear the screen
    EXIT       — quit NeevDB

{cyan("─" * 52)}
""")


# ──────────────────────────────────────────────
# Main CLI Loop
# ──────────────────────────────────────────────

def main():
    """Start the interactive NeevDB CLI shell."""

    # Enable ANSI colors on Windows
    if sys.platform == "win32":
        os.system("color")

    # Get database file from argument or use default
    db_file = sys.argv[1] if len(sys.argv) > 1 else "neevdb.json"

    print(cyan("=" * 52))
    print(bold(f"  NeevDB v1.0 — Interactive Shell"))
    print(dim(f"  Database: {db_file}"))
    print(cyan("=" * 52))
    print(dim("  Type HELP for commands, EXIT to quit.\n"))

    # Suppress internal NeevDB print logs in CLI mode
    db = NeevDB.__new__(NeevDB)
    from neevdb.storage import Storage
    from neevdb.query import QueryEngine
    db.storage      = Storage(db_file)
    db.query_engine = QueryEngine()

    while True:
        try:
            command = input(bold(cyan("NeevDB")) + " > ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{dim('  Goodbye!')}")
            break

        if not command:
            continue

        upper = command.upper()

        # ── EXIT ──
        if upper in ("EXIT", "QUIT", "BYE"):
            print(dim("  Goodbye! NeevDB closed."))
            break

        # ── HELP ──
        elif upper == "HELP":
            print_help()

        # ── CLEAR ──
        elif upper == "CLEAR":
            os.system("cls" if sys.platform == "win32" else "clear")

        # ── SHOW TABLES ──
        elif upper == "SHOW TABLES":
            data   = db.storage.read()
            tables = list(data["tables"].keys())
            if tables:
                print(green(f"  Tables: {', '.join(tables)}"))
            else:
                print(yellow("  No tables found. Use CREATE TABLE to make one."))

        # ── CREATE TABLE ──
        elif upper.startswith("CREATE TABLE"):
            parts = command.split()
            if len(parts) < 3:
                print(red("  Usage: CREATE TABLE table_name"))
            else:
                table_name = parts[2]
                data = db.storage.read()
                if table_name in data["tables"]:
                    print(yellow(f"  Table '{table_name}' already exists."))
                else:
                    data["tables"][table_name] = []
                    db.storage.save(data)
                    print(green(f"  Table '{table_name}' created."))

        # ── DROP TABLE ──
        elif upper.startswith("DROP TABLE"):
            parts = command.split()
            if len(parts) < 3:
                print(red("  Usage: DROP TABLE table_name"))
            else:
                table_name = parts[2]
                data = db.storage.read()
                if table_name not in data["tables"]:
                    print(red(f"  Table '{table_name}' not found."))
                else:
                    confirm = input(yellow(f"  Are you sure you want to drop '{table_name}'? (yes/no): ")).strip().lower()
                    if confirm == "yes":
                        del data["tables"][table_name]
                        db.storage.save(data)
                        print(green(f"  Table '{table_name}' dropped."))
                    else:
                        print(dim("  Cancelled."))

        # ── SELECT ──
        elif upper.startswith("SELECT"):
            try:
                results = db.query(command)
                print_table(results)
            except (SyntaxError, ValueError) as e:
                print(red(f"  Error: {e}"))

        # ── INSERT ──
        elif upper.startswith("INSERT"):
            parse_insert(command, db)

        # ── DELETE ──
        elif upper.startswith("DELETE"):
            parse_delete(command, db)

        # ── Unknown command ──
        else:
            print(red(f"  Unknown command: '{command}'"))
            print(dim("  Type HELP to see all available commands."))


if __name__ == "__main__":
    main()