"""
NeevDB - REST API Server
A fully functional REST API built on top of NeevDB using FastAPI.

Run with:
    uvicorn api:app --reload

Base URL: http://localhost:8000
Docs UI:  http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any
from neevdb import NeevDB

# ── App setup ──────────────────────────────────────────────────────
app = FastAPI(
    title="NeevDB API",
    description="A lightweight REST API built on top of NeevDB — your own database engine.",
    version="1.0.0",
)

# Allow all origins (so browser playground can call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database connection ─────────────────────────────────────────────
db = NeevDB("neevdb.json")


# ── Request models ──────────────────────────────────────────────────
class RecordBody(BaseModel):
    """Body for inserting or updating a record."""
    data: dict[str, Any]


# ── Root ────────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    """Welcome endpoint — confirms the API is running."""
    return {
        "name":    "NeevDB API",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
    }


# ── Tables ──────────────────────────────────────────────────────────
@app.get("/tables", tags=["Tables"])
def list_tables():
    """
    List all tables in the database.

    Returns:
        A list of table names.

    Example:
        GET /tables
        → { "tables": ["users", "products"] }
    """
    data   = db.storage.read()
    tables = list(data["tables"].keys())
    return {"tables": tables, "count": len(tables)}


@app.post("/tables/{table_name}", tags=["Tables"])
def create_table(table_name: str):
    """
    Create a new table.

    Args:
        table_name: Name of the table to create.

    Example:
        POST /tables/users
        → { "message": "Table 'users' created." }
    """
    data = db.storage.read()
    if table_name in data["tables"]:
        raise HTTPException(status_code=409, detail=f"Table '{table_name}' already exists.")
    data["tables"][table_name] = []
    db.storage.save(data)
    return {"message": f"Table '{table_name}' created.", "table": table_name}


@app.delete("/tables/{table_name}", tags=["Tables"])
def drop_table(table_name: str):
    """
    Delete a table and all its records permanently.

    Args:
        table_name: Name of the table to delete.

    Example:
        DELETE /tables/users
        → { "message": "Table 'users' dropped." }
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
    del data["tables"][table_name]
    db.storage.save(data)
    return {"message": f"Table '{table_name}' dropped.", "table": table_name}


# ── Records ─────────────────────────────────────────────────────────
@app.get("/tables/{table_name}/records", tags=["Records"])
def get_records(
    table_name: str,
    where:  Optional[str] = Query(None, description="Filter: field=value or field>value"),
    order:  Optional[str] = Query(None, description="Field to sort by"),
    desc:   Optional[bool]= Query(False, description="Sort descending"),
    limit:  Optional[int] = Query(None, description="Max number of records to return"),
):
    """
    Get all records from a table, with optional filtering and sorting.

    Args:
        table_name : Table to read from.
        where      : Filter condition  e.g. age>18  or  city=Mumbai
        order      : Field to sort by  e.g. name
        desc       : If true, sort descending
        limit      : Max records to return

    Examples:
        GET /tables/users/records
        GET /tables/users/records?where=age>18
        GET /tables/users/records?where=city=Mumbai&order=name&limit=5
        GET /tables/users/records?order=age&desc=true&limit=3
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    records = list(data["tables"][table_name])

    # ── Apply WHERE filter ──
    if where:
        import re
        match = re.match(r"(\w+)\s*(==|!=|>=|<=|>|<|=)\s*(.+)", where)
        if not match:
            raise HTTPException(status_code=400, detail=f"Invalid where format: '{where}'. Use: field>value or field=value")

        field, operator, value = match.group(1), match.group(2), match.group(3).strip()

        operators = {
            "=":  lambda a, b: str(a) == str(b),
            "==": lambda a, b: str(a) == str(b),
            "!=": lambda a, b: str(a) != str(b),
            ">":  lambda a, b: float(a) > float(b),
            "<":  lambda a, b: float(a) < float(b),
            ">=": lambda a, b: float(a) >= float(b),
            "<=": lambda a, b: float(a) <= float(b),
        }

        cmp = operators.get(operator)
        filtered = []
        for record in records:
            if field not in record:
                continue
            try:
                if cmp(record[field], value):
                    filtered.append(record)
            except (ValueError, TypeError):
                continue
        records = filtered

    # ── Apply ORDER BY ──
    if order:
        reverse = desc or False
        try:
            records = sorted(records, key=lambda r: r.get(order, ""), reverse=reverse)
        except TypeError:
            pass

    # ── Apply LIMIT ──
    if limit is not None:
        records = records[:limit]

    return {
        "table":   table_name,
        "count":   len(records),
        "records": records,
    }


@app.get("/tables/{table_name}/records/{record_id}", tags=["Records"])
def get_record_by_id(table_name: str, record_id: int):
    """
    Get a single record by its _id.

    Args:
        table_name : Table to search in.
        record_id  : The _id of the record.

    Example:
        GET /tables/users/records/1
        → { "record": { "_id": 1, "name": "Alice", ... } }
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    for record in data["tables"][table_name]:
        if record.get("_id") == record_id:
            return {"table": table_name, "record": record}

    raise HTTPException(status_code=404, detail=f"Record with _id={record_id} not found in '{table_name}'.")


