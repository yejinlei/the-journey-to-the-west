[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = 'Continue'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

$owner = 'wenku'
$repo  = 'xiyouji'
$branch = 'master'
$out = 'f:\src\The-Journey-to-the-West\book\text\00-baiwen'

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Output "listing tree ..."
$treeUrl = "https://api.github.com/repos/$owner/$repo/git/trees/$branch`?recursive=1"
$j = Invoke-RestMethod -Uri $treeUrl -TimeoutSec 60 -Headers @{ 'User-Agent' = $ua; 'Accept' = 'application/vnd.github+json' }
$files = @($j.tree | Where-Object { $_.type -eq 'blob' })

$md = @($files | Where-Object { $_.path -like 'zh-tw/*.md' })
$extra = @($files | Where-Object { $_.path -match '^(README|LICENSE)' })

Write-Output ("md files = " + $md.Count + " ; extra = " + $extra.Count)

$ok = 0
$fail = 0

foreach ($f in ($md + $extra)) {
    $leaf = Split-Path $f.path -Leaf
    $dest = Join-Path $out $leaf
    $raw = "https://raw.githubusercontent.com/$owner/$repo/$branch/" + $f.path
    try {
        Invoke-WebRequest -Uri $raw -OutFile $dest -TimeoutSec 60 -Headers @{ 'User-Agent' = $ua }
        $ok++
    } catch {
        $fail++
        Write-Output ("FAIL " + $f.path)
    }
    Start-Sleep -Milliseconds 120
}

Write-Output ("done. ok=$ok fail=$fail out=$out")
