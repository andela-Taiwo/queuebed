# Queuebed

A job queue and scheduler that keeps its state in Postgres, with no broker to operate, and
proves it keeps its promises. Jobs are enqueued in the caller's transaction, claimed fairly
across tenants, and judged by a fault-injection harness that kills, pauses and skews workers
and must catch deliberately planted bugs.

> **Status: foundation only.** The project layout, tooling, duration parsing and validated
> settings exist and are tested. The queue core, history recorder, invariant checker, fault
> scheduler, fair claim engine, twin and scheduler are not built yet. See
> [the plan](docs/PLAN.md).

## What it will do

- **Enqueue** jobs in the same transaction as the data they act on, with idempotency keys, so
  a rolled-back transaction never leaves a job behind.
- **Claim** jobs with `FOR UPDATE SKIP LOCKED` under leases with fencing tokens, so a worker
  that wakes after its lease expired cannot complete a job someone else took.
- **Share fairly** between tenants: deficit round-robin inside the claim query itself, with
  per-tenant caps, so one tenant flooding the queue cannot starve the rest.
- **Retry** with backoff, give up after a set number of attempts, and keep dead jobs for
  replay.
- **Schedule** recurring jobs exactly once per slot, through daylight-saving changes, with an
  explicit catch-up policy after downtime.
- **Operate** from a CLI and admin API, with metrics in Prometheus text format.

## How it is proven

- A **history recorder** the queue cannot touch, and one **invariant checker**: no lost jobs,
  no ghost jobs, no overlapping execution, no fenced completions, one run per slot, bounded
  service lag per tenant.
- A **seeded fault scheduler**: kill, pause, clock skew, immediate Postgres restarts and a TCP
  proxy that cuts connections mid-transaction; exhaustive within small bounds, seeded and
  shrunk beyond them.
- **Planted bugs** the checker must catch, and a **deterministic twin** of the fairness policy
  the real system must agree with.

Out of scope: a web dashboard, container images and Kubernetes. See [the plan](docs/PLAN.md)
for why, and for the numbers each session is held to.

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
