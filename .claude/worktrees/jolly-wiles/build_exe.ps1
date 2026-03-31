# Build Jarvis.exe with PyInstaller.
# If you get "Access is denied" to dist\Jarvis.exe, close Jarvis completely first:
#   - Close the "Jarvis - Listening" window (X), or press F8, or tray icon -> Quit

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Remove old EXE so build can overwrite (fails silently if in use)
$distExe = "dist\Jarvis.exe"
if (Test-Path $distExe) {
    try {
        Remove-Item $distExe -Force -ErrorAction Stop
    } catch {
        Write-Host ""
        Write-Host "ERROR: Cannot delete $distExe - Jarvis is probably running." -ForegroundColor Red
        Write-Host "  Close Jarvis (window X, or F8, or tray icon -> Quit), then run this script again." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

pyinstaller --noconfirm Jarvis.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "Build done. Run: dist\Jarvis.exe" -ForegroundColor Green
