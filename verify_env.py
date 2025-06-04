"""
This script verifies that the Python virtual environment is set up correctly
and that all required dependencies are installed.
"""
import importlib
import sys


def check_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} is installed")
        return True
    except ImportError:
        print(f"❌ {module_name} is NOT installed")
        return False


if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("\nChecking required packages:")

    # List of required packages from requirements.txt
    required_packages = [
        "fastapi",
        "uvicorn",
        "atlassian",  # for atlassian-python-api
        "requests",
        "requests_oauthlib",
        "dotenv",  # for python-dotenv
        "aiohttp",
        "pydantic",
        "jmespath",
        "python_multipart",
        "sqlalchemy",
        "pytest",
        "httpx",
    ]

    all_installed = all(check_module(pkg) for pkg in required_packages)

    if all_installed:
        print(
            "\n✨ All dependencies are installed! The virtual environment is set up correctly."
        )
    else:
        print(
            "\n⚠️ Some dependencies are missing. Please run: pip install -r python-server/requirements.txt"
        )
