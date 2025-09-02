param(
    [string]$XsdUrl = 'https://www.w3.org/2001/XMLSchema.xsd',
    [string]$CacheKey = 'Schema.xsd',
    [string]$ServiceHost = '127.0.0.1'
)

$ErrorActionPreference = 'Stop'

function Wait-Healthy($url) {
  for ($i=0; $i -lt 30; $i++) {
    try { $r = Invoke-WebRequest -UseBasicParsing $url; if ($r.StatusCode -eq 200) { return } } catch {}
    Start-Sleep -Seconds 1
  }
  throw "Service not healthy: $url"
}

Wait-Healthy "http://$ServiceHost:8082/health"
Wait-Healthy "http://$ServiceHost:8083/health"
Wait-Healthy "http://$ServiceHost:8084/health"
Wait-Healthy "http://$ServiceHost:8085/health"
Wait-Healthy "http://$ServiceHost:8086/health"
Wait-Healthy "http://$ServiceHost:8087/health"

$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{xsd_url=$XsdUrl; cache_key=$CacheKey} | ConvertTo-Json) "http://$ServiceHost:8082/fetch"
Write-Host "fetch:" $r.StatusCode ($r.Content.Substring(0,[Math]::Min(200,$r.Content.Length)))

$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{cache_key=$CacheKey; query='element name and type'; k=3} | ConvertTo-Json) "http://$ServiceHost:8083/query"
Write-Host "rag:" $r.StatusCode ($r.Content.Substring(0,[Math]::Min(200,$r.Content.Length)))

$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{prompt='Return XML <note><to>A</to><from>B</from><body>Hi</body></note>'} | ConvertTo-Json) "http://$ServiceHost:8084/fill"
Write-Host "llm:" $r.StatusCode

$xml = '<note xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><to>A</to><from>B</from><body>Hi</body></note>'
$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{xml_string=$xml; cache_key=$CacheKey} | ConvertTo-Json) "http://$ServiceHost:8085/validate"
Write-Host "validate:" $r.StatusCode $r.Content

# Test the new format selector service
$pipeData = "EntityName|Test Corp|Type:Company|Structure:LLC`nTransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00"
$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{pipe_data=$pipeData} | ConvertTo-Json) "http://$ServiceHost:8086/analyze"
Write-Host "format_selector:" $r.StatusCode ($r.Content.Substring(0,[Math]::Min(200,$r.Content.Length)))

# Test the orchestrator service
$r = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body (@{pipe_data=$pipeData; validate_output=$true; use_rag=$true} | ConvertTo-Json) "http://$ServiceHost:8087/pipeline"
Write-Host "orchestrator:" $r.StatusCode ($r.Content.Substring(0,[Math]::Min(200,$r.Content.Length)))
