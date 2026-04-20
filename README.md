# test-work-repo

Simple Todo API implemented with Python's standard library.

## Run the API

```bash
python todo_api.py
```

The API starts on `http://127.0.0.1:8000`.

## Endpoints

- `GET /todos` - List todos
- `POST /todos` - Create todo (`{"title":"..."}`)
- `GET /todos/{id}` - Get single todo
- `PUT /todos/{id}` - Update todo (`{"title":"...","completed":true}`)
- `DELETE /todos/{id}` - Delete todo

## Run tests

```bash
python -m unittest -v
```
