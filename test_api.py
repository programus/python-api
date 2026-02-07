"""
Test script for the Python Code Execution API
"""
import requests
import json


BASE_URL = "http://localhost:8000"


def test_simple_code():
    """Test simple code execution without dependencies."""
    print("Test 1: Simple code execution")
    payload = {
        "code": "print('Hello, World!')",
        "lib": None
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "Hello, World!" in result["output"]
    print("✓ Test 1 passed\n")


def test_code_with_calculation():
    """Test code with calculations."""
    print("Test 2: Code with calculation")
    payload = {
        "code": "result = 2 + 2\nprint(f'Result: {result}')"
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "Result: 4" in result["output"]
    print("✓ Test 2 passed\n")


def test_code_with_dependencies():
    """Test code execution with external dependencies."""
    print("Test 3: Code with dependencies (requests library)")
    payload = {
        "code": "import requests\nprint(f'Requests version: {requests.__version__}')",
        "lib": ["requests==2.31.0"]
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "Requests version:" in result["output"]
    print("✓ Test 3 passed\n")


def test_code_with_error():
    """Test code that produces an error."""
    print("Test 4: Code with error")
    payload = {
        "code": "raise ValueError('This is a test error')"
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "ValueError" in result["error"] or "ValueError" in result["output"]
    print("✓ Test 4 passed\n")


def test_root_endpoint():
    """Test root endpoint."""
    print("Test 5: Root endpoint")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Test 5 passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Python Code Execution API Tests")
    print("=" * 60)
    print("Make sure the API is running at http://localhost:8000")
    print("=" * 60)
    print()
    
    try:
        test_root_endpoint()
        test_simple_code()
        test_code_with_calculation()
        test_code_with_dependencies()
        test_code_with_error()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
