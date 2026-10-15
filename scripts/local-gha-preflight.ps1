param(
  [switch]$RunAct
)

$ErrorActionPreference = "Stop"

function Test-Cmd($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($null -eq $cmd) { return $null }
  return $cmd.Source
}

Write-Host "== Kodi Builder local GitHub Actions preflight ==" -ForegroundColor Cyan

$git = Test-Cmd "git"
$docker = Test-Cmd "docker"
$act = Test-Cmd "act"

$missing = @()
if (-not $git) { $missing += "git" }
if (-not $docker) { $missing += "docker" }
if (-not $act) { $missing += "act" }

Write-Host ""
Write-Host "Tool status:" -ForegroundColor Yellow
Write-Host ("  git:    " + ($(if ($git) { $git } else { "MISSING" })))
Write-Host ("  docker: " + ($(if ($docker) { $docker } else { "MISSING" })))
Write-Host ("  act:    " + ($(if ($act) { $act } else { "MISSING" })))

if ($missing.Count -gt 0) {
  $winget = Test-Cmd "winget"
  Write-Host ""
  Write-Host "Missing required tools: $($missing -join ', ')" -ForegroundColor Red
  if ($winget) {
    Write-Host "Recommended install options (PowerShell as Admin):" -ForegroundColor Yellow
    Write-Host "  winget install --id Git.Git -e"
    Write-Host "  winget install --id Docker.DockerDesktop -e"
    Write-Host "  winget install --id nektos.act -e"
  } else {
    Write-Host "winget not found. Install manually, then rerun this script:" -ForegroundColor Yellow
    Write-Host "  Git: https://git-scm.com/download/win"
    Write-Host "  Docker Desktop: https://www.docker.com/products/docker-desktop/"
    Write-Host "  act: https://github.com/nektos/act/releases"
  }
  Write-Host ""
  Write-Host "After install, restart terminal and run this script again."
  exit 1
}

Write-Host ""
Write-Host "Versions:" -ForegroundColor Yellow
& git --version
& docker --version
& act --version

Write-Host ""
Write-Host "Docker sanity check:" -ForegroundColor Yellow
try {
  & docker info *> $null
  Write-Host "  Docker daemon reachable: YES"
} catch {
  Write-Host "  Docker daemon reachable: NO" -ForegroundColor Red
  Write-Host "  Start Docker Desktop, wait until it is ready, then rerun."
  exit 1
}

Write-Host ""
Write-Host "Ready for local workflow test." -ForegroundColor Green
Write-Host "Suggested command:"
Write-Host "  act workflow_dispatch -W .github/workflows/build-kodi.yml -j build --container-architecture linux/amd64 --input branch=Piers --input abi=arm64-v8a --input app_name=Kodi --input package_id=org.xbmc.kodi --input apk_filename= --input unknown_sources=true --input create_release=false --input debug_mode=true"

if ($RunAct) {
  Write-Host ""
  Write-Host "Running act now..." -ForegroundColor Cyan
  & act workflow_dispatch `
    -W .github/workflows/build-kodi.yml `
    -j build `
    --container-architecture linux/amd64 `
    --input branch=Piers `
    --input abi=arm64-v8a `
    --input app_name=Kodi `
    --input package_id=org.xbmc.kodi `
    --input apk_filename= `
    --input unknown_sources=true `
    --input create_release=false `
    --input debug_mode=true
}
