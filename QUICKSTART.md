# Quick Start Guide

## Start the Server

```bash
# Local installation
# First install uv (if not already installed)
pip install uv

# Then install dependencies and run
pip install -r requirements.txt
python main.py
```

Or with Docker:
```bash
docker-compose up --build
```

## Make a Request

### Using curl:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "lib": null
  }'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/execute",
    json={
        "code": "print('Hello, World!')",
        "lib": ["requests==2.31.0"]  # Optional
    }
)

result = response.json()
print(f"Output: {result['output']}")
print(f"Error: {result['error']}")
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | /        | API information |
| POST   | /execute | Execute Python code |
| GET    | /docs    | Interactive API documentation (Swagger UI) |
| GET    | /redoc   | Alternative API documentation (ReDoc) |

## Request Format

```json
{
  "code": "string (required) - Python code to execute",
  "lib": ["array of strings (optional) - Dependencies in requirements.txt format"]
}
```

## Response Format

```json
{
  "output": "string - Standard output from code execution",
  "error": "string - Error information if any"
}
```

## Examples

See `examples.py` and `test_api.py` for more comprehensive examples.

## Security Note

⚠️ This API executes arbitrary Python code. Use in trusted environments only or implement proper security measures (authentication, rate limiting, resource limits, etc.).
