"""
FastAPI-based Python code execution platform.
Accepts JSON with Python code and dependencies, executes in isolated venv.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import hashlib
import json
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
    name: Optional[str] = Field(
        default=None,
        description="Optional name to cache and reuse virtual environment"
    )


class CodeExecutionResponse(BaseModel):
    """Response model for code execution."""
    output: str = Field(default="", description="Standard output from code execution")
    error: str = Field(default="", description="Error information if any")


def create_venv(venv_path: Path) -> bool:
    """Create a virtual environment at the specified path."""
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return False


def install_dependencies(venv_path: Path, dependencies: List[str]) -> tuple[bool, str]:
    """Install dependencies in the virtual environment."""
    if not dependencies:
        return True, ""
    
    # Determine pip executable path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    # Create a temporary requirements file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
        req_file.write('\n'.join(dependencies))
        req_file_path = req_file.name
    
    try:
        result = subprocess.run(
            [str(pip_path), "install", "-r", req_file_path],
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


# Directory for cached virtual environments
VENV_CACHE_DIR = Path(tempfile.gettempdir()) / "pyapi_cached_venvs"
VENV_CACHE_DIR.mkdir(exist_ok=True)


def get_venv_metadata_path(venv_name: str) -> Path:
    """Get the path to the metadata file for a named venv."""
    return VENV_CACHE_DIR / f"{venv_name}.metadata.json"


def get_cached_venv_path(venv_name: str) -> Path:
    """Get the path to a cached venv by name."""
    return VENV_CACHE_DIR / venv_name


def save_venv_metadata(venv_name: str, lib: Optional[List[str]]):
    """Save metadata about a cached venv."""
    metadata = {
        "lib": lib or [],
        "created_at": __import__('time').time()
    }
    metadata_path = get_venv_metadata_path(venv_name)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)


def load_venv_metadata(venv_name: str) -> Optional[dict]:
    """Load metadata about a cached venv."""
    metadata_path = get_venv_metadata_path(venv_name)
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def should_recreate_venv(venv_name: str, requested_lib: Optional[List[str]]) -> bool:
    """
    Check if a venv should be recreated based on lib comparison.
    Returns True if venv needs recreation, False if it can be reused.
    """
    venv_path = get_cached_venv_path(venv_name)
    metadata = load_venv_metadata(venv_name)
    
    # If venv doesn't exist or no metadata, needs creation
    if not venv_path.exists() or metadata is None:
        return True
    
    # Compare lib lists (normalize to empty list if None)
    existing_lib = set(metadata.get("lib", []))
    new_lib = set(requested_lib or [])
    
    # If libs are different, recreate
    return existing_lib != new_lib


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
        request: CodeExecutionRequest containing code, optional libraries, and optional name
        
    Returns:
        CodeExecutionResponse with output and error information
    """
    venv_dir = None
    is_temporary_venv = True
    
    try:
        # Check if we should use a named/cached venv
        if request.name:
            is_temporary_venv = False
            venv_dir = get_cached_venv_path(request.name)
            
            # Check if we need to recreate the venv
            if should_recreate_venv(request.name, request.lib):
                # Remove existing venv if it exists
                if venv_dir.exists():
                    try:
                        shutil.rmtree(venv_dir)
                    except Exception:
                        pass
                
                # Create new virtual environment
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
                
                # Save metadata for the cached venv
                save_venv_metadata(request.name, request.lib)
            # else: venv exists and libs match, reuse it
        else:
            # Create temporary venv (original behavior)
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
        # Clean up only if it's a temporary venv
        if is_temporary_venv and venv_dir and venv_dir.exists():
            try:
                shutil.rmtree(venv_dir)
            except Exception:
                pass  # Best effort cleanup


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
