# CiteLibre demo launcher for Windows: starts the shared platform and one CiteLibre
# application with Docker Compose, waits until the application answers, then opens the
# portal. Run it through citelibre.cmd. Same commands and options as citelibre.sh (keep
# both in sync). Compatible with Windows PowerShell 5.1: keep this file ASCII only.
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot

$Apps = @('rendezvous', 'serviceez', 'participez')
# Platform services started with --lite (no Elasticsearch, Kibana, Solr, Matomo, Adminer)
$LiteServices = @('mariadb', 'init-keycloak-db', 'keycloak', 'httpd', 'mailpit')
$BaseUrl = 'http://localhost'
$Timeout = 600
if ($env:CITELIBRE_TIMEOUT) { $Timeout = [int]$env:CITELIBRE_TIMEOUT }

function Show-Usage {
    @"
Usage: citelibre.cmd [command] [application] [options]

Commands:
  start [app]   start the platform and the application (default command)
  stop          stop every CiteLibre container, data is kept
  reset         remove every CiteLibre container, data is lost
  status        list the CiteLibre containers
  logs [app]    follow the application logs (application.log, error.log)

Applications: $($Apps -join ', ') (default: rendezvous)

Options (start):
  --lite             start a light platform: no Elasticsearch, Kibana, Solr, Matomo, Adminer
  --version <x.y.z>  image version to run (default: CITELIBRE_IMAGE_VERSION of the app .env)
  --no-browser       do not open the browser
"@
}

function Write-Info([string]$Message) { Write-Host '==> ' -ForegroundColor Blue -NoNewline; Write-Host $Message }

function Stop-WithError([string]$Message) {
    Write-Host 'Error: ' -ForegroundColor Red -NoNewline
    Write-Host $Message
    exit 1
}

function Invoke-ComposePlatform { docker compose -f citelibre-platform/docker-compose.yml @args }
function Invoke-ComposeApp([string]$App) { docker compose -f "citelibre-$App/docker-compose.yml" @args }

function Assert-App([string]$App) {
    if ($Apps -notcontains $App) { Stop-WithError "unknown application '$App' (expected: $($Apps -join ', '))" }
}

function Test-ContainerRunning([string]$Name) {
    return [bool](docker ps -q --filter "name=^$Name`$")
}

function Assert-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Stop-WithError 'Docker is not installed, see https://docs.docker.com/get-docker/'
    }
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-WithError 'Docker is not running: start Docker Desktop and retry.' }
    docker compose version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-WithError 'Docker Compose v2 is required (docker compose).' }
}

# Port 80 must be free, unless our own httpd already holds it
function Assert-Port {
    if (Test-ContainerRunning 'citelibre-httpd') { return }
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $busy = $client.ConnectAsync('127.0.0.1', 80).Wait(1000)
    } catch {
        $busy = $false
    } finally {
        $client.Close()
    }
    if ($busy) {
        $owner = docker ps --filter publish=80 --format '{{.Names}}'
        if ($owner) { Stop-WithError "port 80 is already used by the container $($owner): stop it and retry." }
        Stop-WithError 'port 80 is already used (IIS, Skype, another web server...): stop it and retry.'
    }
}

# Uses the local image when present (built in the packaging repository), else pulls it
function Assert-Image([string]$App, [string]$Version) {
    $image = "citelibre/packaging-$($App):$Version"
    docker image inspect $image 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Info "Using local image $image"; return }
    Write-Info "Pulling $image"
    docker pull $image
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "image $image is neither local nor on Docker Hub.`nBuild it in the packaging repository: mvn clean package -Passembly,$App,docker"
    }
}

# HTTP status code without following redirects, 0 when there is no answer
function Get-HttpCode([string]$Url) {
    $request = [System.Net.HttpWebRequest]::Create($Url)
    $request.AllowAutoRedirect = $false
    $request.Timeout = 5000
    try {
        $response = $request.GetResponse()
        $code = [int]$response.StatusCode
        $response.Close()
        return $code
    } catch [System.Net.WebException] {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return 0
    } catch {
        return 0
    }
}

# Waits until the URL answers 2xx/3xx; fails early when the given container stopped
function Wait-Url([string]$Url, [string]$Container) {
    $waited = 0
    Write-Host "    waiting for $Url " -NoNewline
    while ($true) {
        $code = Get-HttpCode $Url
        if ($code -ge 200 -and $code -lt 400) { Write-Host ' ok'; return }
        if (-not (Test-ContainerRunning $Container)) {
            Write-Host ''
            docker logs --tail 30 $Container
            Stop-WithError "container $Container stopped, see the logs above."
        }
        if ($waited -ge $Timeout) {
            Write-Host ''
            Stop-WithError "no answer after $($Timeout)s, check: citelibre.cmd logs"
        }
        Write-Host '.' -NoNewline
        Start-Sleep -Seconds 5
        $waited += 5
    }
}

