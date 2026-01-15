# Script to compile the Linux executable
# Attempts to use WSL if available, or shows instructions

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BUILD LINUX EXECUTABLE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$linuxPath = $PSScriptRoot

# Check if WSL is available
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
    Write-Host "WSL detected. Attempting to build using WSL..." -ForegroundColor Green
    Write-Host ""
    
    # Convert Windows path to WSL path
    $wslPath = $linuxPath -replace 'C:', '/mnt/c' -replace '\\', '/'
    
    Write-Host "Running build in WSL..." -ForegroundColor Yellow
    Write-Host "WSL path: $wslPath" -ForegroundColor Gray
    Write-Host ""
    
    # Execute in WSL
    wsl bash -c "cd '$wslPath' && chmod +x build_editor_linux.sh && ./build_editor_linux.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "   BUILD COMPLETED" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "The executable is at:" -ForegroundColor Green
        Write-Host "  $linuxPath\dist\FantasyManager_Editor_v4_Linux" -ForegroundColor Yellow
        Write-Host "  $linuxPath\FantasyManager_Editor_v4_Linux" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host ""
        Write-Host "Error during WSL build." -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Yellow
        Write-Host ""
    }
}
else {
    Write-Host "WSL is not available." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To build the Linux executable, you need:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OPTION 1: Install WSL" -ForegroundColor Green
    Write-Host "  1. Run in PowerShell (as Administrator):" -ForegroundColor White
    Write-Host "     wsl --install" -ForegroundColor Gray
    Write-Host "  2. Restart your computer" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTION 2: Build on a Linux machine" -ForegroundColor Green
    Write-Host "  1. Copy the 'devkit/linux/' folder to a Linux machine" -ForegroundColor White
    Write-Host "  2. Open a terminal in that folder" -ForegroundColor White
    Write-Host "  3. Run:" -ForegroundColor White
    Write-Host "     chmod +x build_editor_linux.sh" -ForegroundColor Gray
    Write-Host "     ./build_editor_linux.sh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "OPTION 3: Use the Python script directly" -ForegroundColor Green
    Write-Host "  You don't need to build. You can run directly:" -ForegroundColor White
    Write-Host "  python3 fantasy_manager_editor_v4_linux.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For more information, see:" -ForegroundColor Cyan
    Write-Host "  linux/COMPILAR_EJECUTABLE.md" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Press Enter to exit..."
Read-Host
