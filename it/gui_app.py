from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Any, List, Optional, Tuple

from tabdb.core import Database, Table
from tabdb.types import ValidationError, DateInvl
from tabdb.storage_json import save_json, load_json

DEFAULT_TYPES = ["integer", "real", "char", "string", "date", "dateInvl"]

class TableEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TabDB Desktop Client (Type 1)")
        self.geometry("1000x600")
        self.minsize(900, 520)

        self.db = Database(name="Untitled")
        self.db_path: Optional[str] = None
        self.current_table: Optional[str] = None

        self._build_menu()
        self._build_layout()
        self._refresh_tables_list()

    # ---------------- UI BUILD ----------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New Database", command=self.new_db)
        filem.add_command(label="Open JSON...", command=self.open_db)
        filem.add_command(label="Save", command=self.save_db)
        filem.add_command(label="Save As...", command=self.save_db_as)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filem)

        tablem = tk.Menu(menubar, tearoff=0)
        tablem.add_command(label="Create Table...", command=self.create_table_dialog)
        tablem.add_command(label="Delete Table", command=self.delete_table)
        tablem.add_separator()
        tablem.add_command(label="Intersect Tables...", command=self.intersect_tables_dialog)
        menubar.add_cascade(label="Table", menu=tablem)

        rowm = tk.Menu(menubar, tearoff=0)
        rowm.add_command(label="Add Row...", command=self.add_row_dialog)
        rowm.add_command(label="Edit Selected Row...", command=self.edit_selected_row_dialog)
        rowm.add_command(label="Delete Selected Row", command=self.delete_selected_row)
        menubar.add_cascade(label="Row", menu=rowm)

        self.config(menu=menubar)

    def _build_layout(self):
        outer = ttk.Frame(self, padding=8)
        outer.pack(fill="both", expand=True)

        # Left panel - tables
        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(left, text="Tables").pack(anchor="w")
        self.tables_list = tk.Listbox(left, width=28, height=24)
        self.tables_list.pack(fill="y", expand=True)
        self.tables_list.bind("<<ListboxSelect>>", lambda e: self.on_table_select())

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(btns, text="Create", command=self.create_table_dialog).pack(side="left", fill="x", expand=True)
        ttk.Button(btns, text="Delete", command=self.delete_table).pack(side="left", fill="x", expand=True, padx=(6,0))

        # Right panel - rows
        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True)

        topbar = ttk.Frame(right)
        topbar.pack(fill="x")
        self.table_label = ttk.Label(topbar, text="No table selected")
        self.table_label.pack(side="left")

        rowbtns = ttk.Frame(topbar)
        rowbtns.pack(side="right")
        ttk.Button(rowbtns, text="Add Row", command=self.add_row_dialog).pack(side="left")
        ttk.Button(rowbtns, text="Edit", command=self.edit_selected_row_dialog).pack(side="left", padx=(6,0))
        ttk.Button(rowbtns, text="Delete", command=self.delete_selected_row).pack(side="left", padx=(6,0))

        self.tree = ttk.Treeview(right, columns=(), show="headings", selectmode="browse")
        self.tree.pack(fill="both", expand=True, pady=(8,0))

        # status bar
        self.status = ttk.Label(self, text="Ready", anchor="w")
        self.status.pack(fill="x")

    # ---------------- Helpers ----------------

    def set_status(self, msg: str):
        self.status.config(text=msg)

    def get_selected_table(self) -> Optional[str]:
        sel = self.tables_list.curselection()
        if not sel:
            return None
        return self.tables_list.get(sel[0])

    def get_current_table_obj(self) -> Optional[Table]:
        name = self.current_table
        if not name:
            return None
        try:
            return self.db.get_table(name)
        except ValidationError:
            return None

    def _refresh_tables_list(self):
        self.tables_list.delete(0, tk.END)
        for name in sorted(self.db.tables.keys()):
            self.tables_list.insert(tk.END, name)

    def _load_table_into_grid(self, table: Table):
        self.tree.delete(*self.tree.get_children())
        cols = [c.name for c in table.columns]
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, stretch=True)

        for idx, row in enumerate(table.rows):
            self.tree.insert("", tk.END, iid=str(idx), values=[self._display_value(v) for v in row])

        self.table_label.config(text=f"Table: {table.name} (rows: {len(table.rows)})")

    def _display_value(self, v: Any) -> str:
        if isinstance(v, DateInvl):
            return f"{v.start.isoformat()}..{v.end.isoformat()}"
        try:
            # date has isoformat
            if hasattr(v, "isoformat"):
                return v.isoformat()
        except Exception:
            pass
        return str(v)

    # ---------------- Menu actions ----------------

    def new_db(self):
        if not messagebox.askyesno("Confirm", "Create new database? Unsaved changes will be lost."):
            return
        self.db = Database(name="Untitled")
        self.db_path = None
        self.current_table = None
        self._refresh_tables_list()
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()
        self.table_label.config(text="No table selected")
        self.set_status("New database created")

    def open_db(self):
        path = filedialog.askopenfilename(
            title="Open database JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.db = load_json(path)
            self.db_path = path
            self.current_table = None
            self._refresh_tables_list()
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = ()
            self.table_label.config(text="No table selected")
            self.set_status(f"Loaded: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON:\n{e}")

    def save_db(self):
        if not self.db_path:
            return self.save_db_as()
        try:
            save_json(self.db, self.db_path)
            self.set_status(f"Saved: {self.db_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")

    def save_db_as(self):
        path = filedialog.asksaveasfilename(
            title="Save database as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        self.db_path = path
        self.save_db()

    # ---------------- Table operations ----------------

    def on_table_select(self):
        name = self.get_selected_table()
        if not name:
            return
        self.current_table = name
        table = self.db.get_table(name)
        self._load_table_into_grid(table)
        self.set_status(f"Selected table: {name}")

    def create_table_dialog(self):
        dlg = CreateTableDialog(self, DEFAULT_TYPES)
        self.wait_window(dlg)
        if not dlg.result:
            return
        table_name, columns = dlg.result
        try:
            self.db.create_table(table_name, columns)
            self._refresh_tables_list()
            self.set_status(f"Created table: {table_name}")
        except ValidationError as e:
            messagebox.showerror("Validation error", str(e))

    def delete_table(self):
        name = self.get_selected_table()
        if not name:
            messagebox.showinfo("Info", "Select a table first.")
            return
        if not messagebox.askyesno("Confirm", f"Delete table '{name}'?"):
            return
        try:
            self.db.drop_table(name)
            self._refresh_tables_list()
            self.current_table = None
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = ()
            self.table_label.config(text="No table selected")
            self.set_status(f"Deleted table: {name}")
        except ValidationError as e:
            messagebox.showerror("Error", str(e))

    def intersect_tables_dialog(self):
        if len(self.db.tables) < 2:
            messagebox.showinfo("Info", "Need at least two tables to intersect.")
            return
        dlg = IntersectDialog(self, sorted(self.db.tables.keys()))
        self.wait_window(dlg)
        if not dlg.result:
            return
        a, b, out_name = dlg.result
        try:
            t1 = self.db.get_table(a)
            t2 = self.db.get_table(b)
            out = t1.intersect(t2, out_name)
            if out.name in self.db.tables:
                raise ValidationError(f"Table '{out.name}' already exists")
            self.db.tables[out.name] = out
            self._refresh_tables_list()
            self.set_status(f"Created intersection table: {out.name}")
        except ValidationError as e:
            messagebox.showerror("Validation error", str(e))

    # ---------------- Row operations ----------------

    def add_row_dialog(self):
        table = self.get_current_table_obj()
        if not table:
            messagebox.showinfo("Info", "Select a table first.")
            return
        dlg = RowDialog(self, table, title=f"Add row to {table.name}")
        self.wait_window(dlg)
        if not dlg.result:
            return
        try:
            table.insert_row(dlg.result)
            self._load_table_into_grid(table)
            self.set_status("Row added")
        except ValidationError as e:
            messagebox.showerror("Validation error", str(e))

    def _get_selected_row_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def edit_selected_row_dialog(self):
        table = self.get_current_table_obj()
        if not table:
            messagebox.showinfo("Info", "Select a table first.")
            return
        idx = self._get_selected_row_index()
        if idx is None:
            messagebox.showinfo("Info", "Select a row first.")
            return
        current = table.rows[idx]
        dlg = RowDialog(self, table, title=f"Edit row #{idx}", initial=current)
        self.wait_window(dlg)
        if not dlg.result:
            return
        try:
            table.update_row(idx, dlg.result)
            self._load_table_into_grid(table)
            self.set_status("Row updated")
        except ValidationError as e:
            messagebox.showerror("Validation error", str(e))

    def delete_selected_row(self):
        table = self.get_current_table_obj()
        if not table:
            messagebox.showinfo("Info", "Select a table first.")
            return
        idx = self._get_selected_row_index()
        if idx is None:
            messagebox.showinfo("Info", "Select a row first.")
            return
        if not messagebox.askyesno("Confirm", f"Delete row #{idx}?"):
            return
        try:
            table.delete_row(idx)
            self._load_table_into_grid(table)
            self.set_status("Row deleted")
        except ValidationError as e:
            messagebox.showerror("Error", str(e))

# ---------------- Dialogs ----------------

class CreateTableDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, types: List[str]):
        super().__init__(master)
        self.title("Create Table")
        self.resizable(False, False)
        self.result: Optional[Tuple[str, List[Tuple[str, str]]]] = None
        self.types = types

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Table name:").grid(row=0, column=0, sticky="w")
        self.e_name = ttk.Entry(frm, width=30)
        self.e_name.grid(row=0, column=1, sticky="we")

        ttk.Label(frm, text="Columns (name, type):").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.cols = tk.Listbox(frm, width=42, height=8)
        self.cols.grid(row=2, column=0, columnspan=2, sticky="we")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="we", pady=(8,0))
        ttk.Button(btns, text="Add column", command=self.add_col).pack(side="left")
        ttk.Button(btns, text="Remove", command=self.remove_col).pack(side="left", padx=(6,0))

        actions = ttk.Frame(frm)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10,0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Create", command=self.submit).pack(side="right", padx=(6,0))

        self.grab_set()
        self.e_name.focus_set()

    def add_col(self):
        name = simpledialog.askstring("Column name", "Enter column name:", parent=self)
        if not name:
            return
        t = TypePickerDialog(self, self.types).pick()
        if not t:
            return
        self.cols.insert(tk.END, f"{name.strip()} : {t}")

    def remove_col(self):
        sel = self.cols.curselection()
        if not sel:
            return
        self.cols.delete(sel[0])

    def submit(self):
        table_name = (self.e_name.get() or "").strip()
        columns: List[Tuple[str, str]] = []
        for i in range(self.cols.size()):
            item = self.cols.get(i)
            if ":" not in item:
                continue
            n, t = item.split(":", 1)
            columns.append((n.strip(), t.strip()))
        if not table_name:
            messagebox.showerror("Error", "Table name is required", parent=self)
            return
        if not columns:
            messagebox.showerror("Error", "Add at least one column", parent=self)
            return
        self.result = (table_name, columns)
        self.destroy()

