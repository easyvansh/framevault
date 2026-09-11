$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Create .venv and install backend/requirements-dev.txt first." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js is required." }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg is required for video processing. Restart PowerShell after installing it." }
if (-not (Test-Path (Join-Path $ProjectRoot "frontend\node_modules"))) { throw "Run npm install in frontend first." }
$Backend = Start-Process -FilePath $Python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001", "--app-dir", "backend" -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden
try { Set-Location (Join-Path $ProjectRoot "frontend"); npm.cmd run dev } finally { Stop-Process -Id $Backend.Id -ErrorAction SilentlyContinue }
