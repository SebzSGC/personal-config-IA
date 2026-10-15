<#
.SYNOPSIS
  Trae los cambios del repo (git pull) y vuelve a enlazar por si hay plugins nuevos.
#>
$ErrorActionPreference = 'Stop'
Write-Host "Trayendo cambios de GitHub..." -ForegroundColor Cyan
git -C $PSScriptRoot pull --ff-only
if ($LASTEXITCODE -ne 0) {
  Write-Host "No se pudo hacer pull automatico (hay cambios locales sin subir o conflictos). Revisa con: git status" -ForegroundColor Red
  exit 1
}
& (Join-Path $PSScriptRoot 'instalar.ps1')
