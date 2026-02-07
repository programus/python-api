"""
FastAPI-based Python code execution platform.
Accepts JSON with Python code and dependencies, executes in isolated venv.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="Python Code Execution API",
    description="Execute Python code in isolated virtual environments",
    version="1.0.0"
)


class CodeExecutionRequest(BaseModel):
    """Request model for code execution."""
    code: str = Field(..., description="Python code to execute")
    lib: Optional[List[str]] = Field(
        default=None,
        description="List of libraries in requirements.txt format"
    )


class CodeExecutionResponse(BaseModel):
    """Response model for code execution."""
    output: str = Field(default="", description="Standard output from code execution")
    error: str = Field(default="", description="Error information if any")


def create_venv(venv_path: Path) -> bool:
    """Create a virtual environment at the specified path using uv."""
    try:
        subprocess.run(
            ["uv", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return False


def install_dependencies(venv_path: Path, dependencies: List[str]) -> tuple[bool, str]:
    """Install dependencies in the virtual environment using uv."""
    if not dependencies:
        return True, ""
    
    # Create a temporary requirements file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
        req_file.write('\n'.join(dependencies))
        req_file_path = req_file.name
    
    try:
        result = subprocess.run(
            ["uv", "pip", "install", "-r", req_file_path, "--python", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        os.unlink(req_file_path)
        
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if os.path.exists(req_file_path):
            os.unlink(req_file_path)
        return False, str(e)


def execute_code_in_venv(venv_path: Path, code: str) -> tuple[str, str]:
    """Execute Python code in the virtual environment."""
    # Determine python executable path
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python"
    else:
        python_path = venv_path / "bin" / "python"
    
    try:
        result = subprocess.run(
            [str(python_path), "-c", code],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Error: Code execution timed out (30 seconds limit)"
    except Exception as e:
        return "", f"Error: {str(e)}"


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Python Code Execution API",
        "version": "1.0.0",
        "endpoint": "/execute"
    }


@app.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    Execute Python code in an isolated virtual environment.
    
    Args:
        request: CodeExecutionRequest containing code and optional libraries
        
    Returns:
        CodeExecutionResponse with output and error information
    """
    venv_dir = None
    
    try:
        # Create temporary directory for venv
        venv_dir = Path(tempfile.mkdtemp(prefix="pyapi_venv_"))
        
        # Create virtual environment
        if not create_venv(venv_dir):
            return CodeExecutionResponse(
                output="",
                error="Failed to create virtual environment"
            )
        
        # Install dependencies if provided
        if request.lib:
            success, error_msg = install_dependencies(venv_dir, request.lib)
            if not success:
                return CodeExecutionResponse(
                    output="",
                    error=f"Failed to install dependencies: {error_msg}"
                )
        
        # Execute the code
        output, error = execute_code_in_venv(venv_dir, request.code)
        
        return CodeExecutionResponse(
            output=output,
            error=error
        )
        
    except Exception as e:
        return CodeExecutionResponse(
            output="",
            error=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Clean up the virtual environment
        if venv_dir and venv_dir.exists():
            try:
                shutil.rmtree(venv_dir)
            except Exception:
                pass  # Best effort cleanup


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
