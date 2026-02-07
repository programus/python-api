# Python Code Execution API

A FastAPI-based Python API platform that executes Python code in isolated virtual environments.

## Features

- **Code Execution Endpoint**: Accepts JSON with Python code and dependencies, returns execution results
- **Isolated Execution**: Each code execution runs in a separate Python virtual environment
- **Named Virtual Environments**: Optionally cache and reuse virtual environments by name
- **Dependency Management**: Automatically installs required libraries before code execution
- **Error Handling**: Captures and reports both standard output and errors

## Development Setup

This project uses `uv` for development dependency management.

1. Clone the repository:
```bash
git clone https://github.com/programus/python-api.git
cd python-api
```

2. Install `uv` (if not already installed):
```bash
pip install uv
```

3. Sync dependencies (creates `.venv` and installs all dependencies):
```bash
uv sync
```

4. Activate the virtual environment:
```bash
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows
```

## Installation

### Option 1: Local Installation (for production/deployment)

1. Clone the repository:
```bash
git clone https://github.com/programus/python-api.git
cd python-api
```

2. Install dependencies with pip:
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

## Configuration

The API supports several environment variables for configuration:

### Timeout Configuration

- **VENV_CREATE_TIMEOUT**: Timeout in seconds for virtual environment creation (default: 30)
- **DEPENDENCY_INSTALL_TIMEOUT**: Timeout in seconds for dependency installation (default: 300)
- **CODE_EXECUTION_TIMEOUT**: Timeout in seconds for code execution (default: 30)

Example:
```bash
export VENV_CREATE_TIMEOUT=60
export DEPENDENCY_INSTALL_TIMEOUT=600
export CODE_EXECUTION_TIMEOUT=45
python main.py
```

Or with Docker:
```bash
docker run -p 8000:8000 \
  -e VENV_CREATE_TIMEOUT=60 \
  -e DEPENDENCY_INSTALL_TIMEOUT=600 \
  -e CODE_EXECUTION_TIMEOUT=45 \
  python-api
```

### Logging

The API logs all commands and their output to stdout, making it easy to debug issues. Logs include:
- Virtual environment creation commands and output
- Dependency installation commands and output
- Code execution commands and output
- Timing information for all operations
- Error messages with full stack traces

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
  "lib": ["requests==2.31.0", "numpy==1.24.0"],
  "name": "my-env"
}
```

- `code` (string, required): Python code to execute
- `lib` (array of strings, optional): List of libraries in requirements.txt format
- `name` (string, optional): Name for caching the virtual environment. If provided:
  - The venv will be cached and reused for subsequent requests with the same name
  - If the `lib` list changes, the venv will be recreated
  - If the `lib` list is the same, the existing venv is reused (faster execution)

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

#### Example 5: Named Virtual Environment (Caching)

First request creates the venv:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import requests\nprint(f\"Requests version: {requests.__version__}\")",
    "lib": ["requests==2.31.0"],
    "name": "my-requests-env"
  }'
```

Second request reuses the same venv (faster):
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import requests\nprint(\"Using cached environment!\")",
    "lib": ["requests==2.31.0"],
    "name": "my-requests-env"
  }'
```

If you change the libraries, the venv is recreated:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import requests\nimport pandas as pd\nprint(\"New environment created!\")",
    "lib": ["requests==2.31.0", "pandas==2.0.0"],
    "name": "my-requests-env"
  }'
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