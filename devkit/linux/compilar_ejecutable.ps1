# Script para compilar el ejecutable de Linux
# Intenta usar WSL si esta disponible, o muestra instrucciones

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   COMPILAR EJECUTABLE LINUX" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$linuxPath = $PSScriptRoot

# Verificar si WSL esta disponible
$wslAvailable = $false
try {
    $result = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $wslAvailable = $true
    }
}
catch {
    $wslAvailable = $false
}

if ($wslAvailable) {
    Write-Host "WSL detectado. Intentando compilar usando WSL..." -ForegroundColor Green
    Write-Host ""
    
    # Convertir ruta de Windows a ruta de WSL
    $wslPath = $linuxPath -replace 'C:', '/mnt/c' -replace '\\', '/'
    
    Write-Host "Ejecutando compilacion en WSL..." -ForegroundColor Yellow
    Write-Host "Ruta en WSL: $wslPath" -ForegroundColor Gray
    Write-Host ""
    
    # Ejecutar en WSL
    wsl bash -c "cd '$wslPath' && chmod +x build_editor_linux.sh && ./build_editor_linux.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "   COMPILACION COMPLETADA" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "El ejecutable esta en:" -ForegroundColor Green
        Write-Host "  $linuxPath\dist\FantasyManager_Editor_v4_Linux" -ForegroundColor Yellow
        Write-Host "  $linuxPath\FantasyManager_Editor_v4_Linux" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host ""
        Write-Host "Error durante la compilacion en WSL." -ForegroundColor Red
        Write-Host "Revisa los mensajes de error arriba." -ForegroundColor Yellow
        Write-Host ""
    }
}
else {
    Write-Host "WSL no esta disponible." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para compilar el ejecutable de Linux, necesitas:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OPCION 1: Instalar WSL" -ForegroundColor Green
    Write-Host "  1. Ejecuta en PowerShell (como Administrador):" -ForegroundColor White
    Write-Host "     wsl --install" -ForegroundColor Gray
    Write-Host "  2. Reinicia tu computadora" -ForegroundColor White
    Write-Host "  3. Ejecuta este script nuevamente" -ForegroundColor White
    Write-Host ""
    Write-Host "OPCION 2: Compilar en una maquina Linux" -ForegroundColor Green
    Write-Host "  1. Copia la carpeta 'devkit/linux/' a una maquina Linux" -ForegroundColor White
    Write-Host "  2. Abre una terminal en esa carpeta" -ForegroundColor White
    Write-Host "  3. Ejecuta:" -ForegroundColor White
    Write-Host "     chmod +x build_editor_linux.sh" -ForegroundColor Gray
    Write-Host "     ./build_editor_linux.sh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "OPCION 3: Usar el script Python directamente" -ForegroundColor Green
    Write-Host "  No necesitas compilar. Puedes ejecutar directamente:" -ForegroundColor White
    Write-Host "  python3 fantasy_manager_editor_v4_linux.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Para mas informacion, consulta:" -ForegroundColor Cyan
    Write-Host "  linux/COMPILAR_EJECUTABLE.md" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Presiona Enter para salir..."
Read-Host



