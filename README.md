# Threat Intel Ingestion

This LXC-oriented service ingests three independent sources into PostgreSQL:

- `cisa-kev` refreshes CISA's Known Exploited Vulnerabilities catalogue.
- `nvd` incrementally ingests NVD CVEs modified since the last successful run.
- `krebs` stores newly listed Krebs on Security articles and derived tags.

Each command is idempotent and returns a non-zero exit status on failure, making it safe for cron. The NVD watermark advances only after a complete database transaction succeeds; a small overlap is intentionally re-read on the next run.

## LXC installation

Run these steps inside the container as an administrator. The scheduled commands run as the unprivileged `ti` account; PostgreSQL may be local or reachable through the `DATABASE_URL` host.

For a new Debian/Ubuntu systemd LXC deployed at `/opt/threat-intel`, the all-in-one bootstrap is the recommended path:

```bash
cd /opt/threat-intel
chmod 0755 bin/setup-and-start bin/setup-postgres
./bin/setup-and-start
```

It creates the service account, provisions PostgreSQL, installs dependencies, enables cron and the dashboard, and runs the first source sync. Use `./bin/setup-and-start --no-initial-sync` when you want to start services without immediately downloading feeds.

The manual sequence below remains useful for customized deployments.

```bash
groupadd --system ti
useradd --system --gid ti --create-home --shell /usr/sbin/nologin ti
install -d -m 0755 -o root -g root /opt/threat-intel
install -d -m 0750 -o ti -g ti /var/log/threat-intel /var/lock/threat-intel
# Deploy this repository to /opt/threat-intel as root, then create its virtual environment:
python3 -m venv /opt/threat-intel/venv
/opt/threat-intel/venv/bin/pip install --upgrade pip
/opt/threat-intel/venv/bin/pip install -r /opt/threat-intel/requirements.txt
install -d -m 0750 -o root -g ti /etc/threat-intel
install -m 0640 -o root -g ti /opt/threat-intel/.env.example /etc/threat-intel/threat-intel.env
# Edit DATABASE_URL (and optionally NVD_API_KEY) in the environment file.
chmod 0755 /opt/threat-intel/bin/run-job
```

Never keep production credentials in the repository. Rotate the previously committed database password before deploying this version.

Bootstrap PostgreSQL, create the application role/database, apply the schema, and create the environment file in one step:

```bash
/opt/threat-intel/bin/setup-postgres --install-postgresql
```

The script prompts for a database password and does not modify an existing environment file unless `--write-env` is provided; that option updates only `DATABASE_URL` and preserves other settings. On an already provisioned PostgreSQL server, omit `--install-postgresql`. Run `setup-postgres --help` for database/role overrides.

New databases are explicitly created as UTF-8. If you are reusing an older `SQL_ASCII` database, the application still forces UTF-8 client connections so feed content is accepted, but migrate to a UTF-8 PostgreSQL database when practical.

Install the supplied scheduler and log rotation policy:

```bash
install -m 0644 deploy/cron.d/threat-intel /etc/cron.d/threat-intel
install -m 0644 deploy/logrotate/threat-intel /etc/logrotate.d/threat-intel
systemctl reload cron
```

## Search dashboard

The dashboard is a read-only Flask application that searches CVE metadata, CISA KEV status, and collected articles. It binds to `127.0.0.1:8080` by default, so it is not exposed outside the LXC without an intentional reverse proxy or SSH tunnel.

The **Articles & RSS** page lets an authorized dashboard user add individual RSS or Atom URLs with a source type, reliability rating, and priority. The hourly `rss` cron job ingests enabled feeds and records per-feed success/failure health on that page. The initial setup seeds CISA Advisories, Microsoft MSRC, DFIR Report, Unit 42, Cisco Talos, SANS ISC, and BleepingComputer; add other verified RSS/Atom endpoints through the page.

```bash
install -m 0644 deploy/systemd/threat-intel-dashboard.service /etc/systemd/system/threat-intel-dashboard.service
chmod 0755 /opt/threat-intel/bin/run-dashboard
systemctl daemon-reload
systemctl enable --now threat-intel-dashboard
curl --fail http://127.0.0.1:8080/healthz
```

For local access from an administrator workstation, use an SSH tunnel:

```bash
ssh -L 8080:127.0.0.1:8080 root@YOUR_CONTAINER_HOST
```

Then open `http://127.0.0.1:8080`. If you publish it through a reverse proxy, require authentication and TLS. The dashboard uses read-only PostgreSQL sessions and accepts an optional `DASHBOARD_DATABASE_URL` for a separately provisioned read-only database role.

Run and inspect a job before waiting for cron:

```bash
sudo -u ti /opt/threat-intel/bin/run-job cisa-kev
tail -n 100 /var/log/threat-intel/cisa-kev.log
```

## Commands

```bash
python -m scraper.jobs init-db
python -m scraper.jobs cisa-kev
python -m scraper.jobs nvd
python -m scraper.jobs krebs
python -m scraper.jobs rss
python -m scraper.jobs seed-rss
```

Configuration is documented in `.env.example`. Cron output is one JSON object per line by default, so a log collector can index timestamps, source counts, and exceptions. NVD uses 2,000-record pages, retries transient failures, honours `Retry-After`, and defaults to a conservative 6.5-second inter-page delay without an API key. Its API request window is capped at 120 days; if the job has been offline longer it resumes through consecutive safe windows.

## Teardown

To permanently remove this deployment's runtime state, run:

```bash
sudo /opt/threat-intel/bin/teardown
```

The script requires typing `DELETE` before it drops the `threatintel` database and `ti_user` PostgreSQL role. It also removes the `ti` Linux account, dashboard unit, cron schedule, credentials, logs, and locks. It intentionally preserves the application files and PostgreSQL packages/clusters because they may be shared. Use `--yes` only for a deliberate automated removal.
