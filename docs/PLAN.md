# Plan

Queuebed is built in sessions, each with a clear success test. Later sessions build on
earlier ones.

| # | Session | Success |
|---|---|---|
| 1 | Schema and migrations, and enqueueing: payloads, queues, priorities, run-after times, idempotency keys, enqueue inside the caller's transaction | A rolled-back transaction enqueues nothing; a repeated idempotency key creates one job; migrations apply and roll back on a real Postgres |
| 2 | Workers: claim with `SKIP LOCKED`, leases and heartbeats, completion, and recovery of jobs from a crashed worker | Under concurrent workers no job runs twice while its lease is held; a worker killed mid-job has its job picked up after the lease; tests use a real Postgres and real processes |
| 3 | Failure handling: retries with backoff and jitter, attempt limits, a dead-letter state, timeouts, replay | Every failure path has a test; a poison job never blocks the queue; replay runs a dead job again with its history kept |
| 4 | Scheduler: cron expressions with time zones and daylight-saving changes, exactly one run per slot across several scheduler instances, catch-up rules after downtime | Cron parsing matches a reference on a fixed table of cases; with three schedulers running, each slot runs once; DST gaps and repeats behave as documented |
| 5 | Operations: admin API (list, inspect, retry, cancel, pause a queue), Prometheus metrics, structured logs, graceful shutdown | Shutdown finishes or releases every running job within the grace period; metrics match the database state in tests |
| 6 | Dashboard and deployment: a small web UI over the admin API, container images, a compose file and a Kubernetes manifest with probes | Playwright covers pausing a queue and replaying a dead job; the deployment passes a smoke test with a worker killed and Postgres restarted |
| 7 | Scale and soak: throughput and latency benchmarks, a soak run with injected crashes, table bloat and vacuum tuning | Benchmarks fail the build on regression; a soak run loses and duplicates no job; the README states the measured limits |

## Rules

- Postgres is the only stateful dependency. No Redis, no message broker.
- Delivery is at least once. Exactly-once effects come from idempotent jobs, and the docs say
  so.
- Tests that need Postgres use a separate test database and never touch a developer's data.
- No secrets in logs, errors, URLs or the command line.
