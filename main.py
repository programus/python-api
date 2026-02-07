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
import time
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configure timeouts from environment variables
VENV_CREATE_TIMEOUT = int(os.getenv("VENV_CREATE_TIMEOUT", "30"))
DEPENDENCY_INSTALL_TIMEOUT = int(os.getenv("DEPENDENCY_INSTALL_TIMEOUT", "300"))
CODE_EXECUTION_TIMEOUT = int(os.getenv("CODE_EXECUTION_TIMEOUT", "30"))

# Configure cache directory - use environment variable or default to temp dir
VENV_CACHE_DIR_PATH = os.getenv("VENV_CACHE_DIR", os.path.join(tempfile.gettempdir(), "pyapi_cached_venvs"))

logger.info(f"Configuration loaded:")
logger.info(f"  VENV_CREATE_TIMEOUT: {VENV_CREATE_TIMEOUT}s")
logger.info(f"  DEPENDENCY_INSTALL_TIMEOUT: {DEPENDENCY_INSTALL_TIMEOUT}s")
logger.info(f"  CODE_EXECUTION_TIMEOUT: {CODE_EXECUTION_TIMEOUT}s")
logger.info(f"  VENV_CACHE_DIR: {VENV_CACHE_DIR_PATH}")



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
    cmd = [sys.executable, "-m", "venv", str(venv_path)]
    logger.info(f"Creating virtual environment at: {venv_path}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=VENV_CREATE_TIMEOUT
        )
        
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.info(f"STDERR: {result.stderr}")
        
        logger.info(f"Virtual environment created successfully at: {venv_path}")
        return True
    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout creating virtual environment after {VENV_CREATE_TIMEOUT}s")
        logger.error(f"Partial STDOUT: {e.stdout if e.stdout else 'N/A'}")
        logger.error(f"Partial STDERR: {e.stderr if e.stderr else 'N/A'}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment (exit code {e.returncode})")
        logger.error(f"STDOUT: {e.stdout if e.stdout else 'N/A'}")
        logger.error(f"STDERR: {e.stderr if e.stderr else 'N/A'}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating virtual environment: {str(e)}")
        return False


