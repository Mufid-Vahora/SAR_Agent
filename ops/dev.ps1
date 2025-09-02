param(
  [switch]$Up,
  [switch]$Down,
  [switch]$Logs,
  [switch]$Build
)

if ($Up) { docker compose up -d --build }
elseif ($Down) { docker compose down -v }
elseif ($Logs) { docker compose logs -f --tail=200 }
elseif ($Build) { docker compose build }
else { Write-Host "Usage: dev.ps1 -Up|-Down|-Logs|-Build" }


