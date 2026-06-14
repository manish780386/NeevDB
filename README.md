# NeevDB 🗄️

> A lightweight, file-based database engine built with pure Python — zero dependencies, zero setup.

**NeevDB** ("neev" = foundation in Hindi) is a database engine written from scratch in Python.
It supports tables, CRUD operations, SQL-like queries, an interactive CLI shell, and a full REST API server.

---

## 📦 Install

```bash
# Core — zero dependencies
pip install neevdb

# With REST API server support
pip install neevdb[server]
```

---

## 📁 Project Structure

```
NeevDB/
├── neevdb/
│   ├── __init__.py       # Package entry point
│   ├── core.py           # Main database engine (CRUD + Query)
│   ├── storage.py        # File read/write layer
│   ├── query.py          # SQL-like query parser and executor
│   └── server.py         # Optional REST API server (FastAPI)
├── tests/
│   ├── test_core.py      # Core test suite (12 tests)
│   └── test_v2.py        # Full test suite (50+ tests)
├── api.py                # FastAPI REST API server
├── cli.py                # Interactive terminal shell
├── dashboard.html        # Browser dashboard UI
├── start.py              # One-command server launcher
├── pyproject.toml        # Package config
└── README.md
```

---

## ⚡ Quick Start

```python
from neevdb import NeevDB

db = NeevDB("mydata.json")

db.create_table("users")
db.insert("users", {"name": "Alice", "age": 25, "city": "Mumbai"})
db.insert("users", {"name": "Bob",   "age": 17, "city": "Delhi"})

# Find all
all_users = db.find_all("users")

# Find with condition
adults = db.find("users", lambda row: row["age"] > 18)

# Update
db.update("users", lambda row: row["name"] == "Bob", {"age": 20})

# Delete
db.delete("users", lambda row: row["name"] == "Alice")

# Count
total = db.count("users")
```

---

## 🔍 Query Engine

```python
db.query("SELECT * FROM users")
db.query("SELECT * FROM users WHERE age > 18")
db.query("SELECT name, city FROM users")
db.query("SELECT * FROM users ORDER BY age")
db.query("SELECT * FROM users ORDER BY age DESC")
db.query("SELECT * FROM users LIMIT 5")
db.query("SELECT name, city FROM users WHERE age > 18 ORDER BY name LIMIT 3")
```

### Supported WHERE operators

| Operator | Meaning          | Example               |
|----------|------------------|-----------------------|
| `=`      | Equal to         | WHERE city = Mumbai   |
| `!=`     | Not equal to     | WHERE status != draft |
| `>`      | Greater than     | WHERE age > 18        |
| `<`      | Less than        | WHERE price < 500     |
| `>=`     | Greater or equal | WHERE score >= 90     |
| `<=`     | Less or equal    | WHERE stock <= 10     |

---

## 🌐 REST API Server

Start the server with one command:

```bash
python start.py
```

Or with a custom database file:

```bash
python start.py mydata.json
```

Browser opens automatically at `http://localhost:8000` with the dashboard.

### From Python:

```python
from neevdb.server import start
start(db_path="mydata.json", host="0.0.0.0", port=8000)
```

### API Endpoints

| Method   | Endpoint                           | Description              |
|----------|------------------------------------|--------------------------|
| GET      | `/api`                             | Health check             |
| GET      | `/api/stats`                       | Database statistics      |
| GET      | `/api/tables`                      | List all tables          |
| POST     | `/api/tables/{name}`               | Create a table           |
| DELETE   | `/api/tables/{name}`               | Drop a table             |
| GET      | `/api/tables/{name}/records`       | Get records (+ filters)  |
| GET      | `/api/tables/{name}/records/{id}`  | Get record by ID         |
| POST     | `/api/tables/{name}/records`       | Insert a record          |
| PUT      | `/api/tables/{name}/records/{id}`  | Update a record          |
| DELETE   | `/api/tables/{name}/records/{id}`  | Delete a record          |
| POST     | `/api/query`                       | Run SQL-like query       |

### Query parameters for GET /records

```
?where=age>18          → Filter records
?order=name            → Sort by field
?desc=true             → Sort descending
?limit=5               → Max records
```

### Use from any frontend

```javascript
// Fetch users older than 18, sorted by name
const res  = await fetch('http://localhost:8000/api/tables/users/records?where=age>18&order=name')
const data = await res.json()
console.log(data.records)

// Insert a record
await fetch('http://localhost:8000/api/tables/users/records', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data: { name: 'Alice', age: 25 } })
})

// Run a query
const res = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'SELECT * FROM users WHERE age > 18 ORDER BY name LIMIT 5' })
})
```

---

## 💻 CLI Shell

```bash
python cli.py
python cli.py mydata.json
```

```
NeevDB > SHOW TABLES
NeevDB > CREATE TABLE users
NeevDB > INSERT INTO users name=Alice age=25 city=Mumbai
NeevDB > SELECT * FROM users WHERE age > 18
NeevDB > SELECT * FROM users ORDER BY age DESC LIMIT 5
NeevDB > DELETE FROM users WHERE name = Alice
NeevDB > DROP TABLE users
NeevDB > HELP
NeevDB > EXIT
```

---

## 🧪 Running Tests

```bash
# Core tests (12 tests)
python tests/test_core.py

# Full test suite (50+ tests)
python tests/test_v2.py
```

---

## 🛠️ How It Works

```
Your Code / CLI / Browser
         │
         ▼
    NeevDB Core       ← CRUD operations, table management
         │
         ├──► Query Engine   ← Parses SQL-like strings
         │
         ├──► Storage        ← Reads/writes JSON file to disk
         │
         └──► REST API       ← FastAPI server (optional)
                  │
                  └──► Dashboard HTML  ← Browser UI
```

---

## 📦 Zero Dependencies (Core)

| Module     | Used for                    |
|------------|-----------------------------|
| `json`     | Saving and loading data     |
| `os`       | File path checks            |
| `re`       | Query string parsing        |
| `datetime` | Auto-generating timestamps  |
| `sys`      | CLI argument handling       |

Optional server dependencies: `fastapi`, `uvicorn`

---

## 🚀 Built By

**Manish Dange** — built NeevDB from scratch as a learning project.
"Neev" means foundation in Hindi — this is the foundation of something bigger.

---

## 📌 Changelog

### v3.0.1
- Fixed dashboard loading from any folder
- API endpoints unified under `/api/` prefix
- `start.py` always runs from correct directory


### v3.0.0
- Fixed dashboard loading from any folder
- Improved error messages

### v2.0.0
- Optional REST API server (`pip install neevdb[server]`)
- `from neevdb.server import start` — one line server start
- Dashboard HTML UI
- Full test suite (50+ tests)

### v1.0.0
- JSON file storage
- Tables, CRUD operations
- SQL-like query engine (SELECT/WHERE/ORDER BY/LIMIT)
- Interactive CLI shell
- 12 passing tests

---

## 📌 Roadmap

- [x] Phase 1 — JSON storage, Tables, CRUD
- [x] Phase 2 — Query Engine (SELECT/WHERE/ORDER BY/LIMIT)
- [x] Phase 3 — Interactive CLI Shell
- [x] Phase 4 — PyPI publish (`pip install neevdb`)
- [x] Phase 5 — REST API server + Browser Dashboard
- [ ] Phase 6 — Indexes for faster queries
- [ ] Phase 7 — Multi-table JOIN support
- [ ] Phase 8 — Deploy to cloud (Railway/Render)