def install_dependencies(venv_path: Path, dependencies: List[str]) -> tuple[bool, str]:
    """Install dependencies in the virtual environment."""
    if not dependencies:
        logger.info("No dependencies to install")
        return True, ""
    
    logger.info(f"Installing {len(dependencies)} dependencies: {dependencies}")
    
    # Determine pip executable path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    # Create a temporary requirements file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
        req_file.write('\n'.join(dependencies))
        req_file_path = req_file.name
    
    logger.info(f"Created temporary requirements file: {req_file_path}")
    
    # Use CA certificate from accessible location
    # Try multiple cert file locations in order of preference
    cert_candidates = [
        '/usr/local/share/ca-certificates.crt',  # Our custom copy
        '/etc/ssl/cert.pem',  # Standard location
    ]
    cert_file = next((f for f in cert_candidates if os.path.exists(f)), None)
    
    if cert_file:
        logger.info(f"Using certificate file: {cert_file}")
        cmd = [str(pip_path), "install", "--cert", cert_file, "-r", req_file_path]
    else:
        logger.warning("No accessible certificate file found, proceeding without --cert flag")
        cmd = [str(pip_path), "install", "-r", req_file_path]
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Prepare environment with SSL certificate settings
    env = os.environ.copy()
    # Use accessible certificate file location
    cert_candidates = [
        '/usr/local/share/ca-certificates.crt',  # Our custom copy
        '/etc/ssl/cert.pem',  # Standard location
    ]
    accessible_cert = next((f for f in cert_candidates if os.path.exists(f)), None)
    if accessible_cert:
        env['SSL_CERT_FILE'] = accessible_cert
        env['REQUESTS_CA_BUNDLE'] = accessible_cert
        logger.info(f"Set SSL_CERT_FILE and REQUESTS_CA_BUNDLE to: {accessible_cert}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=DEPENDENCY_INSTALL_TIMEOUT,
            env=env
        )
        os.unlink(req_file_path)
        
        # Log output (even on success, pip produces useful output)
        if result.stdout:
            logger.info(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.info(f"STDERR:\n{result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Dependency installation failed (exit code {result.returncode})")
            return False, result.stderr
        
        logger.info("Dependencies installed successfully")
        return True, ""
    except subprocess.TimeoutExpired as e:
        if os.path.exists(req_file_path):
            os.unlink(req_file_path)
        logger.error(f"Timeout installing dependencies after {DEPENDENCY_INSTALL_TIMEOUT}s")
        logger.error(f"Partial STDOUT: {e.stdout if e.stdout else 'N/A'}")
        logger.error(f"Partial STDERR: {e.stderr if e.stderr else 'N/A'}")
        return False, f"Error: Dependency installation timed out ({DEPENDENCY_INSTALL_TIMEOUT} seconds limit)"
    except Exception as e:
        if os.path.exists(req_file_path):
            os.unlink(req_file_path)
        logger.error(f"Unexpected error installing dependencies: {str(e)}")
        return False, str(e)


def execute_code_in_venv(venv_path: Path, code: str) -> tuple[str, str]:
    """Execute Python code in the virtual environment."""
    # Determine python executable path
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python"
    else:
        python_path = venv_path / "bin" / "python"
    
    cmd = [str(python_path), "-c", code]
    logger.info(f"Executing code in venv: {venv_path}")
    logger.info(f"Command: {cmd[0]} -c <code>")
    logger.info(f"Code to execute:\n{code}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CODE_EXECUTION_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Code execution completed in {elapsed:.2f}s")
        
        if result.stdout:
            logger.info(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.info(f"STDERR:\n{result.stderr}")
        
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start_time
        logger.error(f"Code execution timed out after {CODE_EXECUTION_TIMEOUT}s (elapsed: {elapsed:.2f}s)")
        logger.error(f"Partial STDOUT: {e.stdout if e.stdout else 'N/A'}")
        logger.error(f"Partial STDERR: {e.stderr if e.stderr else 'N/A'}")
        return "", f"Error: Code execution timed out ({CODE_EXECUTION_TIMEOUT} seconds limit)"
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Unexpected error executing code (elapsed: {elapsed:.2f}s): {str(e)}")
        return "", f"Error: {str(e)}"


# Directory for cached virtual environments
VENV_CACHE_DIR = Path(VENV_CACHE_DIR_PATH)

# Create cache directory with proper error handling
try:
    VENV_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Cache directory ready: {VENV_CACHE_DIR}")
except PermissionError as e:
    logger.error(f"Permission denied creating cache directory {VENV_CACHE_DIR}: {e}")
    logger.warning("Cached venvs will not be available. Only temporary venvs will work.")
except Exception as e:
    logger.error(f"Error creating cache directory {VENV_CACHE_DIR}: {e}")
    logger.warning("Cached venvs may not work properly.")


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
        "created_at": time.time()
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
    logger.info("="*80)
    logger.info("New code execution request received")
    logger.info(f"Named venv: {request.name if request.name else 'No (temporary)'}")
    logger.info(f"Dependencies: {request.lib if request.lib else 'None'}")
    logger.info("="*80)
    
    venv_dir = None
    is_temporary_venv = True
    
    try:
        # Check if we should use a named/cached venv
        if request.name:
            is_temporary_venv = False
            venv_dir = get_cached_venv_path(request.name)
            logger.info(f"Using named venv: {request.name}")
            
            # Check if we need to recreate the venv
            if should_recreate_venv(request.name, request.lib):
                logger.info(f"Venv needs to be created/recreated")
                # Remove existing venv if it exists
                if venv_dir.exists():
                    logger.info(f"Removing existing venv at: {venv_dir}")
                    try:
                        shutil.rmtree(venv_dir)
                    except Exception as e:
                        logger.warning(f"Failed to remove existing venv: {e}")
                
                # Create new virtual environment
                if not create_venv(venv_dir):
                    logger.error("Failed to create virtual environment")
                    return CodeExecutionResponse(
                        output="",
                        error="Failed to create virtual environment"
                    )
                
                # Install dependencies if provided
                if request.lib:
                    success, error_msg = install_dependencies(venv_dir, request.lib)
                    if not success:
                        logger.error(f"Failed to install dependencies: {error_msg}")
                        return CodeExecutionResponse(
                            output="",
                            error=f"Failed to install dependencies: {error_msg}"
                        )
                
                # Save metadata for the cached venv
                save_venv_metadata(request.name, request.lib)
                logger.info(f"Saved metadata for cached venv: {request.name}")
            else:
                logger.info(f"Reusing existing venv at: {venv_dir}")
        else:
            # Create temporary venv (original behavior)
            venv_dir = Path(tempfile.mkdtemp(prefix="pyapi_venv_"))
            logger.info(f"Creating temporary venv at: {venv_dir}")
            
            # Create virtual environment
            if not create_venv(venv_dir):
                logger.error("Failed to create virtual environment")
                return CodeExecutionResponse(
                    output="",
                    error="Failed to create virtual environment"
                )
            
            # Install dependencies if provided
            if request.lib:
                success, error_msg = install_dependencies(venv_dir, request.lib)
                if not success:
                    logger.error(f"Failed to install dependencies: {error_msg}")
                    return CodeExecutionResponse(
                        output="",
                        error=f"Failed to install dependencies: {error_msg}"
                    )
        
        # Execute the code
        output, error = execute_code_in_venv(venv_dir, request.code)
        
        logger.info("Code execution request completed successfully")
        logger.info("="*80)
        
        return CodeExecutionResponse(
            output=output,
            error=error
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in execute_code: {str(e)}", exc_info=True)
        logger.info("="*80)
        return CodeExecutionResponse(
            output="",
            error=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Clean up only if it's a temporary venv
        if is_temporary_venv and venv_dir and venv_dir.exists():
            logger.info(f"Cleaning up temporary venv: {venv_dir}")
            try:
                shutil.rmtree(venv_dir)
                logger.info("Temporary venv cleaned up successfully")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary venv: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
