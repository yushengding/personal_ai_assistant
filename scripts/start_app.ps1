Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

if (-not (Test-Path '.venv')) {
  py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Start-Process 'http://127.0.0.1:8000/ui'
uvicorn apps.gateway.main:app --host 127.0.0.1 --port 8000 --reload
