param(
    [int[]]$Ports = @(8082,8083,8084,8085,8086,8087)
)

$ErrorActionPreference = 'SilentlyContinue'
$procs = Get-NetTCPConnection -LocalPort $Ports | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($processId in $procs) {
    try { Stop-Process -Id $processId -Force } catch {}
}
Write-Host "Stopped services on ports: $($Ports -join ', ')"
