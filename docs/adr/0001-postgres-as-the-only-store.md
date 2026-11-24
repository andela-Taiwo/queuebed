# 0001: Postgres is the only store

## Status

Accepted

## Context

Most teams that need background jobs already run Postgres. A separate broker (Redis,
RabbitMQ) adds a system to operate, back up and monitor, and loses the ability to enqueue a
job in the same transaction as the data it acts on. That transactional enqueue removes a
whole class of bugs: a job for an order that was rolled back, or an order with no job.

Since Postgres 9.5, `SELECT ... FOR UPDATE SKIP LOCKED` lets many workers claim different
rows without blocking each other, which is what a queue needs.

## Decision

- All queue, job and schedule state lives in Postgres tables.
- Workers claim jobs with `FOR UPDATE SKIP LOCKED` and hold a time-limited lease.
- Delivery is at least once. A job may run again if its worker dies after doing the work but
  before recording it, so jobs must be idempotent, and the docs say so plainly.

## Consequences

- Throughput is bounded by Postgres. Session 7 measures where that bound is and documents it.
- Job tables churn, so vacuum and bloat need attention and monitoring.
- `LISTEN/NOTIFY` can wake idle workers early, but polling stays as the fallback, so a missed
  notification only adds latency.
