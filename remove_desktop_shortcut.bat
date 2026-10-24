@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Join-Path ([Environment]::GetFolderPath('Desktop')) 'ReproGuard AI.lnk'; if(Test-Path $p){Remove-Item $p -Force; Write-Host 'Shortcut removed.'} else {Write-Host 'Shortcut not found.'}"
pause
