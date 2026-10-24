[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = 'Continue'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'

Write-Output "=== NDL ndlsearch opensearch ==="
try {
    $u = 'https://ndlsearch.ndl.go.jp/api/opensearch?title=%E8%A5%BF%E9%81%8A%E8%A8%98&cnt=40'
    $x = Invoke-RestMethod -Uri $u -TimeoutSec 40 -Headers @{ 'User-Agent' = $ua }
    $items = $x.rss.channel.item
    Write-Output ("items=" + @($items).Count)
    foreach ($it in $items) {
        Write-Output (" - " + $it.title + " | " + $it.link)
    }
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 200) { $m = $m.Substring(0, 200) }
    Write-Output ("NDL FAIL: " + $m)
}

Write-Output ""
Write-Output "=== NDL digital collections fulltext search ==="
try {
    $u2 = 'https://dl.ndl.go.jp/api/item/search?keyword=%E8%A5%BF%E9%81%8A%E8%A8%98&size=20'
    $r2 = Invoke-WebRequest -Uri $u2 -TimeoutSec 40 -UseBasicParsing -Headers @{ 'User-Agent' = $ua }
    Write-Output ("status=" + $r2.StatusCode + " len=" + $r2.Content.Length)
    Write-Output $r2.Content.Substring(0, [Math]::Min(1500, $r2.Content.Length))
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 200) { $m = $m.Substring(0, 200) }
    Write-Output ("NDL2 FAIL: " + $m)
}

Write-Output ""
Write-Output "=== harvard ids retry ==="
try {
    Start-Sleep -Seconds 3
    $rh = Invoke-WebRequest -Uri 'https://ids.lib.harvard.edu/' -TimeoutSec 25 -UseBasicParsing -Headers @{ 'User-Agent' = $ua }
    Write-Output ("harvard status=" + $rh.StatusCode)
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 150) { $m = $m.Substring(0, 150) }
    Write-Output ("harvard FAIL: " + $m)
}

Write-Output ""
Write-Output "=== cadal cardpage ==="
try {
    $rc = Invoke-WebRequest -Uri 'https://cadal.edu.cn/cardpage/bookCardPage?ssno=02000733' -TimeoutSec 30 -UseBasicParsing -Headers @{ 'User-Agent' = $ua }
    Write-Output ("cadal status=" + $rc.StatusCode + " len=" + $rc.Content.Length)
    if ($rc.Content -match '(?s)<title>(.*?)</title>') { Write-Output ("title=" + $Matches[1]) }
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 150) { $m = $m.Substring(0, 150) }
    Write-Output ("cadal FAIL: " + $m)
}
