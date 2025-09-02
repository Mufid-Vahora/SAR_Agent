$ErrorActionPreference = 'Stop'

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install --upgrade pip | Out-Null
.\.venv\Scripts\python -m pip install -r requirements.txt httpx==0.27.0 | Out-Null

.\.venv\Scripts\python tests\smoke.py
.\.venv\Scripts\python tests\test_xsd_formats.py
