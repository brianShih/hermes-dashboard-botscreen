$ErrorActionPreference = 'Stop'
$taskContainer = 'bot-screen-integration'
$taskInfo = (& docker inspect $taskContainer | ConvertFrom-Json)[0]
if ($LASTEXITCODE -ne 0 -or $taskInfo.Config.Labels.'com.sigensys.bot-screen' -ne 'integration') {
    throw 'Integration container ownership could not be verified.'
}
& docker stop $taskContainer
if ($LASTEXITCODE -ne 0) { throw 'Could not stop the integration container.' }
