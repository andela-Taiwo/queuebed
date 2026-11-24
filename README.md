# Queuebed

A job queue and scheduler that keeps its state in Postgres: enqueue work from any service,
run it on a pool of workers, retry what fails, and run recurring jobs on a schedule, with no
broker to operate.

> **Status: foundation only.** The project layout, tooling, duration parsing and validated
> settings exist and are tested. The schema, workers, retries, scheduler, admin API and
> deployment are not built yet. See [the plan](docs/PLAN.md).

## What it will do

- **Enqueue** jobs in the same transaction as the data they act on, with optional idempotency
  keys, priorities and run-after times.
- **Run** jobs on a worker pool that claims them with `FOR UPDATE SKIP LOCKED` and holds a
  lease, so a crashed worker's jobs are picked up again.
- **Retry** with backoff, give up after a set number of attempts, and keep failed jobs for
  inspection and replay.
- **Schedule** recurring jobs from cron expressions, exactly once per slot across many
  scheduler instances.
- **Operate**: an admin API and dashboard, metrics, graceful shutdown and a deployment that
  survives losing a worker or the database restarting.

## What exists today

| Module | What it does |
|---|---|
| `queuebed.durations` | Parses and formats durations such as `250ms`, `30s` and `1h30m` |
| `queuebed.settings` | Reads and validates settings from the environment, reports every problem at once, and never shows the database password |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12. Later sessions need PostgreSQL 14
or newer.

```bash
make setup   # install locked dependencies
make check   # lint, format check, type check and tests
make help    # list every target
```

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `QUEUEBED_DATABASE_URL` | (required) | `postgresql://` connection URL |
| `QUEUEBED_WORKERS` | `4` | Worker count, 1 to 256 |
| `QUEUEBED_LEASE` | `5m` | How long a claimed job is held before another worker may take it |
| `QUEUEBED_POLL_INTERVAL` | `1s` | How often idle workers look for work; must be shorter than the lease |
| `QUEUEBED_SHUTDOWN_GRACE` | `30s` | How long running jobs get to finish on shutdown |

## Licence

MIT. See [LICENSE](LICENSE).
