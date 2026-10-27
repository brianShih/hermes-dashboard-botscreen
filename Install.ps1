param([Parameter(ValueFromRemainingArguments=$true)][string[]]$InstallerArguments)
$ErrorActionPreference = 'Stop'
try {
    if ($null -eq $InstallerArguments) { $InstallerArguments = @() }
    $botScreenLauncher = $null
    $botScreenExplicitRoot = $null
    $botScreenExplicitPython = $null
    for ($botScreenIndex = 0; $botScreenIndex -lt $InstallerArguments.Count; $botScreenIndex++) {
        if ($InstallerArguments[$botScreenIndex] -eq '--hermes-root' -and $botScreenIndex + 1 -lt $InstallerArguments.Count) { $botScreenExplicitRoot = $InstallerArguments[$botScreenIndex + 1] }
        if ($InstallerArguments[$botScreenIndex] -eq '--python' -and $botScreenIndex + 1 -lt $InstallerArguments.Count) { $botScreenExplicitPython = $InstallerArguments[$botScreenIndex + 1] }
        if ($InstallerArguments[$botScreenIndex] -eq '--launcher' -and $botScreenIndex + 1 -lt $InstallerArguments.Count) { $botScreenLauncher = $InstallerArguments[$botScreenIndex + 1] }
    }
    if (-not $botScreenLauncher -and $botScreenExplicitRoot) {
        foreach ($botScreenRelative in @('.hermes/bin/hermes.exe','.venv/Scripts/hermes.exe')) {
            $botScreenCandidate = Join-Path $botScreenExplicitRoot $botScreenRelative
            if (Test-Path -LiteralPath $botScreenCandidate -PathType Leaf) { $botScreenLauncher = $botScreenCandidate; break }
        }
    }
    if (-not $botScreenLauncher -and -not $botScreenExplicitRoot) {
        $botScreenCommand = Get-Command hermes.exe,hermes.cmd,hermes -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($botScreenCommand) { $botScreenLauncher = $botScreenCommand.Source }
    }
    if (-not $botScreenLauncher -and -not $botScreenExplicitRoot) {
        $botScreenRoots = @($botScreenExplicitRoot)
        if ($env:HERMES_HOME) { $botScreenRoots += (Join-Path $env:HERMES_HOME 'hermes-agent') }
        if ($env:LOCALAPPDATA) { $botScreenRoots += (Join-Path $env:LOCALAPPDATA 'hermes/hermes-agent') }
        $botScreenRoots += (Join-Path $env:USERPROFILE '.hermes/hermes-agent')
        foreach ($botScreenRoot in $botScreenRoots) {
            if (-not $botScreenRoot) { continue }
            foreach ($botScreenRelative in @('.hermes/bin/hermes.exe','.venv/Scripts/hermes.exe')) {
                $botScreenCandidate = Join-Path $botScreenRoot $botScreenRelative
                if (Test-Path -LiteralPath $botScreenCandidate -PathType Leaf) { $botScreenLauncher = $botScreenCandidate; break }
            }
            if ($botScreenLauncher) { break }
        }
    }
    $botScreenPython = $botScreenExplicitPython
    if (-not $botScreenPython -and $botScreenLauncher) {
        $botScreenRuntime = & $botScreenLauncher --print-runtime-command
        if ($LASTEXITCODE -ne 0) { throw 'The selected Hermes launcher could not resolve its Python runtime.' }
        $botScreenCommandArray = ($botScreenRuntime -join "`n") | ConvertFrom-Json
        $botScreenPython = $botScreenCommandArray[0]
    }
    if (-not $botScreenPython -or -not (Test-Path -LiteralPath $botScreenPython -PathType Leaf)) {
        throw 'Hermes was not found. Install Hermes first, or pass --hermes-root and --python. See ONE_CLICK.md.'
    }
    $botScreenForwarded = @($InstallerArguments)
    if ($botScreenLauncher -and $InstallerArguments -notcontains '--launcher') { $botScreenForwarded += @('--launcher', $botScreenLauncher) }
    & $botScreenPython (Join-Path $PSScriptRoot 'scripts/install-dashboard.py') @botScreenForwarded
    exit $LASTEXITCODE
} catch {
    Write-Host ('INSTALLATION STOPPED: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
