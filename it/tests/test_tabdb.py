import unittest
from tabdb.core import Database
from tabdb.types import ValidationError
from tabdb.storage_json import save_json, load_json
import tempfile
import os

class TestTabDB(unittest.TestCase):
    def test_date_validation_rejects_invalid(self):
        db = Database()
        t = db.create_table("T", [("d", "date")])
        with self.assertRaises(ValidationError):
            t.insert_row(["2025-02-30"])  # invalid date

    def test_dateinvl_validation_order(self):
        db = Database()
        t = db.create_table("T", [("inv", "dateInvl")])
        with self.assertRaises(ValidationError):
            t.insert_row([["2025-02-10", "2025-01-01"]])  # start > end

    def test_intersection_operation_variant(self):
        # INDIVIDUAL OPERATION: table intersection
        db = Database()
        a = db.create_table("A", [("id", "integer"), ("name", "string")])
        b = db.create_table("B", [("id", "integer"), ("name", "string")])

        a.insert_row(["1", "x"])
        a.insert_row(["2", "y"])
        b.insert_row(["2", "y"])
        b.insert_row(["3", "z"])

        inter = a.intersect(b, "I")
        self.assertEqual(inter.name, "I")
        self.assertEqual(len(inter.rows), 1)
        self.assertEqual(inter.rows[0][0], 2)
        self.assertEqual(inter.rows[0][1], "y")

    def test_save_load_roundtrip_json(self):
        db = Database(name="DB")
        t = db.create_table("T", [("id","integer"), ("when","date")])
        t.insert_row([1, "2025-01-01"])

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "db.json")
            save_json(db, path)
            db2 = load_json(path)

        self.assertIn("T", db2.tables)
        t2 = db2.get_table("T")
        self.assertEqual(t2.rows[0][0], 1)
        self.assertEqual(t2.rows[0][1].isoformat(), "2025-01-01")

if __name__ == "__main__":
    unittest.main()
