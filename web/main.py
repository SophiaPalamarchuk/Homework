from __future__ import annotations

import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, List

from tabdb.core import Database
from tabdb.types import ValidationError
from tabdb.storage_json import db_to_dict, db_from_dict, save_json_text

app = FastAPI(
    title="TabDB Web (Type 1)",
    description="REST API for partial tabular DBMS + simple Web UI.",
    version="1.0.0",
)

DB: Database = Database(name="Untitled")

class NewDbRequest(BaseModel):
    name: str = "Untitled"

class ColumnIn(BaseModel):
    name: str
    type: str

class CreateTableRequest(BaseModel):
    name: str
    columns: List[ColumnIn]

class RowIn(BaseModel):
    values: List[Any]

class IntersectRequest(BaseModel):
    a: str
    b: str
    result_name: str

def bad_request(e: Exception):
    raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/db/new")
def db_new(req: NewDbRequest):
    global DB
    DB = Database(name=req.name)
    return {"ok": True, "name": DB.name}

@app.get("/db")
def db_get():
    return db_to_dict(DB)

@app.post("/db/load-json")
async def db_load_json(file: UploadFile = File(...)):
    global DB
    try:
        raw = await file.read()
        payload = json.loads(raw.decode("utf-8"))
        DB = db_from_dict(payload)
        return {"ok": True, "name": DB.name, "tables": sorted(DB.tables.keys())}
    except Exception as e:
        bad_request(f"Failed to load JSON: {e}")

@app.get("/db/download-json")
def db_download_json():
    return JSONResponse(content=db_to_dict(DB))

@app.get("/tables")
def list_tables():
    return {"tables": sorted(DB.tables.keys())}

@app.post("/tables")
def create_table(req: CreateTableRequest):
    try:
        DB.create_table(req.name, [(c.name, c.type) for c in req.columns])
        return {"ok": True, "table": req.name}
    except ValidationError as e:
        bad_request(e)

@app.delete("/tables/{name}")
def delete_table(name: str):
    try:
        DB.drop_table(name)
        return {"ok": True}
    except ValidationError as e:
        bad_request(e)

@app.get("/tables/{name}")
def get_table(name: str):
    try:
        t = DB.get_table(name)
        return {
            "name": t.name,
            "columns": [{"name": c.name, "type": c.type} for c in t.columns],
            "rows": [[_display(v) for v in r] for r in t.rows],
        }
    except ValidationError as e:
        bad_request(e)

def _display(v: Any) -> Any:
    try:
        if hasattr(v, "start") and hasattr(v, "end") and hasattr(v.start, "isoformat"):
            return [v.start.isoformat(), v.end.isoformat()]
        if hasattr(v, "isoformat"):
            return v.isoformat()
    except Exception:
        pass
    return v

@app.post("/tables/{name}/rows")
def add_row(name: str, req: RowIn):
    try:
        t = DB.get_table(name)
        idx = t.insert_row(req.values)
        return {"ok": True, "index": idx}
    except ValidationError as e:
        bad_request(e)

@app.put("/tables/{name}/rows/{index}")
def update_row(name: str, index: int, req: RowIn):
    try:
        t = DB.get_table(name)
        t.update_row(index, req.values)
        return {"ok": True}
    except ValidationError as e:
        bad_request(e)

@app.delete("/tables/{name}/rows/{index}")
def delete_row(name: str, index: int):
    try:
        t = DB.get_table(name)
        t.delete_row(index)
        return {"ok": True}
    except ValidationError as e:
        bad_request(e)

@app.post("/tables/intersect")
def intersect(req: IntersectRequest):
    try:
        t1 = DB.get_table(req.a)
        t2 = DB.get_table(req.b)
        out = t1.intersect(t2, req.result_name)
        if out.name in DB.tables:
            raise ValidationError(f"Table '{out.name}' already exists")
        DB.tables[out.name] = out
        return {"ok": True, "table": out.name, "rows": len(out.rows)}
    except ValidationError as e:
        bad_request(e)

# Frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
