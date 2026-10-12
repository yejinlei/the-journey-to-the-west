[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = 'Continue'

$sites = @(
    'https://dl.ndl.go.jp/',
    'https://digital.archives.go.jp/',
    'https://ids.lib.harvard.edu/',
    'https://cadal.edu.cn/',
    'https://read.nlc.cn/',
    'https://www.gutenberg.org/',
    'https://api.github.com/',
    'https://zh.wikisource.org/',
    'https://archive.org/'
)

Write-Output "=== reachability ==="
foreach ($s in $sites) {
    try {
        $r = Invoke-WebRequest -Uri $s -TimeoutSec 12 -UseBasicParsing -MaximumRedirection 3
        Write-Output ("OK   {0}  status={1}" -f $s, $r.StatusCode)
    } catch {
        $m = $_.Exception.Message
        if ($m.Length -gt 70) { $m = $m.Substring(0, 70) }
        Write-Output ("FAIL {0}  {1}" -f $s, $m)
    }
}

Write-Output ""
Write-Output "=== NDL search: title=xiyouji ==="
try {
    $q = '%22%E8%A5%BF%E9%81%8A%E8%A8%98%22'
    $u = "https://dl.ndl.go.jp/api/sru?operation=searchRetrieve&maximumRecords=60&query=title%3D$q"
    $x = Invoke-RestMethod -Uri $u -TimeoutSec 40
    $n = ($x | Select-Xml -XPath '//*[local-name()="numberOfRecords"]') | Select-Object -First 1
    Write-Output ("numberOfRecords=" + $n.Node.InnerText)
    ($x | Select-Xml -XPath '//*[local-name()="title"]') | ForEach-Object {
        Write-Output (" - " + $_.Node.InnerText)
    }
} catch {
    $m = $_.Exception.Message
    if ($m.Length -gt 200) { $m = $m.Substring(0, 200) }
    Write-Output ("NDL FAIL: " + $m)
}
