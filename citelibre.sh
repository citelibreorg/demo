#!/usr/bin/env bash
# CiteLibre demo launcher: starts the shared platform and one CiteLibre application with
# Docker Compose, waits until the application answers, then opens the portal.
# Windows counterpart: citelibre.cmd / citelibre.ps1 (keep both in sync).
set -euo pipefail
cd "$(dirname "$0")"

APPS="rendezvous serviceez participez"
# Platform services started with --lite (no Elasticsearch, Kibana, Solr, Matomo, Adminer)
LITE_SERVICES="mariadb init-keycloak-db keycloak httpd mailpit"
BASE_URL="http://localhost"
TIMEOUT=${CITELIBRE_TIMEOUT:-600}

usage() {
  cat <<EOF
Usage: ./citelibre.sh [command] [application] [options]

Commands:
  start [app]   start the platform and the application (default command)
  stop          stop every CiteLibre container, data is kept
  reset         remove every CiteLibre container, data is lost
  status        list the CiteLibre containers
  logs [app]    follow the application logs (application.log, error.log)

Applications: ${APPS// /, } (default: rendezvous)

Options (start):
  --lite             start a light platform: no Elasticsearch, Kibana, Solr, Matomo, Adminer
  --version <x.y.z>  image version to run (default: CITELIBRE_IMAGE_VERSION of the app .env)
  --no-browser       do not open the browser
EOF
}

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

compose_platform() { docker compose -f citelibre-platform/docker-compose.yml "$@"; }
compose_app() { local app=$1; shift; docker compose -f "citelibre-$app/docker-compose.yml" "$@"; }

check_app() {
  [[ " $APPS " == *" $1 "* ]] || fail "unknown application '$1' (expected: ${APPS// /, })"
}

check_docker() {
  command -v docker >/dev/null || fail "Docker is not installed, see https://docs.docker.com/get-docker/"
  docker info >/dev/null 2>&1 || fail "Docker is not running: start Docker Desktop (or the Docker service) and retry."
  docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required (docker compose)."
}

# Port 80 must be free, unless our own httpd already holds it
check_port() {
  [ -n "$(docker ps -q --filter name=^citelibre-httpd$)" ] && return
  if (exec 3<>/dev/tcp/127.0.0.1/80) 2>/dev/null; then
    local owner
    owner=$(docker ps --filter publish=80 --format '{{.Names}}')
    fail "port 80 is already used${owner:+ by the container $owner}: stop it and retry."
  fi
}

# Uses the local image when present (built in the packaging repository), else pulls it
check_image() {
  local image="citelibre/packaging-$1:$2"
  docker image inspect "$image" >/dev/null 2>&1 && { info "Using local image $image"; return; }
  info "Pulling $image"
  docker pull "$image" || fail "image $image is neither local nor on Docker Hub.
Build it in the packaging repository: mvn clean package -Passembly,$1,docker"
}

http_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$1" || true; }

# Waits until the URL answers 2xx/3xx; fails early when the given container stopped
wait_url() {
  local url=$1 container=$2 waited=0 code
  printf '    waiting for %s ' "$url"
  while :; do
    code=$(http_code "$url")
    [[ $code == [23]* ]] && { echo " ok"; return; }
    if [ -z "$(docker ps -q --filter "name=^$container$")" ]; then
      echo
      docker logs --tail 30 "$container" 2>&1 || true
      fail "container $container stopped, see the logs above."
    fi
    ((waited >= TIMEOUT)) && { echo; fail "no answer after ${TIMEOUT}s, check: ./citelibre.sh logs"; }
    printf '.'
    sleep 5
    waited=$((waited + 5))
  done
}

open_browser() {
  if command -v xdg-open >/dev/null; then xdg-open "$1" >/dev/null 2>&1 &
  elif command -v open >/dev/null; then open "$1"
  fi
}

start() {
  local app=rendezvous lite=false version="" browser=true
  while [ $# -gt 0 ]; do
    case $1 in
      --lite) lite=true ;;
      --version) [ $# -ge 2 ] || fail "--version needs a value"; version=$2; shift ;;
      --no-browser) browser=false ;;
      -*) usage; exit 1 ;;
      *) check_app "$1"; app=$1 ;;
    esac
    shift
  done
  [ -n "$version" ] || version=$(sed -n 's/^CITELIBRE_IMAGE_VERSION=//p' "citelibre-$app/.env")
  export CITELIBRE_IMAGE_VERSION=$version

  check_docker
  check_port
  check_image "$app" "$version"

  if $lite; then
    info "Starting the light platform (MariaDB, Keycloak, httpd, Mailpit)"
    # shellcheck disable=SC2086
    compose_platform up -d $LITE_SERVICES
  else
    info "Starting the platform (MariaDB, Keycloak, Elasticsearch, Kibana, Solr, Matomo, httpd, Mailpit)"
    compose_platform up -d
  fi
  wait_url "$BASE_URL/keycloak/realms/citelibre_backoffice" citelibre-keycloak

  info "Starting CiteLibre $app $version (the first start takes a few minutes)"
  compose_app "$app" up -d
  wait_url "$BASE_URL/citelibre-$app/jsp/site/Portal.jsp" "citelibre-$app"

  cat <<EOF

CiteLibre $app is ready:
  Portal        $BASE_URL/
  Front office  $BASE_URL/citelibre-$app/jsp/site/Portal.jsp   test@citelibre.org / citelibre
  Back office   $BASE_URL/citelibre-$app/jsp/admin/AdminMenu.jsp   admin@citelibre.org / citelibre
  Mails sent    $BASE_URL/mailpit/

Stop with ./citelibre.sh stop (data is kept), start from scratch with ./citelibre.sh reset
EOF
  if $browser; then open_browser "$BASE_URL/"; fi
}

stop() {
  check_docker
  local app
  for app in $APPS; do compose_app "$app" stop; done
  compose_platform stop
}

reset() {
  check_docker
  local answer app
  read -r -p "Every CiteLibre container and its data will be removed. Continue? [y/N] " answer
  [[ $answer == [yYoO]* ]] || exit 0
  # Applications first: they use the network created by the platform
  for app in $APPS; do compose_app "$app" down --volumes --remove-orphans; done
  compose_platform down --volumes --remove-orphans
}

status() {
  check_docker
  docker ps -a --filter name=citelibre- --format 'table {{.Names}}\t{{.Status}}'
}

logs() {
  local app=${1:-rendezvous}
  check_app "$app"
  check_docker
  [ -n "$(docker ps -q --filter "name=^citelibre-$app$")" ] || fail "citelibre-$app is not running."
  # Lutece writes its logs in WEB-INF/logs, not on the container output
  docker exec "citelibre-$app" sh -c \
    "cd /opt/applications/apache-tomcat/webapps/citelibre-$app/WEB-INF/logs && tail -n 50 -F application.log error.log"
}

command=${1:-start}
[ $# -gt 0 ] && shift
case $command in
  start) start "$@" ;;
  stop) stop ;;
  reset) reset ;;
  status) status ;;
  logs) logs "$@" ;;
  -h|--help|help) usage ;;
  # ./citelibre.sh rendezvous --lite: start is implied
  *) start "$command" "$@" ;;
esac
