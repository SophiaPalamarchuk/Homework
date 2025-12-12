import unittest
from fastapi.testclient import TestClient
from main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.post("/db/new", json={"name": "DB"})

    def test_intersection(self):
        self.client.post("/tables", json={
            "name":"A",
            "columns":[{"name":"id","type":"integer"},{"name":"name","type":"string"}]
        })
        self.client.post("/tables", json={
            "name":"B",
            "columns":[{"name":"id","type":"integer"},{"name":"name","type":"string"}]
        })
        self.client.post("/tables/A/rows", json={"values":[1,"x"]})
        self.client.post("/tables/A/rows", json={"values":[2,"y"]})
        self.client.post("/tables/B/rows", json={"values":[2,"y"]})

        r = self.client.post("/tables/intersect", json={"a":"A","b":"B","result_name":"I"})
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/tables/I")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["rows"]), 1)

if __name__ == "__main__":
    unittest.main()
