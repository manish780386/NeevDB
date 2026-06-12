# NeevDB 🗄️

> A lightweight, file-based database engine built with pure Python — no dependencies, no setup, just run.

**NeevDB** ("neev" = foundation in Hindi) is a simple database engine written from scratch in Python.  
It supports tables, CRUD operations, SQL-like queries, and an interactive CLI shell.

---

## 📁 Folder Structure

```
NeevDB/
├── neevdb/
│   ├── __init__.py       # Package entry point
│   ├── core.py           # Main database engine (CRUD + Query)
│   ├── storage.py        # File read/write layer
│   └── query.py          # SQL-like query parser and executor
├── tests/
│   └── test_core.py      # Full test suite (12 tests)
├── cli.py                # Interactive terminal shell
└── README.md             # You are here
```

---

## ⚡ Quick Start

```python
from neevdb import NeevDB

# Connect to (or create) a database file
db = NeevDB("mydata.json")

# Create a table
db.create_table("users")

# Insert records
db.insert("users", {"name": "Alice", "age": 25, "city": "Mumbai"})
db.insert("users", {"name": "Bob",   "age": 17, "city": "Delhi"})

# Find all records
all_users = db.find_all("users")

# Find with a condition
adults = db.find("users", lambda row: row["age"] > 18)

# Update records
db.update("users", lambda row: row["name"] == "Bob", {"age": 20})

# Delete records
db.delete("users", lambda row: row["name"] == "Alice")

# Count records
total = db.count("users")
```

---

## 🔍 Query Engine

NeevDB supports SQL-like query strings:

```python
# Select all records
db.query("SELECT * FROM users")

# Filter with WHERE
db.query("SELECT * FROM users WHERE age > 18")

# Select specific columns
db.query("SELECT name, city FROM users")

# Sort with ORDER BY
db.query("SELECT * FROM users ORDER BY age")
db.query("SELECT * FROM users ORDER BY age DESC")

# Limit results
db.query("SELECT * FROM users LIMIT 5")

# Combine everything
db.query("SELECT name, city FROM users WHERE age > 18 ORDER BY name LIMIT 3")
```

### Supported WHERE operators:

| Operator | Meaning           |
|----------|-------------------|
| `=`      | Equal to          |
| `!=`     | Not equal to      |
| `>`      | Greater than      |
| `<`      | Less than         |
| `>=`     | Greater or equal  |
| `<=`     | Less or equal     |

---

## 💻 CLI Shell

Launch the interactive terminal shell:

```bash
python cli.py
```

Or connect to a specific database file:

```bash
python cli.py mydata.json
```

### CLI Commands:

```
NeevDB > SHOW TABLES
NeevDB > CREATE TABLE users
NeevDB > INSERT INTO users name=Alice age=25 city=Mumbai
NeevDB > SELECT * FROM users
NeevDB > SELECT * FROM users WHERE age > 18
NeevDB > SELECT * FROM users ORDER BY age DESC LIMIT 3
NeevDB > DELETE FROM users WHERE name = Alice
NeevDB > DROP TABLE users
NeevDB > HELP
NeevDB > EXIT
```

### Example CLI session:

```
══════════════════════════════════════════════════════
  NeevDB v1.0 — Interactive Shell
  Database: neevdb.json
══════════════════════════════════════════════════════
  Type HELP for commands, EXIT to quit.

NeevDB > CREATE TABLE users
  Table 'users' created.

NeevDB > INSERT INTO users name=Manish age=21 city=Indore
  Inserted record with _id=1 into 'users'.

NeevDB > SELECT * FROM users
  ────────────────────────────────
  name      age   city
  ────────────────────────────────
  Manish    21    Indore
  ────────────────────────────────
  1 row(s)

NeevDB > EXIT
  Goodbye! NeevDB closed.
```

---

## 🧪 Running Tests

```bash
python tests/test_core.py
```

Expected output:
```
══════════════════════════════════════════
  NeevDB - Full Test Suite
══════════════════════════════════════════
  All 12 tests PASSED! NeevDB Phase 2 complete! 🚀
══════════════════════════════════════════
```

---

## 🛠️ How It Works

```
Your Code / CLI
      │
      ▼
  NeevDB Core         ← CRUD operations, table management
      │
      ├──► Query Engine   ← Parses SQL-like strings, filters, sorts, limits
      │
      └──► Storage        ← Reads and writes JSON file to disk
```

- **Storage layer** — All data is saved in a human-readable `.json` file
- **Core engine** — Manages tables and records in memory, syncs to disk on every change
- **Query engine** — Parses query strings using `re` (regex), executes filters/sort/limit
- **CLI shell** — A `while True` input loop that parses commands and calls the engine

---

## 📦 No Dependencies

NeevDB uses only Python built-in modules:

| Module     | Used for                        |
|------------|---------------------------------|
| `json`     | Saving and loading data         |
| `os`       | File path and existence checks  |
| `re`       | Query string parsing            |
| `datetime` | Auto-generating timestamps      |
| `sys`      | CLI argument handling           |

No `pip install` required. Works on Python 3.7+.

---

## 🚀 Built By

**Manish** — built NeevDB from scratch as a learning project.  
"Neev" means foundation in Hindi — this is the foundation of something bigger.

---

## 📌 Roadmap

- [x] Phase 1 — JSON storage, Tables, CRUD
- [x] Phase 2 — Query Engine (SELECT / WHERE / ORDER BY / LIMIT)
- [x] Phase 3 — Interactive CLI Shell
- [ ] Phase 4 — `pip install neevdb` (publish to PyPI)
- [ ] Phase 5 — Indexes for faster queries
- [ ] Phase 6 — Multi-table JOIN support