class TypePickerDialog(tk.Toplevel):
    def __init__(self, master, types: List[str]):
        super().__init__(master)
        self.title("Pick type")
        self.resizable(False, False)
        self.value: Optional[str] = None

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Select column type:").pack(anchor="w")
        self.box = ttk.Combobox(frm, values=types, state="readonly", width=18)
        self.box.current(0)
        self.box.pack(pady=(6,0), anchor="w")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(10,0))
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side="right")
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=(6,0))

        self.grab_set()

    def _ok(self):
        self.value = self.box.get()
        self.destroy()

    def _cancel(self):
        self.value = None
        self.destroy()

    def pick(self) -> Optional[str]:
        self.wait_window(self)
        return self.value

class IntersectDialog(tk.Toplevel):
    def __init__(self, master, table_names: List[str]):
        super().__init__(master)
        self.title("Intersect Tables")
        self.resizable(False, False)
        self.result: Optional[Tuple[str, str, str]] = None

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Table A:").grid(row=0, column=0, sticky="w")
        self.a = ttk.Combobox(frm, values=table_names, state="readonly", width=26)
        self.a.current(0)
        self.a.grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="Table B:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.b = ttk.Combobox(frm, values=table_names, state="readonly", width=26)
        self.b.current(1 if len(table_names) > 1 else 0)
        self.b.grid(row=1, column=1, sticky="w", pady=(6,0))

        ttk.Label(frm, text="Result table name:").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.out = ttk.Entry(frm, width=28)
        self.out.insert(0, "Intersection")
        self.out.grid(row=2, column=1, sticky="w", pady=(6,0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10,0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Create", command=self.submit).pack(side="right", padx=(6,0))

        self.grab_set()

    def submit(self):
        a = self.a.get()
        b = self.b.get()
        out = (self.out.get() or "").strip()
        if not out:
            messagebox.showerror("Error", "Result table name is required", parent=self)
            return
        if a == b:
            messagebox.showerror("Error", "Select two different tables", parent=self)
            return
        self.result = (a, b, out)
        self.destroy()

class RowDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, table: Table, title: str, initial: Optional[List[Any]] = None):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result: Optional[List[Any]] = None
        self.table = table

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        self.entries: List[Any] = []
        for r, col in enumerate(table.columns):
            ttk.Label(frm, text=f"{col.name} ({col.type}):").grid(row=r, column=0, sticky="w", pady=(4,0))
            if col.type.lower() == "dateinvl":
                e1 = ttk.Entry(frm, width=14)
                e2 = ttk.Entry(frm, width=14)
                e1.grid(row=r, column=1, sticky="w", pady=(4,0))
                ttk.Label(frm, text="..").grid(row=r, column=2, sticky="w", pady=(4,0), padx=(6,6))
                e2.grid(row=r, column=3, sticky="w", pady=(4,0))
                self.entries.append(("dateinvl", e1, e2))
            else:
                e = ttk.Entry(frm, width=38)
                e.grid(row=r, column=1, columnspan=3, sticky="w", pady=(4,0))
                self.entries.append(("single", e))

        # preload initial values
        if initial is not None:
            for spec, *objs in self.entries:
                idx = len([None for _ in range(0)])  # dummy
            for i, col in enumerate(table.columns):
                val = initial[i]
                if col.type.lower() == "dateinvl":
                    spec, e1, e2 = self.entries[i]
                    if isinstance(val, DateInvl):
                        e1.insert(0, val.start.isoformat())
                        e2.insert(0, val.end.isoformat())
                    else:
                        # fallback
                        try:
                            e1.insert(0, val[0])
                            e2.insert(0, val[1])
                        except Exception:
                            pass
                else:
                    spec, e = self.entries[i]
                    try:
                        if hasattr(val, "isoformat"):
                            e.insert(0, val.isoformat())
                        else:
                            e.insert(0, str(val))
                    except Exception:
                        e.insert(0, str(val))

        btns = ttk.Frame(frm)
        btns.grid(row=len(table.columns), column=0, columnspan=4, sticky="e", pady=(10,0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="OK", command=self.submit).pack(side="right", padx=(6,0))

        self.grab_set()

    def submit(self):
        raw: List[Any] = []
        for spec in self.entries:
            if spec[0] == "dateinvl":
                _, e1, e2 = spec
                raw.append([e1.get(), e2.get()])
            else:
                _, e = spec
                raw.append(e.get())
        self.result = raw
        self.destroy()

def main():
    app = TableEditorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
