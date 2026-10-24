[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = 'Continue'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

$repos = @('qinglee/xiyouji', 'gazhikaba/xiyouji_txt', 'wenku/xiyouji', 'kugeceo/xiyouji.luhui.net')

foreach ($r in $repos) {
    Write-Output "=== $r ==="
    foreach ($br in @('main', 'master')) {
        try {
            $u = "https://api.github.com/repos/$r/git/trees/$br`?recursive=1"
            $j = Invoke-RestMethod -Uri $u -TimeoutSec 30 -Headers @{ 'User-Agent' = $ua; 'Accept' = 'application/vnd.github+json' }
            $files = @($j.tree | Where-Object { $_.type -eq 'blob' })
            Write-Output ("branch=$br filecount=" + $files.Count)
            $files | Sort-Object -Property size -Descending | Select-Object -First 12 | ForEach-Object {
                Write-Output ("   {0,9}  {1}" -f $_.size, $_.path)
            }
            break
        } catch {
            $m = $_.Exception.Message
            if ($m.Length -gt 100) { $m = $m.Substring(0, 100) }
            Write-Output ("  branch=$br FAIL: $m")
        }
    }
    Write-Output ""
    Start-Sleep -Seconds 1
}