@app.post("/tables/{table_name}/records", tags=["Records"])
def insert_record(table_name: str, body: RecordBody):
    """
    Insert a new record into a table.

    Args:
        table_name : Table to insert into.
        body       : JSON body with a 'data' key containing the record fields.

    Example:
        POST /tables/users/records
        Body: { "data": { "name": "Alice", "age": 25, "city": "Mumbai" } }
        → { "record": { "name": "Alice", "age": 25, "_id": 1, ... } }
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    try:
        inserted = db.insert(table_name, body.data)
        return {"message": "Record inserted.", "table": table_name, "record": inserted}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/tables/{table_name}/records/{record_id}", tags=["Records"])
def update_record(table_name: str, record_id: int, body: RecordBody):
    """
    Update a record by its _id.

    Args:
        table_name : Table to update.
        record_id  : The _id of the record to update.
        body       : JSON body with a 'data' key containing updated fields.

    Example:
        PUT /tables/users/records/1
        Body: { "data": { "city": "Delhi" } }
        → { "message": "Record updated.", "updated": 1 }
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    updated_count = db.update(
        table_name,
        lambda r: r.get("_id") == record_id,
        body.data
    )

    if updated_count == 0:
        raise HTTPException(status_code=404, detail=f"Record with _id={record_id} not found.")

    return {"message": "Record updated.", "table": table_name, "updated": updated_count}


@app.delete("/tables/{table_name}/records/{record_id}", tags=["Records"])
def delete_record(table_name: str, record_id: int):
    """
    Delete a record by its _id.

    Args:
        table_name : Table to delete from.
        record_id  : The _id of the record to delete.

    Example:
        DELETE /tables/users/records/1
        → { "message": "Record deleted.", "deleted": 1 }
    """
    data = db.storage.read()
    if table_name not in data["tables"]:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    deleted_count = db.delete(
        table_name,
        lambda r: r.get("_id") == record_id
    )

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Record with _id={record_id} not found.")

    return {"message": "Record deleted.", "table": table_name, "deleted": deleted_count}


# ── Query endpoint ───────────────────────────────────────────────────
class QueryBody(BaseModel):
    """Body for running a raw SQL-like query."""
    query: str


@app.post("/query", tags=["Query"])
def run_query(body: QueryBody):
    """
    Run a SQL-like query string against the database.

    Supported syntax:
        SELECT * FROM users
        SELECT * FROM users WHERE age > 18
        SELECT name, city FROM users ORDER BY age DESC LIMIT 5

    Args:
        body: JSON body with a 'query' key.

    Example:
        POST /query
        Body: { "query": "SELECT * FROM users WHERE age > 18 ORDER BY name LIMIT 5" }
    """
    try:
        results = db.query(body.query)
        return {
            "query":   body.query,
            "count":   len(results),
            "records": results,
        }
    except (SyntaxError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Stats endpoint ───────────────────────────────────────────────────
@app.get("/stats", tags=["Info"])
def get_stats():
    """
    Get overall database statistics.

    Returns total tables, total records across all tables, and per-table counts.

    Example:
        GET /stats
        → { "total_tables": 2, "total_records": 15, "tables": { "users": 7, ... } }
    """
    data          = db.storage.read()
    table_counts  = {t: len(r) for t, r in data["tables"].items()}
    total_records = sum(table_counts.values())

    return {
        "total_tables":  len(table_counts),
        "total_records": total_records,
        "tables":        table_counts,
    }