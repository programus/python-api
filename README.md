# Python Code Execution API

A FastAPI-based Python API platform that executes Python code in isolated virtual environments.

## Features

- **Code Execution Endpoint**: Accepts JSON with Python code and dependencies, returns execution results
- **Isolated Execution**: Each code execution runs in a separate Python virtual environment created with `uv`
- **Fast Dependency Management**: Uses `uv` for ultra-fast package installation
- **Error Handling**: Captures and reports both standard output and errors

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/programus/python-api.git
cd python-api
```

2. Install `uv` (if not already installed):
```bash
pip install uv
```

3. Install dependencies with uv:
```bash
uv pip install --system -r requirements.txt
```

Or with pip:
```bash
pip install -r requirements.txt
```

### Option 2: Docker Installation (Recommended for Production)

1. Clone the repository:
```bash
git clone https://github.com/programus/python-api.git
cd python-api
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or build and run with Docker directly:
```bash
docker build -t python-api .
docker run -p 8000:8000 python-api
```

## Usage

### Starting the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### GET /
Returns API information and version.

**Response:**
```json
{
  "message": "Python Code Execution API",
  "version": "1.0.0",
  "endpoint": "/execute"
}
```

#### POST /execute
Executes Python code in an isolated virtual environment.

**Request Body:**
```json
{
  "code": "print('Hello, World!')",
  "lib": ["requests==2.31.0", "numpy==1.24.0"]
}
```

- `code` (string, required): Python code to execute
- `lib` (array of strings, optional): List of libraries in requirements.txt format

**Response:**
```json
{
  "output": "Hello, World!\n",
  "error": ""
}
```

- `output` (string): Standard output from code execution
- `error` (string): Error information if any occurred

### Examples

#### Example 1: Simple Code Execution

```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")"
  }'
```

Response:
```json
{
  "output": "Hello, World!\n",
  "error": ""
}
```

#### Example 2: Code with Calculations

```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "result = sum(range(1, 11))\nprint(f\"Sum: {result}\")"
  }'
```

Response:
```json
{
  "output": "Sum: 55\n",
  "error": ""
}
```

#### Example 3: Code with External Dependencies

```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import requests\nprint(f\"Requests version: {requests.__version__}\")",
    "lib": ["requests==2.31.0"]
  }'
```

Response:
```json
{
  "output": "Requests version: 2.31.0\n",
  "error": ""
}
```

#### Example 4: Code with Error

```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "raise ValueError(\"This is a test error\")"
  }'
```

Response:
```json
{
  "output": "",
  "error": "Traceback (most recent call last):\n  File \"<string>\", line 1, in <module>\nValueError: This is a test error\n"
}
```

## Testing

A test script is provided to verify the API functionality:

```bash
# Start the server in one terminal
python main.py

# Run tests in another terminal
pip install requests  # Required for test script
python test_api.py
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security Considerations

⚠️ **Warning**: This API executes arbitrary Python code. It should only be used in trusted environments or with proper security measures:

- Consider running in a containerized environment (Docker)
- Implement authentication and authorization
- Set resource limits (CPU, memory, execution time)
- Use network isolation
- Implement rate limiting
- Validate and sanitize inputs

## License

See LICENSE file for details.