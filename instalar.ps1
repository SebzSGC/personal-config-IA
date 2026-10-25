<#
.SYNOPSIS
  Conecta este repositorio con Claude Code y/o Google Antigravity en este equipo.

.DESCRIPTION
  Crea "uniones de carpeta" (junctions) desde las carpetas globales de cada herramienta hacia el repo:

    Para Antigravity:
      ~/.gemini/config/skills       -> skills/
      ~/.gemini/config/agents       -> agents/antigravity/
      ~/.gemini/config/plugins/<x>  -> plugins/<x>   (uno por plugin con plugin.json)
      ~/.gemini/config/plugins.json -> registra la carpeta plugins/

    Para Claude Code:
      ~/.claude/skills              -> skills/
      ~/.claude/agents              -> agents/claude/
      Registra este repo como marketplace local ("personal-config-ia") e instala sus plugins.

  Si ejecutas el script sin parámetros en modo interactivo (o mediante instalar.cmd),
  te preguntará si deseas instalar para Antigravity, Claude Code o Ambos.
  Tu elección se guarda en .instalacion.json (ignorado por git) para que 'sincronizar'
  la recuerde automáticamente sin volver a preguntar.

  Las uniones no requieren permisos de administrador. Después de un "git pull" los cambios ya están activos.

  Si en el equipo ya existen skills o agentes propios, se INCORPORAN al repo (nunca se sobrescribe nada del repo);
  lo que choca de nombre queda en una carpeta de respaldo "<carpeta>.respaldo-<fecha>".

.PARAMETER Objetivo
  Herramienta destino: 'Antigravity', 'Claude' o 'Ambos'.

.PARAMETER Antigravity
  Instala únicamente para Google Antigravity.

.PARAMETER Claude
  Instala únicamente para Claude Code.

.PARAMETER Ambos
  Instala para ambas herramientas (Google Antigravity y Claude Code).

.PARAMETER Simular
  Muestra lo que haría sin cambiar nada.

.PARAMETER Desinstalar
  Quita las uniones y deja en su lugar una COPIA de lo que hay en el repo (el equipo sigue funcionando sin el repo).

.PARAMETER NoInteractivo
  No realiza preguntas interactivas; usa el parámetro indicado, la configuración guardada o 'Ambos' por defecto.

.EXAMPLE
  .\instalar.cmd
  .\instalar.ps1 -Antigravity
  .\instalar.ps1 -Claude
  .\instalar.ps1 -Ambos
  .\instalar.ps1 -Simular
  .\instalar.ps1 -Desinstalar
#>
[CmdletBinding()]
param(
  [ValidateSet('Antigravity', 'Claude', 'Ambos', 'antigravity', 'claude', 'ambos', '')]
  [string]$Objetivo = '',
  [switch]$Antigravity,
  [switch]$Claude,
  [switch]$Ambos,
  [switch]$Simular,
  [switch]$Desinstalar,
  [switch]$NoInteractivo
)

$ErrorActionPreference = 'Stop'
$Repo  = $PSScriptRoot
$Casa  = $HOME
$Marca = Get-Date -Format 'yyyyMMdd-HHmmss'
$Resumen = New-Object System.Collections.Generic.List[string]
$ArchivoConfig = Join-Path $Repo '.instalacion.json'

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

