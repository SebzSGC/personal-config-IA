<#
.SYNOPSIS
  Conecta este repositorio con Claude y Antigravity en este equipo.

.DESCRIPTION
  Crea "uniones de carpeta" (junctions) desde las carpetas globales de cada herramienta hacia el repo:

    ~/.claude/skills              -> skills/
    ~/.gemini/config/skills       -> skills/
    ~/.claude/agents              -> agents/claude/
    ~/.gemini/config/agents       -> agents/antigravity/
    ~/.gemini/config/plugins/<x>  -> plugins/antigravity/<x>   (uno por plugin)

  Las uniones no requieren permisos de administrador. Despues de un "git pull" los cambios ya estan activos.

  Si en el equipo ya existen skills o agentes propios, se INCORPORAN al repo (nunca se sobrescribe nada del repo);
  lo que choca de nombre queda en una carpeta de respaldo "<carpeta>.respaldo-<fecha>".

.PARAMETER Simular
  Muestra lo que haria sin cambiar nada.

.PARAMETER Desinstalar
  Quita las uniones y deja en su lugar una COPIA de lo que hay en el repo (el equipo sigue funcionando sin el repo).

.EXAMPLE
  .\instalar.ps1 -Simular
  .\instalar.ps1
  .\instalar.ps1 -Desinstalar
#>
[CmdletBinding()]
param(
  [switch]$Simular,
  [switch]$Desinstalar
)

$ErrorActionPreference = 'Stop'
$Repo  = $PSScriptRoot
$Casa  = $HOME
$Marca = Get-Date -Format 'yyyyMMdd-HHmmss'
$Resumen = New-Object System.Collections.Generic.List[string]

function Escribir([string]$texto, [string]$color = 'Gray') { Write-Host $texto -ForegroundColor $color }

function Hacer([string]$descripcion, [scriptblock]$accion) {
  if ($Simular) { Escribir "   (simulacion) $descripcion" 'DarkYellow'; return }
  & $accion
}

