param(
  [string]$Project = 'personal_ai_assistant',
  [string]$Batch = $(Get-Date -Format 'yyyy-MM'),
  [string]$ArchiveTimestamp = $(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'),
  [switch]$CleanExisting
)

$root = Split-Path -Parent $PSScriptRoot
$archiveBase = Join-Path $root "archive\$Project\$Batch"
$types = @('analysis','architecture','planning','implementation','operations')
foreach ($t in $types) {
  New-Item -ItemType Directory -Force -Path (Join-Path $archiveBase $t) | Out-Null
}

if ($CleanExisting) {
  foreach ($t in $types) {
    Get-ChildItem -Path (Join-Path $archiveBase $t) -Filter *.md -File -ErrorAction SilentlyContinue | Remove-Item -Force
  }
}

$map = @{
  'design_benchmark_openclaw_airi.md' = 'analysis'
  'ai_assistant_fusion_research_and_design.md' = 'analysis'
  'ai_assistant_architecture_v1.md' = 'architecture'
  'execution_control_plane_spec_v1.md' = 'architecture'
  'DATABASE_AND_DISTRIBUTION_STRATEGY.md' = 'architecture'
  'ROADMAP.md' = 'planning'
  'DEVELOPMENT_STATUS_AND_ROADMAP.md' = 'planning'
  'README.md' = 'implementation'
}

$files = Get-ChildItem -Path $root -Filter *.md -File | Where-Object { $_.Name -notin @('ARCHIVE_INDEX.md','ARCHIVING_RULES.md') }
foreach ($f in $files) {
  $type = if ($map.ContainsKey($f.Name)) { $map[$f.Name] } else { 'operations' }
  $targetName = "$ArchiveTimestamp`__${type}__" + $f.Name.ToLower()
  $target = Join-Path (Join-Path $archiveBase $type) $targetName
  Copy-Item $f.FullName $target -Force
}

$manifestPath = Join-Path $archiveBase 'manifest.json'
$archived = Get-ChildItem -Path $archiveBase -Recurse -Filter *.md -File
$items = foreach ($f in $archived) {
  $rel = $f.FullName.Substring($archiveBase.Length + 1)
  $rel = $rel -replace '\\','/'
  $type = $rel.Split('/')[0]
  [pscustomobject]@{
    project = $Project
    batch = $Batch
    archived_at = $ArchiveTimestamp
    type = $type
    title = $f.BaseName
    relative_path = $rel
    sha256 = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLower()
  }
}
$items | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifestPath
Write-Host "Archived" $items.Count "files to" $archiveBase "at" $ArchiveTimestamp
