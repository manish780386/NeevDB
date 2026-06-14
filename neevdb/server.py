"""
NeevDB - Optional REST API Server (v3.0.1)

This module is optional. It requires FastAPI and uvicorn to be installed.

Install with:
    pip install neevdb[server]

Usage:
    from neevdb.server import start
    start()

    # Or with custom options:
    start(db_path="mydata.json", host="0.0.0.0", port=8000)
"""


def start(db_path: str = "neevdb.json", host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """
    Start the NeevDB REST API server.

    Requires fastapi and uvicorn to be installed.
    Install them with: pip install neevdb[server]

    Args:
        db_path : Path to the NeevDB JSON database file.
        host    : Host to bind the server to. Use '0.0.0.0' for network access.
        port    : Port number to run the server on.
        reload  : Enable auto-reload on file changes (development only).

    Example:
        from neevdb.server import start
        start(db_path="mydata.json", host="0.0.0.0", port=8000)
    """
    try:
        import fastapi
        import uvicorn
    except ImportError:
        raise ImportError(
            "\n\nNeevDB server requires FastAPI and uvicorn.\n"
            "Install them with:\n\n"
            "    pip install neevdb[server]\n"
        )

    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional, Any
    import re
    from neevdb import NeevDB

    # ── Database ──────────────────────────────────────────────────────
    db = NeevDB(db_path)

    # ── App ───────────────────────────────────────────────────────────
    app = FastAPI(
        title="NeevDB API",
        description="REST API powered by NeevDB — your own database engine.",
        version="3.0.1",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
            raise HTTPException(status_code=400, detail=f"Invalid where: '{where}'. Use: field>value")
        field, operator, value = match.group(1), match.group(2), match.group(3).strip()
        cmp = OPERATORS.get(operator)
        result = []
        for record in records:
            if field not in record:
                continue
            try:
                if cmp(record[field], value):
                    result.append(record)
            except (ValueError, TypeError):
                continue
        return result

    # ── Routes ────────────────────────────────────────────────────────

    @app.get("/", tags=["Info"])
    def root():
        return {"name": "NeevDB API", "version": "3.0.1", "status": "running", "docs": "/docs"}

    @app.get("/stats", tags=["Info"])
    def stats():
        data         = db.storage.read()
        table_counts = {t: len(r) for t, r in data["tables"].items()}
        return {
            "total_tables":  len(table_counts),
            "total_records": sum(table_counts.values()),
            "tables":        table_counts,
        }

    @app.get("/tables", tags=["Tables"])
    def list_tables():
        data = db.storage.read()
        return {"tables": list(data["tables"].keys())}

    @app.post("/tables/{table_name}", tags=["Tables"])
    def create_table(table_name: str):
        data = db.storage.read()
        if table_name in data["tables"]:
            raise HTTPException(status_code=409, detail=f"Table '{table_name}' already exists.")
        data["tables"][table_name] = []
        db.storage.save(data)
        return {"message": f"Table '{table_name}' created.", "table": table_name}

    @app.delete("/tables/{table_name}", tags=["Tables"])
    def drop_table(table_name: str):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        del data["tables"][table_name]
        db.storage.save(data)
        return {"message": f"Table '{table_name}' dropped."}

    @app.get("/tables/{table_name}/records", tags=["Records"])
    def get_records(
        table_name: str,
        where:  Optional[str]  = None,
        order:  Optional[str]  = None,
        desc:   Optional[bool] = False,
        limit:  Optional[int]  = None,
    ):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        records = list(data["tables"][table_name])
        if where:
            records = apply_where(records, where)
        if order:
            try:
                records = sorted(records, key=lambda r: r.get(order, ""), reverse=bool(desc))
            except TypeError:
                pass
        if limit is not None:
            records = records[:limit]
        return {"table": table_name, "count": len(records), "records": records}

    @app.get("/tables/{table_name}/records/{record_id}", tags=["Records"])
    def get_record(table_name: str, record_id: int):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        for record in data["tables"][table_name]:
            if record.get("_id") == record_id:
                return {"table": table_name, "record": record}
        raise HTTPException(status_code=404, detail=f"Record _id={record_id} not found.")

    @app.post("/tables/{table_name}/records", tags=["Records"])
    def insert_record(table_name: str, body: RecordBody):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        inserted = db.insert(table_name, body.data)
        return {"message": "Record inserted.", "table": table_name, "record": inserted}

    @app.put("/tables/{table_name}/records/{record_id}", tags=["Records"])
    def update_record(table_name: str, record_id: int, body: RecordBody):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        count = db.update(table_name, lambda r: r.get("_id") == record_id, body.data)
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Record _id={record_id} not found.")
        return {"message": "Record updated.", "updated": count}

    @app.delete("/tables/{table_name}/records/{record_id}", tags=["Records"])
    def delete_record(table_name: str, record_id: int):
        data = db.storage.read()
        if table_name not in data["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        count = db.delete(table_name, lambda r: r.get("_id") == record_id)
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Record _id={record_id} not found.")
        return {"message": "Record deleted.", "deleted": count}

    @app.post("/query", tags=["Query"])
    def run_query(body: QueryBody):
        try:
            results = db.query(body.query)
            return {"query": body.query, "count": len(results), "records": results}
        except (SyntaxError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── Start server ──────────────────────────────────────────────────
    print(f"\n[NeevDB] Server starting at http://{host}:{port}")
    print(f"[NeevDB] API docs at http://{host}:{port}/docs")
    print(f"[NeevDB] Database: {db_path}\n")

    uvicorn.run(app, host=host, port=port, reload=reload)