function Start-CiteLibre([string[]]$Arguments) {
    $app = 'rendezvous'
    $lite = $false
    $version = ''
    $browser = $true
    for ($i = 0; $i -lt $Arguments.Count; $i++) {
        switch -CaseSensitive ($Arguments[$i]) {
            '--lite' { $lite = $true }
            '--version' {
                if ($i + 1 -ge $Arguments.Count) { Stop-WithError '--version needs a value' }
                $i++
                $version = $Arguments[$i]
            }
            '--no-browser' { $browser = $false }
            default {
                if ($Arguments[$i].StartsWith('-')) { Show-Usage; exit 1 }
                Assert-App $Arguments[$i]
                $app = $Arguments[$i]
            }
        }
    }
    if (-not $version) {
        $line = Select-String -Path "citelibre-$app/.env" -Pattern '^CITELIBRE_IMAGE_VERSION=' | Select-Object -First 1
        if ($line) { $version = $line.Line.Split('=', 2)[1].Trim() }
    }
    $env:CITELIBRE_IMAGE_VERSION = $version

    Assert-Docker
    Assert-Port
    Assert-Image $app $version

    if ($lite) {
        Write-Info 'Starting the light platform (MariaDB, Keycloak, httpd, Mailpit)'
        Invoke-ComposePlatform up -d @LiteServices
    } else {
        Write-Info 'Starting the platform (MariaDB, Keycloak, Elasticsearch, Kibana, Solr, Matomo, httpd, Mailpit)'
        Invoke-ComposePlatform up -d
    }
    if ($LASTEXITCODE -ne 0) { Stop-WithError 'the platform did not start, see the messages above.' }
    Wait-Url "$BaseUrl/keycloak/realms/citelibre_backoffice" 'citelibre-keycloak'

    Write-Info "Starting CiteLibre $app $version (the first start takes a few minutes)"
    Invoke-ComposeApp $app up -d
    if ($LASTEXITCODE -ne 0) { Stop-WithError "CiteLibre $app did not start, see the messages above." }
    Wait-Url "$BaseUrl/citelibre-$app/jsp/site/Portal.jsp" "citelibre-$app"

    @"

CiteLibre $app is ready:
  Portal        $BaseUrl/
  Front office  $BaseUrl/citelibre-$app/jsp/site/Portal.jsp   test@citelibre.org / coucou
  Back office   $BaseUrl/citelibre-$app/jsp/admin/AdminMenu.jsp   admin@citelibre.org / coucou
  Mails sent    $BaseUrl/mailpit/

Stop with citelibre.cmd stop (data is kept), start from scratch with citelibre.cmd reset
"@
    if ($browser) { Start-Process "$BaseUrl/" }
}

function Stop-CiteLibre {
    Assert-Docker
    foreach ($app in $Apps) { Invoke-ComposeApp $app stop }
    Invoke-ComposePlatform stop
}

function Reset-CiteLibre {
    Assert-Docker
    $answer = Read-Host 'Every CiteLibre container and its data will be removed. Continue? [y/N]'
    if ($answer -notmatch '^[yYoO]') { exit 0 }
    # Applications first: they use the network created by the platform
    foreach ($app in $Apps) { Invoke-ComposeApp $app down --volumes --remove-orphans }
    Invoke-ComposePlatform down --volumes --remove-orphans
}

function Show-Status {
    Assert-Docker
    docker ps -a --filter name=citelibre- --format 'table {{.Names}}\t{{.Status}}'
}

function Show-Logs([string]$App) {
    if (-not $App) { $App = 'rendezvous' }
    Assert-App $App
    Assert-Docker
    if (-not (Test-ContainerRunning "citelibre-$App")) { Stop-WithError "citelibre-$App is not running." }
    # Lutece writes its logs in WEB-INF/logs, not on the container output
    docker exec "citelibre-$App" sh -c "cd /opt/applications/apache-tomcat/webapps/citelibre-$App/WEB-INF/logs && tail -n 50 -F application.log error.log"
}

$command = 'start'
$rest = @()
if ($args.Count -gt 0) {
    $command = $args[0]
    if ($args.Count -gt 1) { $rest = $args[1..($args.Count - 1)] }
}
switch -CaseSensitive ($command) {
    'start' { Start-CiteLibre $rest }
    'stop' { Stop-CiteLibre }
    'reset' { Reset-CiteLibre }
    'status' { Show-Status }
    'logs' { Show-Logs ($rest | Select-Object -First 1) }
    { $_ -in '-h', '--help', 'help' } { Show-Usage }
    # citelibre.cmd rendezvous --lite: start is implied
    default { Start-CiteLibre (@($command) + $rest) }
}
