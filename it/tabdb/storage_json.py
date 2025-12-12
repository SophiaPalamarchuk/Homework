from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

from .core import Database, Table, Column
from .types import serialize_value, coerce_value, ValidationError, DateInvl, parse_date

def db_to_dict(db: Database) -> Dict[str, Any]:
    tables: List[Dict[str, Any]] = []
    for t in db.tables.values():
        tables.append({
            "name": t.name,
            "columns": [{"name": c.name, "type": c.type} for c in t.columns],
            "rows": [
                [serialize_value(col.type, val) for col, val in zip(t.columns, row)]
                for row in t.rows
            ]
        })
    return {"name": db.name, "tables": tables}

def db_from_dict(data: Dict[str, Any]) -> Database:
    db = Database(name=data.get("name", "Untitled"))
    for tdata in data.get("tables", []):
        cols = [(c["name"], c["type"]) for c in tdata.get("columns", [])]
        table = db.create_table(tdata["name"], cols)
        for r in tdata.get("rows", []):
            # coerce using schema
            typed = [coerce_value(col.type, rv) for col, rv in zip(table.columns, r)]
            table.rows.append(typed)
    return db

def save_json(db: Database, filepath: str) -> None:
    p = Path(filepath)
    payload = db_to_dict(db)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def load_json(filepath: str) -> Database:
    p = Path(filepath)
    data = json.loads(p.read_text(encoding="utf-8"))
    return db_from_dict(data)
