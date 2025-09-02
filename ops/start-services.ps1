param(
  [string]$ModelName = "sshleifer/tiny-gpt2",
  [string]$ServiceHost = "127.0.0.1"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install --upgrade pip | Out-Null
.\.venv\Scripts\python -m pip install -r requirements.txt | Out-Null

$env:TEMPLATES_DIR = "$PWD\data\templates"
$env:INDEX_DIR = "$PWD\data\indexes"
$env:MODEL_NAME = $ModelName
New-Item -ItemType Directory -Force -Path $env:TEMPLATES_DIR,$env:INDEX_DIR | Out-Null

Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.template_fetcher.app.main:app','--host',$ServiceHost,'--port','8082'
Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.rag.app.main:app','--host',$ServiceHost,'--port','8083'
Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.llm_filler.app.main:app','--host',$ServiceHost,'--port','8084'
Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.validator.app.main:app','--host',$ServiceHost,'--port','8085'
Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.format_selector.app.main:app','--host',$ServiceHost,'--port','8086'
Start-Process -NoNewWindow .\.venv\Scripts\python -ArgumentList '-m','uvicorn','services.orchestrator.app.main:app','--host',$ServiceHost,'--port','8087'

Write-Host "Services started on $ServiceHost - 8082 (template), 8083 (rag), 8084 (llm), 8085 (validator), 8086 (format_selector), 8087 (orchestrator)"
