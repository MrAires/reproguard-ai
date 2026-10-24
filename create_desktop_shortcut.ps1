$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonW = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$Launcher = Join-Path $ProjectRoot "launcher_windows.py"
$Icon = Join-Path $ProjectRoot "assets\reproguard.ico"

if (-not (Test-Path $PythonW)) {
    throw "Python virtual environment was not found. Run setup_windows.bat first."
}
if (-not (Test-Path $Launcher)) {
    throw "launcher_windows.py was not found."
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ReproGuard AI.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonW
$Shortcut.Arguments = '"' + $Launcher + '"'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Open ReproGuard AI research reproducibility auditor"
if (Test-Path $Icon) {
    $Shortcut.IconLocation = $Icon + ",0"
}
$Shortcut.Save()

Write-Host "Desktop shortcut created:" $ShortcutPath
