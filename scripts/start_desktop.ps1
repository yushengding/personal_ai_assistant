Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\apps\desktop-shell')

if (-not (Test-Path 'node_modules')) {
  npm install
}

npm run dev
