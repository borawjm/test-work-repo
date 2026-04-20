import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock
from urllib.parse import urlparse


class TodoStore:
    def __init__(self):
        self._todos = {}
        self._next_id = 1
        self._lock = Lock()

    def list(self):
        with self._lock:
            return [self._todos[todo_id] for todo_id in sorted(self._todos)]

    def create(self, title):
        with self._lock:
            todo_id = self._next_id
            self._next_id += 1
            todo = {"id": todo_id, "title": title, "completed": False}
            self._todos[todo_id] = todo
            return todo

    def get(self, todo_id):
        with self._lock:
            return self._todos.get(todo_id)

    def update(self, todo_id, title=None, completed=None):
        with self._lock:
            todo = self._todos.get(todo_id)
            if todo is None:
                return None
            if title is not None:
                todo["title"] = title
            if completed is not None:
                todo["completed"] = completed
            return todo

    def delete(self, todo_id):
        with self._lock:
            return self._todos.pop(todo_id, None) is not None


class TodoRequestHandler(BaseHTTPRequestHandler):
    store = TodoStore()
    _todo_path_pattern = re.compile(r"^/todos/(\d+)$")

    def _send_json(self, status_code, payload):
        encoded_payload = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded_payload)))
        self.end_headers()
        self.wfile.write(encoded_payload)

    def _send_empty(self, status_code):
        self.send_response(status_code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _parse_todo_id(self):
        match = self._todo_path_pattern.match(urlparse(self.path).path)
        if match is None:
            return None
        return int(match.group(1))

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if content_length <= 0:
            return None
        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/todos":
            self._send_json(200, self.store.list())
            return

        todo_id = self._parse_todo_id()
        if todo_id is None:
            self._send_json(404, {"error": "Not Found"})
            return

        todo = self.store.get(todo_id)
        if todo is None:
            self._send_json(404, {"error": "Todo not found"})
            return

        self._send_json(200, todo)

    def do_POST(self):
        if urlparse(self.path).path != "/todos":
            self._send_json(404, {"error": "Not Found"})
            return

        payload = self._read_json_body()
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            self._send_json(400, {"error": "title is required"})
            return

        todo = self.store.create(title.strip())
        self._send_json(201, todo)

    def do_PUT(self):
        todo_id = self._parse_todo_id()
        if todo_id is None:
            self._send_json(404, {"error": "Not Found"})
            return

        payload = self._read_json_body()
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        title = payload.get("title")
        completed = payload.get("completed")
        if title is None and completed is None:
            self._send_json(400, {"error": "title or completed is required"})
            return
        if title is not None and (not isinstance(title, str) or not title.strip()):
            self._send_json(400, {"error": "title must be a non-empty string"})
            return
        if completed is not None and not isinstance(completed, bool):
            self._send_json(400, {"error": "completed must be a boolean"})
            return

        todo = self.store.update(
            todo_id, title=title.strip() if title is not None else None, completed=completed
        )
        if todo is None:
            self._send_json(404, {"error": "Todo not found"})
            return

        self._send_json(200, todo)

    def do_DELETE(self):
        todo_id = self._parse_todo_id()
        if todo_id is None:
            self._send_json(404, {"error": "Not Found"})
            return

        if not self.store.delete(todo_id):
            self._send_json(404, {"error": "Todo not found"})
            return

        self._send_empty(204)

    def log_message(self, format, *args):
        return


def run_server(host="127.0.0.1", port=8000):
    server = HTTPServer((host, port), TodoRequestHandler)
    print(f"Todo API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
