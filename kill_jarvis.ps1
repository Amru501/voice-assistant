# Force-close Jarvis when the window or F8 doesn't work.
# Run: .\kill_jarvis.ps1

$name = "Jarvis"
$procs = Get-Process -Name $name -ErrorAction SilentlyContinue
if (-not $procs) {
    Write-Host "No process named '$name' is running." -ForegroundColor Yellow
    exit 0
}
foreach ($p in $procs) {
    Write-Host "Stopping $name (PID $($p.Id))..."
    Stop-Process -Id $p.Id -Force
}
Write-Host "Done. Jarvis has been closed." -ForegroundColor Green
