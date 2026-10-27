$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskContainer = 'bot-screen-integration'
$taskImage = 'bot-screen-integration-runtime:local'

function Invoke-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($args[0])" }
}

$taskImageId = & docker image ls -q $taskImage
if (-not $taskImageId) {
    throw 'Missing local runtime image. Run python scripts/prepare-runtime.py first; see INTEGRATION.md.'
}
if (-not (Test-Path "$taskRoot\bot-screen-plugin\dashboard\dist\index.js")) {
    throw 'Build the plugin first: cd bot-screen-plugin; npm.cmd ci; npm.cmd run build'
}
if (-not (Test-Path "$taskRoot\hermes\hermes_cli\web_dist\index.html")) {
    throw 'Build the Hermes Webapp first; see INTEGRATION.md.'
}

$taskExists = & docker ps -a --filter "name=^/$taskContainer`$" --format '{{.Names}}'
if ($taskExists -eq $taskContainer) {
    $taskInspection = & docker inspect $taskContainer
    $taskInfo = ($taskInspection | ConvertFrom-Json)[0]
    if ($taskInfo.Config.Labels.'com.sigensys.bot-screen' -ne 'integration') {
        throw 'Existing container does not have the integration ownership label.'
    }
    foreach ($taskMount in $taskInfo.Mounts) {
        $taskExpected = switch ($taskMount.Destination) {
            '/opt/hermes' { Join-Path $taskRoot 'hermes' }
            '/plugin' { Join-Path $taskRoot 'bot-screen-plugin' }
            '/integration' { Join-Path $taskRoot 'scripts' }
            default { throw 'Unexpected integration mount.' }
        }
        if ($taskMount.RW -or $taskMount.Source.Replace('\','/').ToLower() -ne $taskExpected.Replace('\','/').ToLower()) {
            throw 'Existing container mount does not match this workspace.'
        }
    }
    if (-not $taskInfo.State.Running) { Invoke-Docker start $taskContainer | Out-Null }
} else {
    Invoke-Docker run -d --init --name $taskContainer --label com.sigensys.bot-screen=integration `
        --publish 127.0.0.1:9124:9124 --shm-size 512m `
        --mount "type=bind,source=$taskRoot\hermes,target=/opt/hermes,readonly" `
        --mount "type=bind,source=$taskRoot\bot-screen-plugin,target=/plugin,readonly" `
        --mount "type=bind,source=$taskRoot\scripts,target=/integration,readonly" `
        $taskImage sleep infinity | Out-Null
}

$taskReady = $false
try { $taskReady = (Invoke-WebRequest http://127.0.0.1:9124/login -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch {}
if (-not $taskReady) {
    $taskEnv = @('--workdir','/opt/hermes','--env','PYTHONPATH=/opt/hermes',
                 '--env','HERMES_HOME=/lab/profiles/bot-screen-lab',
                 '--env','HERMES_RUNTIME_DIR=/tmp/hermes-runtime','--env','HOME=/lab/user')
    Invoke-Docker exec @taskEnv $taskContainer /opt/hermes-venv/bin/python /integration/bootstrap.py
    Invoke-Docker exec -d @taskEnv $taskContainer /opt/hermes-venv/bin/python /integration/server.py
    for ($taskAttempt = 0; $taskAttempt -lt 60; $taskAttempt++) {
        try {
            if ((Invoke-WebRequest http://127.0.0.1:9124/login -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) {
                $taskReady = $true
                break
            }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
}
if (-not $taskReady) { throw 'Dashboard did not become ready. Inspect /lab/dashboard.log inside this container.' }
Write-Output 'Ready: http://127.0.0.1:9124/bot-screen'
Write-Output 'Open authenticated dedicated Chrome: node scripts/open-browser.mjs'
