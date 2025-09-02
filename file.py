import os

# Define the directory structure
dirs = [
    "sar_agent/backend/api",
    "sar_agent/backend/core",
    "sar_agent/backend/models",
    "sar_agent/backend/services",
    "sar_agent/backend/utils",
    "sar_agent/frontend/css",
    "sar_agent/frontend/js",
    "sar_agent/frontend/templates",
    "sar_agent/data/input",
    "sar_agent/data/output",
    "sar_agent/data/templates/pdf",
    "sar_agent/data/templates/xml",
    "sar_agent/tests"
]

files = {
    "sar_agent/backend/api/__init__.py": "",
    "sar_agent/backend/core/__init__.py": "",
    "sar_agent/backend/core/app.py": "# Entry point (FastAPI backend)\n",
    "sar_agent/backend/models/__init__.py": "",
    "sar_agent/backend/services/__init__.py": "",
    "sar_agent/backend/utils/__init__.py": "",
    "sar_agent/frontend/templates/index.html": "<!-- Case management prototype -->\n<html><body><h1>SAR/STR Reporting Agent</h1></body></html>",
    "sar_agent/frontend/css/style.css": "/* Basic styles */",
    "sar_agent/frontend/js/app.js": "// Frontend logic placeholder",
    "sar_agent/tests/test_app.py": "# Tests will go here\n",
    "sar_agent/README.md": "# SAR/STR Reporting Agent\n",
    "sar_agent/requirements.txt": "fastapi\nuvicorn\npdfplumber\nlxml\ntransformers\n",
    "sar_agent/Dockerfile": "# Podman-compatible Dockerfile\n",
    "sar_agent/.gitignore": "__pycache__/\n*.pyc\n.env\n"
}

# Create directories
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Create files
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Project directory structure created successfully!")
