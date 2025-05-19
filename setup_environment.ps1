$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    # Save the current color
    $CurrentForegroundColor = $host.UI.RawUI.ForegroundColor
    
    # Set the new color
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    
    # Write the output
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    
    # Restore the original color
    $host.UI.RawUI.ForegroundColor = $CurrentForegroundColor
}

Write-ColorOutput Green "========================================================="
Write-ColorOutput Green "      JIRA CHATBOT API - COMPLETE SETUP SCRIPT"
Write-ColorOutput Green "========================================================="
Write-ColorOutput Yellow "This script will set up the complete Python environment for this project."
Write-Output ""

# 1. Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-ColorOutput Cyan "1. Creating Python virtual environment..."
    try {
        python -m venv .venv
        Write-ColorOutput Green "✓ Virtual environment created successfully."
    } catch {
        Write-ColorOutput Red "✗ Failed to create virtual environment: $_"
        exit 1
    }
} else {
    Write-ColorOutput Cyan "1. Virtual environment already exists."
}

# 2. Activate and install requirements
Write-ColorOutput Cyan "2. Installing project dependencies..."
try {
    & ".\.venv\Scripts\pip" install --upgrade pip
    & ".\.venv\Scripts\pip" install -r python-server\requirements.txt
    Write-ColorOutput Green "✓ Basic dependencies installed successfully."
} catch {
    Write-ColorOutput Red "✗ Failed to install dependencies: $_"
    exit 1
}

# 3. Install development tools
Write-ColorOutput Cyan "3. Installing development tools (black, pylint, pytest-cov)..."
try {
    & ".\.venv\Scripts\pip" install black pylint pytest-cov pre-commit
    Write-ColorOutput Green "✓ Development tools installed successfully."
} catch {
    Write-ColorOutput Red "✗ Failed to install development tools: $_"
    exit 1
}

# 4. Initialize pre-commit hooks
Write-ColorOutput Cyan "4. Setting up pre-commit hooks..."
try {
    & ".\.venv\Scripts\pre-commit" install
    Write-ColorOutput Green "✓ Pre-commit hooks installed successfully."
} catch {
    Write-ColorOutput Yellow "⚠ Pre-commit hooks setup failed. This is not critical, you can continue."
}

# 5. Run verification script
Write-ColorOutput Cyan "5. Verifying installation..."
try {
    & ".\.venv\Scripts\python" verify_env.py
    Write-ColorOutput Green "✓ Environment verification completed."
} catch {
    Write-ColorOutput Red "✗ Environment verification failed: $_"
    exit 1
}

# 6. Final message
Write-ColorOutput Green "========================================================="
Write-ColorOutput Green "                SETUP COMPLETE!"
Write-ColorOutput Green "========================================================="
Write-Output ""
Write-ColorOutput Cyan "You can now run the server with:"
Write-ColorOutput Yellow "    .\run-server.ps1"
Write-Output ""
Write-ColorOutput Cyan "The API will be available at:"
Write-ColorOutput Yellow "    http://localhost:8000"
Write-ColorOutput Cyan "API documentation available at:"
Write-ColorOutput Yellow "    http://localhost:8000/docs"
Write-Output ""
Write-ColorOutput Cyan "Happy coding! 🚀"
