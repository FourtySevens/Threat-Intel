# Threat Intel Ingestion Operations

## Purpose

This service runs inside an LXC container and independently ingests CISA KEV data, NVD CVE updates, and Krebs on Security articles into PostgreSQL. It is designed for cron: every source is a bounded command, is safe to run again, writes a useful exit status, and cannot overlap with another run of the same source.

For a standard Debian/Ubuntu systemd LXC, `bin/setup-and-start` performs the complete initial deployment. It creates the service user, sets up PostgreSQL and the schema, creates the virtual environment, enables cron and the dashboard, then optionally starts an initial sync. It must be run as root from `/opt/threat-intel`.

## Data flow

```
cron -> bin/run-job <source> -> python -m scraper.jobs <source>
                                      |
                       +--------------+--------------+
                       |              |              |
                    cisa-kev         nvd           krebs
                       |              |              |
                  cve + cve_kev      cve     articles + tags
                                      |
                                  job_state watermark
```

`bin/run-job` loads `/etc/threat-intel/threat-intel.env`, obtains a source-specific `flock` lock, and appends JSON logs to `/var/log/threat-intel/<source>.log`. A pre-existing lock is a successful no-op, preventing cron overlap without generating alert noise.

## Jobs

### `cisa-kev`

Fetches CISA's published Known Exploited Vulnerabilities JSON catalogue. Every entry is normalized and upserted in one database transaction. The job creates a minimal CVE record when NVD data has not arrived yet, then records KEV status, due date, and required action. A later NVD update enriches that same CVE rather than creating a duplicate.

### `nvd`

Fetches NVD CVE API v2 changes by modification time. The `job_state` row named `nvd` stores the latest fully committed timestamp. On every run the job intentionally re-reads a configurable overlap (`NVD_OVERLAP_MINUTES`, default 15) to avoid a scheduling-boundary gap. CVE writes and the watermark update share a transaction; a failure rolls back both.

The NVD API window is limited to 120 days. If the LXC has been down longer, the command processes consecutive 120-day windows and checkpoints each completed window, so recovery can resume safely. Requests use 2,000-result pages, transient-error retries with exponential backoff, `Retry-After`, and a conservative inter-page delay. An `NVD_API_KEY` is optional but recommended for a larger API allowance.

### `krebs`

Fetches the front article list, extracts article text and CVE/category tags, and inserts only new content hashes. It creates tags before attaching them, so a clean database is supported. Article hashes and URL uniqueness make repeated cron runs harmless.

## Database initialization and migration

Run `bin/setup-postgres` as root to create the role/database, apply the schema as the application role, and write the initial environment file. It can install PostgreSQL on an apt-based LXC when passed `--install-postgresql`. On a pre-provisioned server, omit that flag. `storage/schema.sql` is idempotent and additive: it creates missing tables and adds columns required by the NVD path to an existing `cve` table. It does not destroy or truncate data.

The principal tables are:

- `cve`: canonical CVE metadata from NVD, plus records initially discovered via KEV.
- `cve_kev`: one CISA KEV status per CVE.
- `articles`, `tags`, and `article_tags`: content-source storage.
- `job_state`: successful-ingestion watermarks.

## Configuration and secrets

All configuration comes from environment variables; `.env.example` documents the supported values. The production file belongs at `/etc/threat-intel/threat-intel.env`, owned by `root:ti`, mode `0640`. The service account may read it but must not write it.

`DATABASE_URL` is required. Database credentials must never be placed in Python source or committed to version control. If an older deployment used the formerly embedded password, rotate it before deploying this version.

New databases are created with UTF-8 encoding. The application explicitly requests a UTF-8 PostgreSQL client connection on every run, which prevents public-feed Unicode text from failing against legacy ASCII client defaults. A legacy `SQL_ASCII` database should nevertheless be migrated to UTF-8 for proper server-side validation and text behavior.

## Schedule and observability

`deploy/cron.d/threat-intel` schedules KEV and NVD every six hours with staggered start times and Krebs twice hourly. Change cadence only after considering source terms, API limits, database capacity, and the expected fresh-data requirement.

Logs are one JSON object per line by default and contain timestamp, level, logger, message, count fields, and exception details when a job fails. `deploy/logrotate/threat-intel` retains fourteen compressed daily rotations. A non-zero command exit is suitable for cron monitoring or a log-based alert.

## Search dashboard

`dashboard/` provides a server-rendered, read-only search interface for CVEs, CISA KEV status, and collected articles. It has vulnerability and article detail pages plus a `/healthz` endpoint. `deploy/systemd/threat-intel-dashboard.service` starts it with Gunicorn as the `ti` user.

The dashboard binds to loopback by default. It must remain behind an authenticated TLS reverse proxy when made available beyond the LXC, or be reached through an SSH tunnel. PostgreSQL connections are explicitly configured as read-only and use a five-second statement timeout; `DASHBOARD_DATABASE_URL` can point at a dedicated read-only role.

## Manual operations

```bash
# Run from the application directory with the environment loaded.
python -m scraper.jobs init-db
python -m scraper.jobs cisa-kev
python -m scraper.jobs nvd
python -m scraper.jobs krebs
```

The complete LXC installation commands are in `README.md`.
