"""
Example usage of the Python Code Execution API
Demonstrates various use cases
"""
import requests
import json

API_URL = "http://localhost:8000/execute"


def execute_code(code, lib=None):
    """Helper function to execute code via the API."""
    payload = {"code": code}
    if lib:
        payload["lib"] = lib
    
    response = requests.post(API_URL, json=payload)
    return response.json()


def example1_hello_world():
    """Example 1: Simple Hello World"""
    print("\n" + "="*60)
    print("Example 1: Simple Hello World")
    print("="*60)
    
    code = 'print("Hello, World!")'
    result = execute_code(code)
    
    print(f"Code: {code}")
    print(f"Output: {result['output']}")
    print(f"Error: {result['error']}")


def example2_calculations():
    """Example 2: Mathematical calculations"""
    print("\n" + "="*60)
    print("Example 2: Mathematical Calculations")
    print("="*60)
    
    code = """
import math

# Calculate circle properties
radius = 5
area = math.pi * radius ** 2
circumference = 2 * math.pi * radius

print(f"Circle with radius {radius}:")
print(f"  Area: {area:.2f}")
print(f"  Circumference: {circumference:.2f}")
"""
    
    result = execute_code(code)
    print(f"Output:\n{result['output']}")
    if result['error']:
        print(f"Error: {result['error']}")


def example3_with_dependencies():
    """Example 3: Using external libraries"""
    print("\n" + "="*60)
    print("Example 3: Using External Libraries (requests)")
    print("="*60)
    
    code = """
import requests

# Check if requests library is available
print(f"Requests library version: {requests.__version__}")
print("Successfully imported requests!")
"""
    
    lib = ["requests==2.31.0"]
    result = execute_code(code, lib)
    
    print(f"Dependencies: {lib}")
    print(f"Output:\n{result['output']}")
    if result['error']:
        print(f"Error: {result['error']}")


def example4_data_processing():
    """Example 4: Data processing with pandas"""
    print("\n" + "="*60)
    print("Example 4: Data Processing with Pandas")
    print("="*60)
    
    code = """
import pandas as pd

# Create a simple dataset
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 35, 40],
    'score': [85, 90, 78, 92]
}

df = pd.DataFrame(data)
print("Dataset:")
print(df)
print()
print("Statistics:")
print(df.describe())
"""
    
    lib = ["pandas==2.0.3"]
    result = execute_code(code, lib)
    
    print(f"Dependencies: {lib}")
    print(f"Output:\n{result['output']}")
    if result['error']:
        print(f"Error: {result['error']}")


def example5_error_handling():
    """Example 5: Error handling"""
    print("\n" + "="*60)
    print("Example 5: Error Handling")
    print("="*60)
    
    code = """
def divide(a, b):
    return a / b

result = divide(10, 0)  # This will raise an error
print(f"Result: {result}")
"""
    
    result = execute_code(code)
    print(f"Output: {result['output']}")
    print(f"Error:\n{result['error']}")


def example6_file_operations():
    """Example 6: File operations in venv"""
    print("\n" + "="*60)
    print("Example 6: File Operations in Virtual Environment")
    print("="*60)
    
    code = """
import os
import tempfile

# Create a temp file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write("Hello from temporary file!")
    temp_path = f.name

# Read the file
with open(temp_path, 'r') as f:
    content = f.read()

print(f"Temp file created at: {temp_path}")
print(f"Content: {content}")

# Clean up
os.unlink(temp_path)
print("Temp file cleaned up successfully!")
"""
    
    result = execute_code(code)
    print(f"Output:\n{result['output']}")
    if result['error']:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Python Code Execution API - Example Usage")
    print("="*60)
    print("Make sure the API server is running at http://localhost:8000")
    print()
    
    try:
        # Run all examples
        example1_hello_world()
        example2_calculations()
        example3_with_dependencies()
        example4_data_processing()
        example5_error_handling()
        example6_file_operations()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("Please make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
