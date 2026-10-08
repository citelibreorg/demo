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

## Local stack (order matters)

1. `docker compose -f citelibre-platform/docker-compose.yml up -d` — creates the named
   network `citelibre-network`.
2. `docker compose -f citelibre-rendezvous/docker-compose.yml up` — app compose files
   declare `citelibre-network` as **external**, so they fail if the platform is not up
   first.
- The app image `citelibre/citelibre-<app>:${CITELIBRE_IMAGE_VERSION}` must exist
  locally: build it in the `packaging` repo with
  `mvn package -Passembly,<app>,docker`.
- `CITELIBRE_IMAGE_VERSION` in each app's `.env` must match the profile's
  `citelibre.packaging.version` in the `packaging` pom — the serviceez `.env` (1.0.9) is
  stale vs its pom profile (1.0.2).
- All compose files take their variables from the `.env` next to them (local dev
  credentials — never put real secrets there).
- DB bootstrap: shared `citelibre-common/sql/init_db.sh` + each app's `sql/*.sql`
  (choose the auth provider SQL file that is mounted, not the commented one).
  Volume paths are relative to the compose file (`../citelibre-common/...`): keep the
  layout when moving files.
- Back office: `http://localhost/citelibre-rendezvous/jsp/admin/AdminMenu.jsp`
  (`admin@citelibre.org` / `coucou`); front office: `/jsp/site/Portal.jsp`.

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