function Normalizar([string]$ruta) {
  if (-not $ruta) { return '' }
  $r = $ruta -replace '^\\\\\?\\', ''
  return ([System.IO.Path]::GetFullPath($r)).TrimEnd('\').ToLowerInvariant()
}

function Obtener-Item([string]$ruta) {
  return Get-Item -LiteralPath $ruta -Force -ErrorAction SilentlyContinue
}

function Destino-DeEnlace($item) {
  if ($null -eq $item -or -not $item.LinkType) { return $null }
  return @($item.Target)[0]
}

function Mover([string]$de, [string]$a) {
  # Move-Item no mueve carpetas entre discos distintos (C: -> D:): en ese caso copia y borra
  try { Move-Item -LiteralPath $de -Destination $a }
  catch { Copy-Item -LiteralPath $de -Destination $a -Recurse -Force; Remove-Item -LiteralPath $de -Recurse -Force }
}

function Quitar-Enlace([string]$ruta) {
  # Borra SOLO el enlace, nunca el contenido de la carpeta a la que apunta
  try { [System.IO.Directory]::Delete($ruta, $false) }
  catch {
    # Enlace "huerfano" (su destino ya no existe): Directory.Delete falla
    if ($env:OS -eq 'Windows_NT') { cmd /c rmdir "$ruta" | Out-Null } else { [System.IO.File]::Delete($ruta) }
  }
  if (Obtener-Item $ruta) { throw "No se pudo quitar el enlace $ruta" }
}

function Enlazar([string]$destino, [string]$origen, [bool]$absorber) {
  $nombre = $destino.Replace($Casa, '~')
  if (-not (Test-Path -LiteralPath $origen)) {
    Hacer "crear $origen" { New-Item -ItemType Directory -Path $origen -Force | Out-Null }
  }
  $item = Obtener-Item $destino
  if ($item) {
    $actual = Destino-DeEnlace $item
    if ($actual) {
      if ((Normalizar $actual) -eq (Normalizar $origen)) { Escribir "   [=] $nombre ya apunta al repo" 'DarkGray'; return }
      Hacer "quitar enlace viejo $nombre -> $actual" { Quitar-Enlace $destino }
    }
    elseif ($item.PSIsContainer) {
      if ($absorber) {
        foreach ($hijo in @(Get-ChildItem -LiteralPath $destino -Force)) {
          $enRepo = Join-Path $origen $hijo.Name
          if (Test-Path -LiteralPath $enRepo) {
            $Resumen.Add("Conflicto: '$($hijo.Name)' ya existe en el repo; la version local quedo en el respaldo de $nombre")
          } else {
            Hacer "incorporar al repo $nombre\$($hijo.Name)" { Mover $hijo.FullName $enRepo }
            $Resumen.Add("Incorporado al repo: $($hijo.Name) (desde $nombre) -> haz commit")
          }
        }
      }
      $quedan = @(Get-ChildItem -LiteralPath $destino -Force -ErrorAction SilentlyContinue)
      if ($quedan.Count -eq 0 -and -not $Simular) {
        Remove-Item -LiteralPath $destino -Force
      } else {
        $respaldo = "$destino.respaldo-$Marca"
        Hacer "respaldar $nombre -> $(Split-Path $respaldo -Leaf)" { Rename-Item -LiteralPath $destino -NewName (Split-Path $respaldo -Leaf) }
        $Resumen.Add("Respaldo creado: $($respaldo.Replace($Casa, '~'))")
      }
    }
    else {
      $respaldo = "$destino.respaldo-$Marca"
      Hacer "respaldar archivo $nombre" { Rename-Item -LiteralPath $destino -NewName (Split-Path $respaldo -Leaf) }
      $Resumen.Add("Respaldo creado: $($respaldo.Replace($Casa, '~'))")
    }
  }
  $padre = Split-Path $destino -Parent
  if (-not (Test-Path -LiteralPath $padre)) { Hacer "crear $padre" { New-Item -ItemType Directory -Path $padre -Force | Out-Null } }
  Hacer "unir $nombre -> repo" { New-Item -ItemType Junction -Path $destino -Target $origen | Out-Null }
  Escribir "   [+] $nombre -> $($origen.Replace($Repo, 'repo'))" 'Green'
}

function Desenlazar([string]$destino, [string]$origen) {
  $nombre = $destino.Replace($Casa, '~')
  $item = Obtener-Item $destino
  $actual = Destino-DeEnlace $item
  if (-not $actual -or (Normalizar $actual) -ne (Normalizar $origen)) { Escribir "   [=] $nombre no esta enlazado al repo" 'DarkGray'; return }
  Hacer "quitar enlace $nombre" { Quitar-Enlace $destino }
  Hacer "copiar contenido del repo a $nombre" { Copy-Item -LiteralPath $origen -Destination $destino -Recurse -Force }
  Escribir "   [-] $nombre ahora es una copia local (ya no sigue al repo)" 'Yellow'
}

# ───────────────────────── Comprobaciones ─────────────────────────
if ($PSVersionTable.PSVersion.Major -ge 6 -and -not $IsWindows) {
  Escribir 'Este script es para Windows. En macOS o Linux usa ./instalar.sh' 'Red'; exit 1
}
Escribir ''
Escribir "Repositorio: $Repo" 'Cyan'
if ($Simular) { Escribir 'Modo simulacion: no se cambia nada.' 'DarkYellow' }

$Carpetas = @(
  @{ Destino = Join-Path $Casa '.claude\skills';         Origen = Join-Path $Repo 'skills' },
  @{ Destino = Join-Path $Casa '.gemini\config\skills';  Origen = Join-Path $Repo 'skills' },
  @{ Destino = Join-Path $Casa '.claude\agents';         Origen = Join-Path $Repo 'agents\claude' },
  @{ Destino = Join-Path $Casa '.gemini\config\agents';  Origen = Join-Path $Repo 'agents\antigravity' }
)
$CarpetaPlugins = Join-Path $Casa '.gemini\config\plugins'
$RepoPlugins    = Join-Path $Repo 'plugins\antigravity'
$Plugins = @(Get-ChildItem -LiteralPath $RepoPlugins -Directory -ErrorAction SilentlyContinue)

# ───────────────────────── Desinstalar ─────────────────────────
if ($Desinstalar) {
  Escribir "`nQuitando enlaces (se deja una copia local de cada cosa):" 'Cyan'
  foreach ($c in $Carpetas) { Desenlazar $c.Destino $c.Origen }
  foreach ($p in $Plugins) { Desenlazar (Join-Path $CarpetaPlugins $p.Name) $p.FullName }
  Escribir "`nListo." 'Cyan'
  exit 0
}

# ───────────────────────── Instalar ─────────────────────────
Escribir "`nSkills y agentes:" 'Cyan'
foreach ($c in $Carpetas) { Enlazar $c.Destino $c.Origen $true }

Escribir "`nPlugins de Antigravity:" 'Cyan'
foreach ($p in $Plugins) { Enlazar (Join-Path $CarpetaPlugins $p.Name) $p.FullName $false }
if ($Plugins.Count -eq 0) { Escribir '   (no hay plugins en el repo)' 'DarkGray' }

# Enlaces a plugins que ya no existen en el repo (se borraron o renombraron)
foreach ($i in @(Get-ChildItem -LiteralPath $CarpetaPlugins -Force -ErrorAction SilentlyContinue)) {
  $t = Destino-DeEnlace $i
  if ($t -and (Normalizar $t).StartsWith((Normalizar $RepoPlugins)) -and -not (Test-Path -LiteralPath $t)) {
    Hacer "quitar enlace huerfano $($i.Name)" { Quitar-Enlace $i.FullName }
    $Resumen.Add("Plugin quitado (ya no esta en el repo): $($i.Name)")
  }
}

# ───────────────────────── Resumen ─────────────────────────
Escribir ''
if ($Resumen.Count) { Escribir 'Para revisar:' 'Yellow'; foreach ($r in $Resumen) { Escribir "   - $r" 'Yellow' } }
Escribir 'Listo. Reinicia Claude y Antigravity para que carguen los cambios.' 'Cyan'
Escribir 'Al agregar un plugin nuevo al repo, vuelve a ejecutar instalar (skills y agentes no lo necesitan).' 'DarkGray'
