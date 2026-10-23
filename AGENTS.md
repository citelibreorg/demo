# AGENTS.md

## What this repo is

CiteLibre demo: Docker Compose stack to run the CiteLibre services
(`citelibre-rendezvous`, `citelibre-serviceez`, `citelibre-participez`) locally, plus
Cypress e2e tests. No Maven build, no application code: changes are compose files,
`.env` files, SQL init scripts, third party configuration (httpd, Keycloak, Matomo,
Solr, Kibana) and tests.

CiteLibre is split into three sibling repositories (usually cloned side by side):

- `packaging`: Maven assembly + Docker image build (Jib) of each service.
- `demo` (this one): Docker Compose stack and e2e tests.
- `ops`: Kubernetes deployment (Bundlebee descriptors, Minikube scripts).

## Layout

- `citelibre-platform/`: shared infrastructure compose (MariaDB, Keycloak,
  Elasticsearch, Kibana, Solr, Matomo, Adminer, httpd portal on port 80, Mailpit) and
  its configuration files.
- `citelibre-common/sql/init_db.sh`: DB bootstrap script mounted by every compose file.
- `citelibre-<app>/`: `docker-compose.yml`, `.env`, `sql/*.sql` for one service.
- `tests/`: Cypress e2e tests (standalone npm project).

## Launcher

- `citelibre.sh` (Linux / macOS) and `citelibre.ps1` (Windows, run through
  `citelibre.cmd`) implement the same commands (`start [app] [--lite] [--version x]
  [--no-browser]`, `stop`, `reset`, `status`, `logs [app]`): **change both together**.
  `citelibre.ps1` must stay ASCII and Windows PowerShell 5.1 compatible (no `??`,
  ternary, `&&`). It can be tested on Linux with a portable `pwsh`.
- `start` uses the local image when present, else pulls it; waits for
  `/keycloak/realms/citelibre_backoffice` then the app `Portal.jsp`.
  `--lite` starts only `mariadb init-keycloak-db keycloak httpd mailpit` (RendezVous
  works, Cypress `cy:common` green; the app logs `UnknownHostException
  citelibre-elastic`, expected).
- `.gitattributes` forces LF on `*.sh` (mounted in Linux containers, a CRLF
  `init_db.sh` breaks on Windows checkouts) and CRLF on `*.cmd` / `*.ps1`.

## Local stack (order matters)

1. `docker compose -f citelibre-platform/docker-compose.yml up -d` — creates the named
   network `citelibre-network`.
2. `docker compose -f citelibre-rendezvous/docker-compose.yml up` — app compose files
   declare `citelibre-network` as **external**, so they fail if the platform is not up
   first.
- The app image `citelibre/packaging-<app>:${CITELIBRE_IMAGE_VERSION}` is pulled from
  Docker Hub (pushed by the `packaging` tag workflow) unless it exists locally: build it
  in the `packaging` repo with `mvn package -Passembly,<app>,docker` (same name).
- `CITELIBRE_IMAGE_VERSION` in each app's `.env` must match the profile's
  `citelibre.packaging.version` in the `packaging` pom — the serviceez `.env` (1.0.9) is
  stale vs its pom profile (1.0.2).
- All compose files take their variables from the `.env` next to them (local dev
  credentials — never put real secrets there).
- DB bootstrap: shared `citelibre-common/sql/init_db.sh` + each app's `sql/*.sql`
  (choose the auth provider SQL file that is mounted, not the commented one). It skips
  an existing database, so `stop` / `up` again keeps the data; `down` resets it.
- RendezVous demo data: `citelibre-rendezvous/sql/03-demo-appointments.sql` (workflow with
  mail tasks, 3 forms, bookings) is **generated** by `03-demo-appointments.py` next to it:
  edit the Python and regenerate (`python3 03-demo-appointments.py 03-demo-appointments.sql`).
  Demo only: `ops` targets production and must not get these data sets. Dates are
  relative to `CURDATE()` (n-th weekday after/before today); fixed ids assume the
  `00-init.sql` dump (workflow 1, states 1-2, action 1, tasks 1-2 already taken).
  Workflow mails go to Mailpit (`mail.server=mailpit` in the image). Action icons are left
  NULL: the BO appointment list builds a broken relative URL for them.
- Lutece logs go to a named volume `<app>-logs` (`CITELIBRE_DOCKER_VOLUME_PATH`), not
  a host folder: a bind mount is created root-owned on Linux.
- Keycloak runs with `KC_CACHE: local`: the DB dump holds a stale `JGROUPS_PING` row.
- Mailpit is only reachable through httpd (`/mailpit`), no host port is published.
  Volume paths are relative to the compose file (`../citelibre-common/...`): keep the
  layout when moving files.
- Back office: `http://localhost/citelibre-rendezvous/jsp/admin/AdminMenu.jsp`
  (`admin@citelibre.org` / `citelibre`); front office: `/jsp/site/Portal.jsp`.

## E2E tests (Cypress)

- `tests/` is a standalone npm project: `cd tests && npm install && npm run cy:common`.
- Requires the platform and the service under test to be running first (baseUrl is the
  rendezvous back office); login uses the local dev credentials.

## Community files

- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` and `SECURITY.md` are identical copies in
  `packaging`, `demo`, `ops` and the org `.github` repository (org-wide default). When
  changing one, apply the same change to all four copies. Keep their links relative
  (`CODE_OF_CONDUCT.md`, `SECURITY.md`) or absolute and repo-independent.
- Issue and pull request templates live only in the org `.github` repository; do not add
  a `.github/ISSUE_TEMPLATE/` here, it would replace all the org templates.
