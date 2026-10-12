[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = 'Continue'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'

Write-Output "=== NDL POST item/search ==="
try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes('{"keyword":"西遊記","size":20,"page":1}')
    Invoke-RestMethod -Method Post -Uri 'https://dl.ndl.go.jp/api/item/search' -Body $bytes -ContentType 'application/json' -TimeoutSec 40 -Headers @{ 'User-Agent' = $ua } | Out-Null
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 250) { $m = $m.Substring(0, 250) }
    Write-Output ("NDL POST FAIL: " + $m)
}

Write-Output ""
Write-Output "=== NDL html search ==="
try {
    $rh = Invoke-WebRequest -Uri 'https://dl.ndl.go.jp/search?cs=bib&keyword=%E8%A5%BF%E9%81%8A%E8%A8%98' -TimeoutSec 40 -UseBasicParsing -Headers @{ 'User-Agent' = $ua }
    Write-Output ("status=" + $rh.StatusCode + " len=" + $rh.Content.Length)
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 200) { $m = $m.Substring(0, 200) }
    Write-Output ("NDL html FAIL: " + $m)
}

Write-Output ""
Write-Output "=== github: pingdianben texts ==="
$queries = @{
    'xiyou-zhengdaoshu' = '%E8%A5%BF%E6%B8%B8%E8%AF%81%E9%81%93%E4%B9%A6'
    'lizhuowu'          = '%E6%9D%8E%E5%8D%93%E5%90%BE'
    'xinshuo-xiyouji'   = '%E6%96%B0%E8%AF%B4%E8%A5%BF%E6%B8%B8%E8%AE%B0'
    'xiyou-zhenquan'    = '%E8%A5%BF%E6%B8%B8%E7%9C%9F%E8%AF%A0'
    'xiyou-yuanzhi'     = '%E8%A5%BF%E6%B8%B8%E5%8E%9F%E6%97%A8'
    'piben-pingdian'    = '%E8%A5%BF%E6%B8%B8%E8%AE%B0%20%E8%AF%84%E7%82%B9'
}
foreach ($k in $queries.Keys) {
    $u = "https://api.github.com/search/repositories?q=$($queries[$k])&per_page=8"
    try {
        $j = Invoke-RestMethod -Uri $u -TimeoutSec 30 -Headers @{ 'User-Agent' = $ua; 'Accept' = 'application/vnd.github+json' }
        Write-Output ("[$k] total=" + $j.total_count)
        foreach ($it in $j.items) {
            $d = $it.description
            if ($d.Length -gt 60) { $d = $d.Substring(0, 60) }
            Write-Output ("   " + $it.full_name + "  stars=" + $it.stargazers_count + "  " + $d)
        }
    } catch {
        $m = $_.Exception.Message
        if ($m.Length -gt 120) { $m = $m.Substring(0, 120) }
        Write-Output ("[$k] FAIL: " + $m)
    }
    Start-Sleep -Seconds 2
}

Write-Output ""
Write-Output "=== github code search: pingdian ==="
try {
    $u2 = 'https://api.github.com/search/code?q=%E8%A5%BF%E6%B8%B8%E8%AE%B0+%E5%A4%B9%E6%89%B9&per_page=5'
    $j2 = Invoke-RestMethod -Uri $u2 -TimeoutSec 30 -Headers @{ 'User-Agent' = $ua; 'Accept' = 'application/vnd.github+json' }
    Write-Output ("code total=" + $j2.total_count)
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 200) { $m = $m.Substring(0, 200) }
    Write-Output ("code search FAIL: " + $m)
}