function Actualizar-JsonConfig([string]$archivoJson, [string]$rutaAgregar) {
  $rutaNormalizada = $rutaAgregar.Replace('\', '/')
  $data = [ordered]@{ entries = @() }
  if (Test-Path -LiteralPath $archivoJson) {
    try {
      $existente = Get-Content -LiteralPath $archivoJson -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($existente.entries) { $data.entries = @($existente.entries) }
    } catch {}
  }
  $yaExiste = $false
  foreach ($e in $data.entries) {
    if ($e.path -and $e.path.Replace('\', '/').ToLowerInvariant() -eq $rutaNormalizada.ToLowerInvariant()) {
      $yaExiste = $true
      break
    }
  }
  if (-not $yaExiste) {
    $data.entries += [PSCustomObject]@{ path = $rutaNormalizada }
  }
  Hacer "registrar $rutaNormalizada en $(Split-Path $archivoJson -Leaf)" {
    $padre = Split-Path $archivoJson -Parent
    if (-not (Test-Path -LiteralPath $padre)) { New-Item -ItemType Directory -Path $padre -Force | Out-Null }
    $json = $data | ConvertTo-Json -Depth 5
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($archivoJson, $json, $utf8NoBom)
  }
  Escribir "   [+] $(Split-Path $archivoJson -Leaf) -> $rutaNormalizada" 'Green'
}

function Quitar-JsonConfig([string]$archivoJson, [string]$rutaQuitar) {
  if (-not (Test-Path -LiteralPath $archivoJson)) { return }
  $rutaNormalizada = $rutaQuitar.Replace('\', '/').ToLowerInvariant()
  try {
    $existente = Get-Content -LiteralPath $archivoJson -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($existente.entries) {
      $restantes = @($existente.entries | Where-Object { $_.path.Replace('\', '/').ToLowerInvariant() -ne $rutaNormalizada })
      Hacer "desregistrar $rutaNormalizada de $(Split-Path $archivoJson -Leaf)" {
        if ($restantes.Count -eq 0) {
          Remove-Item -LiteralPath $archivoJson -Force
        } else {
          $json = [ordered]@{ entries = $restantes } | ConvertTo-Json -Depth 5
          $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
          [System.IO.File]::WriteAllText($archivoJson, $json, $utf8NoBom)
        }
      }
    }
  } catch {}
}

function Claude-Plugins([bool]$instalar) {
  # Claude Code: este repo es un marketplace local (.claude-plugin/marketplace.json)
  $cli = Get-Command claude -ErrorAction SilentlyContinue
  if (-not $cli) {
    if ($instalar) {
      Escribir '   (Claude Code no esta en el PATH: agrega el marketplace a mano si lo instalas después, ver README)' 'DarkGray'
    }
    return
  }
  $mercado = Join-Path $Repo '.claude-plugin\marketplace.json'
  if (-not (Test-Path -LiteralPath $mercado)) { return }
  $datos = Get-Content -LiteralPath $mercado -Raw -Encoding UTF8 | ConvertFrom-Json
  $nombre = $datos.name
  $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try {
    if ($instalar) {
      Hacer "registrar marketplace $nombre en Claude Code" { & claude plugin marketplace add "$Repo" 2>&1 | Out-Null }
      foreach ($p in @($datos.plugins)) {
        Hacer "instalar $($p.name)@$nombre en Claude Code" { & claude plugin install "$($p.name)@$nombre" 2>&1 | Out-Null }
        Escribir "   [+] Claude Code: $($p.name)@$nombre" 'Green'
      }
    } else {
      foreach ($p in @($datos.plugins)) {
        Hacer "desinstalar $($p.name)@$nombre de Claude Code" { & claude plugin uninstall "$($p.name)@$nombre" 2>&1 | Out-Null }
      }
      Hacer "quitar marketplace $nombre de Claude Code" { & claude plugin marketplace remove $nombre 2>&1 | Out-Null }
      Escribir "   [-] Claude Code: plugins de $nombre desinstalados" 'Yellow'
    }
  } finally { $ErrorActionPreference = $prev }
}

function Guardar-Configuracion([string]$obj) {
  Hacer "guardar configuracion local en .instalacion.json" {
    $data = [ordered]@{
      objetivo    = $obj.ToLowerInvariant()
      actualizado = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
    }
    $json = $data | ConvertTo-Json -Depth 2
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ArchivoConfig, $json, $utf8NoBom)
  }
}

# ───────────────────────── Comprobaciones ─────────────────────────
if ($PSVersionTable.PSVersion.Major -ge 6 -and -not $IsWindows) {
  Escribir 'Este script es para Windows. En macOS o Linux usa ./instalar.sh' 'Red'; exit 1
}

# ───────────────────────── Resolver Objetivo ─────────────────────────
if ($Antigravity) { $Objetivo = 'Antigravity' }
elseif ($Claude)  { $Objetivo = 'Claude' }
elseif ($Ambos)   { $Objetivo = 'Ambos' }

$ConfigGuardada = $null
if (Test-Path -LiteralPath $ArchivoConfig) {
  try {
    $cfgJson = Get-Content -LiteralPath $ArchivoConfig -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($cfgJson.objetivo) { $ConfigGuardada = $cfgJson.objetivo.ToString().Trim().ToLowerInvariant() }
  } catch {}
}

if (-not $Objetivo) {
  $esInteractivo = (-not $NoInteractivo) -and (-not [Console]::IsInputRedirected) -and [Environment]::UserInteractive
  if ($esInteractivo -and -not $Desinstalar) {
    $defectoNum = 3
    if ($ConfigGuardada -eq 'antigravity') { $defectoNum = 1 }
    elseif ($ConfigGuardada -eq 'claude') { $defectoNum = 2 }

    Escribir "`n========================================================" 'Cyan'
    Escribir " ¿Para que herramientas deseas configurar este equipo?" 'Cyan'
    Escribir "========================================================" 'Cyan'
    Escribir "  [1] Antigravity" 'White'
    Escribir "  [2] Claude Code" 'White'
    Escribir "  [3] Ambos (Antigravity y Claude)" 'White'
    if ($ConfigGuardada) {
      $guardadoTexto = switch ($ConfigGuardada) {
        'antigravity' { 'Antigravity' }
        'claude'      { 'Claude Code' }
        default       { 'Ambos' }
      }
      Escribir "  (Configuracion actual en este equipo: $guardadoTexto)" 'DarkGray'
    }
    $resp = Read-Host "`nSelecciona una opcion [1-3] (por defecto: $defectoNum)"
    if ([string]::IsNullOrWhiteSpace($resp)) { $resp = "$defectoNum" }
    switch ($resp.Trim().ToLowerInvariant()) {
      '1'           { $Objetivo = 'Antigravity' }
      'antigravity' { $Objetivo = 'Antigravity' }
      '2'           { $Objetivo = 'Claude' }
      'claude'      { $Objetivo = 'Claude' }
      '3'           { $Objetivo = 'Ambos' }
      'ambos'       { $Objetivo = 'Ambos' }
      default {
        Escribir "Opcion '$resp' no reconocida, usando opcion por defecto [$defectoNum]." 'DarkYellow'
        switch ($defectoNum) {
          1 { $Objetivo = 'Antigravity' }
          2 { $Objetivo = 'Claude' }
          default { $Objetivo = 'Ambos' }
        }
      }
    }
  } else {
    if ($ConfigGuardada) {
      switch ($ConfigGuardada) {
        'antigravity' { $Objetivo = 'Antigravity' }
        'claude'      { $Objetivo = 'Claude' }
        default       { $Objetivo = 'Ambos' }
      }
    } else {
      $Objetivo = 'Ambos'
    }
  }
} else {
  switch ($Objetivo.ToLowerInvariant()) {
    'antigravity' { $Objetivo = 'Antigravity' }
    'claude'      { $Objetivo = 'Claude' }
    default       { $Objetivo = 'Ambos' }
  }
}

$HabilitarAntigravity = ($Objetivo -eq 'Antigravity' -or $Objetivo -eq 'Ambos')
$HabilitarClaude      = ($Objetivo -eq 'Claude'      -or $Objetivo -eq 'Ambos')

Escribir ''
Escribir "Repositorio: $Repo" 'Cyan'
Escribir "Objetivo:    $Objetivo" 'Green'
if ($Simular) { Escribir 'Modo simulacion: no se cambia nada.' 'DarkYellow' }

$CarpetasAntigravity = @(
  @{ Destino = Join-Path $Casa '.gemini\config\skills'; Origen = Join-Path $Repo 'skills' },
  @{ Destino = Join-Path $Casa '.gemini\config\agents'; Origen = Join-Path $Repo 'agents\antigravity' }
)
$CarpetasClaude = @(
  @{ Destino = Join-Path $Casa '.claude\skills'; Origen = Join-Path $Repo 'skills' },
  @{ Destino = Join-Path $Casa '.claude\agents'; Origen = Join-Path $Repo 'agents\claude' }
)
$CarpetaPluginsAntigravity = Join-Path $Casa '.gemini\config\plugins'
$RepoPlugins               = Join-Path $Repo 'plugins'
$PluginsAntigravity        = @(Get-ChildItem -LiteralPath $RepoPlugins -Directory -ErrorAction SilentlyContinue |
                               Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'plugin.json') })
$JsonPlugins               = Join-Path $Casa '.gemini\config\plugins.json'

# ───────────────────────── Desinstalar ─────────────────────────
if ($Desinstalar) {
  Escribir "`nQuitando enlaces (se deja una copia local de cada cosa):" 'Cyan'
  if ($HabilitarAntigravity) {
    Escribir "`nAntigravity:" 'Cyan'
    foreach ($c in $CarpetasAntigravity) { Desenlazar $c.Destino $c.Origen }
    foreach ($p in $PluginsAntigravity) { Desenlazar (Join-Path $CarpetaPluginsAntigravity $p.Name) $p.FullName }
    Quitar-JsonConfig $JsonPlugins $RepoPlugins
  }
  if ($HabilitarClaude) {
    Escribir "`nClaude Code:" 'Cyan'
    foreach ($c in $CarpetasClaude) { Desenlazar $c.Destino $c.Origen }
    Claude-Plugins $false
  }
  if (Test-Path -LiteralPath $ArchivoConfig) {
    Hacer "eliminar archivo de configuracion local" {
      Remove-Item -LiteralPath $ArchivoConfig -Force -ErrorAction SilentlyContinue
    }
  }
  Escribir "`nListo." 'Cyan'
  exit 0
}

# ───────────────────────── Instalar ─────────────────────────

# ── Antigravity ──
if ($HabilitarAntigravity) {
  Escribir "`nSkills y agentes de Antigravity:" 'Cyan'
  foreach ($c in $CarpetasAntigravity) { Enlazar $c.Destino $c.Origen $true }

  Escribir "`nPlugins de Antigravity:" 'Cyan'
  foreach ($p in $PluginsAntigravity) { Enlazar (Join-Path $CarpetaPluginsAntigravity $p.Name) $p.FullName $false }
  if ($PluginsAntigravity.Count -eq 0) {
    Escribir '   (no hay plugins en el repo)' 'DarkGray'
  } else {
    Actualizar-JsonConfig $JsonPlugins $RepoPlugins
  }
  # Ruta de antes de la reorganizacion (plugins\antigravity), ya no existe
  Quitar-JsonConfig $JsonPlugins (Join-Path $Repo 'plugins\antigravity')

  # Enlaces a plugins que ya no existen en el repo (se borraron o renombraron)
  foreach ($i in @(Get-ChildItem -LiteralPath $CarpetaPluginsAntigravity -Force -ErrorAction SilentlyContinue)) {
    $t = Destino-DeEnlace $i
    if ($t -and (Normalizar $t).StartsWith((Normalizar $RepoPlugins)) -and -not (Test-Path -LiteralPath $t)) {
      Hacer "quitar enlace huerfano $($i.Name)" { Quitar-Enlace $i.FullName }
      $Resumen.Add("Plugin quitado (ya no esta en el repo): $($i.Name)")
    }
  }
} else {
  # Si Antigravity NO fue seleccionado, retirar enlaces previos que apunten a este repo
  foreach ($c in $CarpetasAntigravity) {
    $item = Obtener-Item $c.Destino
    $t = Destino-DeEnlace $item
    if ($t -and (Normalizar $t) -eq (Normalizar $c.Origen)) {
      Hacer "quitar enlace de Antigravity $($c.Destino)" { Quitar-Enlace $c.Destino }
      $Resumen.Add("Enlace de Antigravity retirado (no seleccionado): $($c.Destino.Replace($Casa, '~'))")
    }
  }
  foreach ($p in $PluginsAntigravity) {
    $dest = Join-Path $CarpetaPluginsAntigravity $p.Name
    $item = Obtener-Item $dest
    $t = Destino-DeEnlace $item
    if ($t -and (Normalizar $t) -eq (Normalizar $p.FullName)) {
      Hacer "quitar enlace de plugin de Antigravity $dest" { Quitar-Enlace $dest }
    }
  }
  Quitar-JsonConfig $JsonPlugins $RepoPlugins
}

# ── Claude Code ──
if ($HabilitarClaude) {
  Escribir "`nSkills y agentes de Claude Code:" 'Cyan'
  foreach ($c in $CarpetasClaude) { Enlazar $c.Destino $c.Origen $true }

  Escribir "`nPlugins de Claude Code:" 'Cyan'
  Claude-Plugins $true
} else {
  # Si Claude NO fue seleccionado, retirar enlaces previos que apunten a este repo
  foreach ($c in $CarpetasClaude) {
    $item = Obtener-Item $c.Destino
    $t = Destino-DeEnlace $item
    if ($t -and (Normalizar $t) -eq (Normalizar $c.Origen)) {
      Hacer "quitar enlace de Claude Code $($c.Destino)" { Quitar-Enlace $c.Destino }
      $Resumen.Add("Enlace de Claude Code retirado (no seleccionado): $($c.Destino.Replace($Casa, '~'))")
    }
  }
  $dirClaude = Join-Path $Casa '.claude'
  if ((Test-Path -LiteralPath $dirClaude) -and -not (Get-ChildItem -LiteralPath $dirClaude -Force -ErrorAction SilentlyContinue)) {
    Hacer "eliminar carpeta vacia ~/.claude" { Remove-Item -LiteralPath $dirClaude -Force -ErrorAction SilentlyContinue }
  }
}

# Guardar configuracion seleccionada
Guardar-Configuracion $Objetivo

# ───────────────────────── Resumen ─────────────────────────
Escribir ''
if ($Resumen.Count) { Escribir 'Para revisar:' 'Yellow'; foreach ($r in $Resumen) { Escribir "   - $r" 'Yellow' } }
if ($Objetivo -eq 'Antigravity') {
  Escribir 'Listo. Reinicia Antigravity para que cargue los cambios.' 'Cyan'
} elseif ($Objetivo -eq 'Claude') {
  Escribir 'Listo. Reinicia Claude para que cargue los cambios.' 'Cyan'
} else {
  Escribir 'Listo. Reinicia Claude y Antigravity para que carguen los cambios.' 'Cyan'
}
Escribir 'Al agregar un plugin nuevo al repo, vuelve a ejecutar instalar (skills y agentes no lo necesitan).' 'DarkGray'
