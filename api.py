"""
NeevDB - REST API Server v3.0.1
Run via: python start.py
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Any
import re, os
from neevdb import NeevDB

# ── Database ──────────────────────────────────────────────────────
DB_PATH = os.environ.get("NEEVDB_PATH", "neevdb.json")
db      = NeevDB(DB_PATH)

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="NeevDB API",
    description="A lightweight REST API built on top of NeevDB — your own database engine.",
    version="3.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Dashboard ─────────────────────────────────────────────────────
def find_dashboard() -> str | None:
    """Find dashboard.html in multiple possible locations."""
    search_paths = [
        os.path.join(os.getcwd(), "dashboard.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard.html"),
    ]
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

@app.get("/", include_in_schema=False)
def serve_dashboard():
    path = find_dashboard()
    if path:
        return FileResponse(path)
    return JSONResponse({
        "name":    "NeevDB API",
        "version": "3.0.1",
        "status":  "running",
        "docs":    "/docs",
        "note":    "Place dashboard.html next to api.py to enable the dashboard UI.",
    })

# ── Models ────────────────────────────────────────────────────────
class RecordBody(BaseModel):
    data: dict[str, Any]

class QueryBody(BaseModel):
    query: str

# ── Helpers ───────────────────────────────────────────────────────
OPERATORS = {
    "=":  lambda a, b: str(a) == str(b),
    "==": lambda a, b: str(a) == str(b),
    "!=": lambda a, b: str(a) != str(b),
    ">":  lambda a, b: float(a) > float(b),
    "<":  lambda a, b: float(a) < float(b),
    ">=": lambda a, b: float(a) >= float(b),
    "<=": lambda a, b: float(a) <= float(b),
}

def apply_where(records: list, where: str) -> list:
    match = re.match(r"(\w+)\s*(==|!=|>=|<=|>|<|=)\s*(.+)", where)
    if not match:
        raise HTTPException(400, f"Invalid where: '{where}'. Example: age>18 or city=Mumbai")
    field, op, val = match.group(1), match.group(2), match.group(3).strip()
    cmp = OPERATORS.get(op)
    result = []
    for record in records:
        if field not in record:
            continue
        try:
            if cmp(record[field], val):
                result.append(record)
        except (ValueError, TypeError):
            continue
    return result

# ── Info ──────────────────────────────────────────────────────────
@app.get("/api", tags=["Info"])
def root():
    """API health check."""
    return {
        "name":    "NeevDB API",
        "version": "3.0.1",
        "status":  "running",
        "db":      DB_PATH,
        "docs":    "/docs",
    }

@app.get("/api/stats", tags=["Info"])
def stats():
    """Get database statistics — total tables, total records, per-table counts."""
    data   = db.storage.read()
    counts = {t: len(r) for t, r in data["tables"].items()}
    return {
        "total_tables":  len(counts),
        "total_records": sum(counts.values()),
        "tables":        counts,
        "db_path":       DB_PATH,
    }

# ── Tables ────────────────────────────────────────────────────────
@app.get("/api/tables", tags=["Tables"])
def list_tables():
    """List all tables in the database."""
    data = db.storage.read()
    return {"tables": list(data["tables"].keys())}

@app.post("/api/tables/{name}", tags=["Tables"])
def create_table(name: str):
    """Create a new table. Returns 409 if already exists."""
    data = db.storage.read()
    if name in data["tables"]:
        raise HTTPException(409, f"Table '{name}' already exists.")
    data["tables"][name] = []
    db.storage.save(data)
    return {"message": f"Table '{name}' created.", "table": name}

@app.delete("/api/tables/{name}", tags=["Tables"])
def drop_table(name: str):
    """Delete a table and all its records permanently."""
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    del data["tables"][name]
    db.storage.save(data)
    return {"message": f"Table '{name}' dropped.", "table": name}

# ── Records ───────────────────────────────────────────────────────
@app.get("/api/tables/{name}/records", tags=["Records"])
def get_records(
    name:  str,
    where: Optional[str]  = Query(None, description="Filter: field=value or field>value"),
    order: Optional[str]  = Query(None, description="Field to sort by"),
    desc:  Optional[bool] = Query(False, description="Sort descending"),
    limit: Optional[int]  = Query(None, description="Max records to return"),
):
    """
    Get records from a table with optional filtering, sorting, and limiting.

    Examples:
        GET /api/tables/users/records
        GET /api/tables/users/records?where=age>18
        GET /api/tables/users/records?where=city=Mumbai&order=name&limit=5
        GET /api/tables/users/records?order=age&desc=true
    """
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    records = list(data["tables"][name])
    if where:
        records = apply_where(records, where)
    if order:
        try:
            records = sorted(records, key=lambda r: r.get(order, ""), reverse=bool(desc))
        except TypeError:
            pass
    if limit is not None:
        records = records[:limit]
    return {"table": name, "count": len(records), "records": records}

@app.get("/api/tables/{name}/records/{rid}", tags=["Records"])
def get_record(name: str, rid: int):
    """Get a single record by its _id."""
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    for record in data["tables"][name]:
        if record.get("_id") == rid:
            return {"table": name, "record": record}
    raise HTTPException(404, f"Record _id={rid} not found in '{name}'.")

@app.post("/api/tables/{name}/records", tags=["Records"])
def insert_record(name: str, body: RecordBody):
    """Insert a new record. Auto-generates _id and _created_at."""
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    inserted = db.insert(name, body.data)
    return {"message": "Record inserted.", "table": name, "record": inserted}

@app.put("/api/tables/{name}/records/{rid}", tags=["Records"])
def update_record(name: str, rid: int, body: RecordBody):
    """Update fields of a record by _id. Only include fields to change."""
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    count = db.update(name, lambda r: r.get("_id") == rid, body.data)
    if count == 0:
        raise HTTPException(404, f"Record _id={rid} not found.")
    return {"message": "Record updated.", "table": name, "updated": count}

@app.delete("/api/tables/{name}/records/{rid}", tags=["Records"])
def delete_record(name: str, rid: int):
    """Delete a record by its _id."""
    data = db.storage.read()
    if name not in data["tables"]:
        raise HTTPException(404, f"Table '{name}' not found.")
    count = db.delete(name, lambda r: r.get("_id") == rid)
    if count == 0:
        raise HTTPException(404, f"Record _id={rid} not found.")
    return {"message": "Record deleted.", "table": name, "deleted": count}

# ── Query ─────────────────────────────────────────────────────────
@app.post("/api/query", tags=["Query"])
def run_query(body: QueryBody):
    """
    Run a SQL-like query string.

    Supported:
        SELECT * FROM users
        SELECT * FROM users WHERE age > 18
        SELECT name, city FROM users ORDER BY age DESC LIMIT 5
    """
    try:
        results = db.query(body.query)
        return {
            "query":   body.query,
            "count":   len(results),
            "records": results,
        }
    except (SyntaxError, ValueError) as e:
        raise HTTPException(400, str(e))