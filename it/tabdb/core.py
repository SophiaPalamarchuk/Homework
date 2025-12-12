from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from types import SimpleNamespace

from .types import ValidationError, coerce_value, serialize_value, DateInvl

SUPPORTED_TYPES = {"integer", "real", "char", "string", "date", "dateinvl"}

@dataclass
class Column:
    name: str
    type: str  # one of SUPPORTED_TYPES

    def __post_init__(self):
        self.type = self.type.lower().strip()
        if self.type not in SUPPORTED_TYPES:
            raise ValidationError(f"Unsupported column type: {self.type}")
        if not self.name or not self.name.strip():
            raise ValidationError("Column name cannot be empty")
        object.__setattr__(self, "name", self.name.strip())

@dataclass
class Table:
    name: str
    columns: List[Column]
    rows: List[List[Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValidationError("Table name cannot be empty")
        self.name = self.name.strip()
        if not self.columns:
            raise ValidationError("Table must have at least one column")
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValidationError("Duplicate column names are not allowed")

    def validate_row(self, raw_values: List[Any]) -> List[Any]:
        if len(raw_values) != len(self.columns):
            raise ValidationError(f"Row must have {len(self.columns)} values")
        typed: List[Any] = []
        for col, raw in zip(self.columns, raw_values):
            typed.append(coerce_value(col.type, raw))
        return typed

    def insert_row(self, raw_values: List[Any]) -> int:
        row = self.validate_row(raw_values)
        self.rows.append(row)
        return len(self.rows) - 1

    def update_row(self, index: int, raw_values: List[Any]) -> None:
        if index < 0 or index >= len(self.rows):
            raise ValidationError("Row index out of range")
        self.rows[index] = self.validate_row(raw_values)

    def delete_row(self, index: int) -> None:
        if index < 0 or index >= len(self.rows):
            raise ValidationError("Row index out of range")
        del self.rows[index]

    def schema_signature(self) -> Tuple[Tuple[str, str], ...]:
        return tuple((c.name, c.type) for c in self.columns)

    def intersect(self, other: "Table", result_name: str) -> "Table":
        """
        Variant operation: intersection of tables.
        Requires identical schema (names + types in same order).
        Returns a new table with distinct common rows.
        """
        if self.schema_signature() != other.schema_signature():
            raise ValidationError("Intersection requires identical schemas (same columns and types in same order)")

        # Convert rows to hashable tuples (Date and DateInvl are hashable; DateInvl is frozen dataclass)
        a = set(tuple(r) for r in self.rows)
        b = set(tuple(r) for r in other.rows)
        inter = sorted(a.intersection(b), key=lambda x: str(x))
        return Table(name=result_name, columns=[Column(c.name, c.type) for c in self.columns], rows=[list(r) for r in inter])

@dataclass
class Database:
    name: str = "Untitled"
    tables: Dict[str, Table] = field(default_factory=dict)

    def create_table(self, name: str, columns: List[Tuple[str, str]]) -> Table:
        name = name.strip()
        if not name:
            raise ValidationError("Table name cannot be empty")
        if name in self.tables:
            raise ValidationError(f"Table '{name}' already exists")
        cols = [Column(n, t) for (n, t) in columns]
        t = Table(name=name, columns=cols)
        self.tables[name] = t
        return t

    def drop_table(self, name: str) -> None:
        if name not in self.tables:
            raise ValidationError(f"Table '{name}' not found")
        del self.tables[name]

    def rename_table(self, old: str, new: str) -> None:
        if old not in self.tables:
            raise ValidationError(f"Table '{old}' not found")
        new = new.strip()
        if not new:
            raise ValidationError("New name cannot be empty")
        if new in self.tables and new != old:
            raise ValidationError(f"Table '{new}' already exists")
        t = self.tables.pop(old)
        t.name = new
        self.tables[new] = t

    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise ValidationError(f"Table '{name}' not found")
        return self.tables[name]
