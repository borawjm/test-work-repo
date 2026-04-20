import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from todo_api import TodoRequestHandler, TodoStore


class TodoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TodoRequestHandler.store = TodoStore()
        cls.server = HTTPServer(("127.0.0.1", 0), TodoRequestHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        TodoRequestHandler.store = TodoStore()

    def request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=2) as response:
                content = response.read()
                return response.status, json.loads(content) if content else None
        except HTTPError as err:
            content = err.read()
            return err.code, json.loads(content) if content else None

    def test_create_and_list_todo(self):
        status, created = self.request("POST", "/todos", {"title": "Write tests"})
        self.assertEqual(status, 201)
        self.assertEqual(created["id"], 1)
        self.assertEqual(created["title"], "Write tests")
        self.assertFalse(created["completed"])

        status, todos = self.request("GET", "/todos")
        self.assertEqual(status, 200)
        self.assertEqual(todos, [created])

    def test_update_todo(self):
        _, created = self.request("POST", "/todos", {"title": "Initial"})
        status, updated = self.request(
            "PUT",
            f"/todos/{created['id']}",
            {"title": "Updated", "completed": True},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Updated")
        self.assertTrue(updated["completed"])

    def test_delete_todo(self):
        _, created = self.request("POST", "/todos", {"title": "Delete me"})
        status, _ = self.request("DELETE", f"/todos/{created['id']}")
        self.assertEqual(status, 204)

        status, body = self.request("GET", f"/todos/{created['id']}")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"error": "Todo not found"})

    def test_invalid_create_payload_returns_400(self):
        status, body = self.request("POST", "/todos", {"title": ""})
        self.assertEqual(status, 400)
        self.assertEqual(body, {"error": "title is required"})


if __name__ == "__main__":
    unittest.main()
