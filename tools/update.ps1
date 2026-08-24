<#
  FuturesPulse — install files handed over from chat, then commit and push.

  Lives in the repo so it arrives by `git pull` and never has to survive a
  browser download. Chrome blocks .bat and .ps1 downloads outright, which is
  why this file is created here rather than sent.

  Usage, from the repo root:
      .\tools\update.ps1            install newest matching files, commit, push
      .\tools\update.ps1 -Serve     serve the repo at http://localhost:8000
      .\tools\update.ps1 -Status    show what would be installed, change nothing
#>
param([switch]$Serve, [switch]$Status)

$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$dl   = Join-Path $env:USERPROFILE 'Downloads'

# Only these filenames are ever installed, and only to these paths. Anything
# else in Downloads is ignored — no guessing where a stray file belongs.
$map = @{
  'index.html'       = 'current\index.html'
  'zigzag.js'        = 'engine\zigzag.js'
  'ingest.py'        = 'pipeline\ingest.py'
  'requirements.txt' = 'pipeline\requirements.txt'
  'ingest.yml'       = '.github\workflows\ingest.yml'
}

function Find-Git {
  $g = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'GitHubDesktop') -Recurse -Filter git.exe -ErrorAction SilentlyContinue |
       Where-Object { $_.FullName -like '*\cmd\git.exe' } | Select-Object -First 1
  if ($g) { return $g.FullName }
  $c = Get-Command git.exe -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return $null
}

Write-Host ''
Write-Host '  FuturesPulse — update' -ForegroundColor White
Write-Host "  repo: $repo" -ForegroundColor DarkGray

if ($Serve) {
  Set-Location $repo
  Write-Host ''
  Write-Host '  http://localhost:8000/current/   (Ctrl+C to stop)' -ForegroundColor Cyan
  Write-Host ''
  python -m http.server 8000
  exit 0
}

# Chrome renames repeats to "index (1).html", so match on the stem and take the
# newest. Compare timestamps so an old download is never installed over new work.
$found = @()
foreach ($name in $map.Keys) {
  $stem = [IO.Path]::GetFileNameWithoutExtension($name)
  $ext  = [IO.Path]::GetExtension($name)
  $hit  = Get-ChildItem $dl -Filter "$stem*$ext" -ErrorAction SilentlyContinue |
          Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $hit) { continue }
  $dest = Join-Path $repo $map[$name]
  $cur  = Get-Item $dest -ErrorAction SilentlyContinue
  if ($cur -and $hit.LastWriteTime -le $cur.LastWriteTime) {
    Write-Host "  skip  $($hit.Name)  — repo copy is newer" -ForegroundColor DarkGray
    continue
  }
  $found += [pscustomobject]@{ Src = $hit; Dest = $dest; Rel = $map[$name] }
}

if ($found.Count -eq 0) {
  Write-Host ''
  Write-Host '  Nothing new to install.' -ForegroundColor Yellow
  Write-Host '  Download the file first, then run this again.' -ForegroundColor DarkGray
  Write-Host ''
  Read-Host '  Press Enter to close'; exit 0
}

Write-Host ''
foreach ($f in $found) {
  Write-Host ("  {0,-18} -> {1}   {2} bytes" -f $f.Src.Name, $f.Rel, $f.Src.Length) -ForegroundColor Green
}

if ($Status) { Write-Host ''; Write-Host '  -Status: nothing changed.' -ForegroundColor Yellow; exit 0 }

foreach ($f in $found) {
  New-Item -ItemType Directory -Force -Path (Split-Path $f.Dest) | Out-Null
  Copy-Item $f.Src.FullName $f.Dest -Force
}
Write-Host ''
Write-Host "  installed $($found.Count) file(s)" -ForegroundColor Green

$git = Find-Git
if (-not $git) {
  Write-Host '  git not found — files are installed; commit with GitHub Desktop.' -ForegroundColor Yellow
  Read-Host '  Press Enter to close'; exit 0
}

Set-Location $repo
& $git add -A | Out-Null
$staged = & $git diff --staged --name-only
if (-not $staged) {
  Write-Host '  no change vs the last commit' -ForegroundColor Yellow
} else {
  $msg = 'update: ' + (($found | ForEach-Object { $_.Rel }) -join ', ')
  & $git commit -m $msg | Out-Null
  Write-Host "  committed: $msg" -ForegroundColor Green
  & $git push 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
  if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '  PUSH FAILED — almost always credentials.' -ForegroundColor Yellow
    Write-Host '  The commit IS made. Open GitHub Desktop and click Push origin.' -ForegroundColor Yellow
  } else {
    Write-Host '  pushed.' -ForegroundColor Green
  }
}

Write-Host ''
Write-Host '  https://rassulshah.github.io/futurespulse/current/   (Ctrl+Shift+R)' -ForegroundColor Cyan
Write-Host ''
Read-Host '  Press Enter to close'
