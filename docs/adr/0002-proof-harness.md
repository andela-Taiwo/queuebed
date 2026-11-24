# 0002: Guarantees are proven by a history checker and planted bugs

## Status

Accepted

## Context

A queue's promises (no lost jobs, no double execution while leased, rolled-back enqueues never
run, one run per schedule slot, fair service between tenants) fail only in rare
interleavings. A test that kills a worker at a random moment usually kills it somewhere
harmless and passes. When the bad interleaving does occur, it happens once and is dismissed as
flaky.

Two failures need special care:

- **Zombie workers.** A worker paused by a long GC pause or a stalled VM can wake after its
  lease expired and another worker claimed the job. If it can still complete the job, the
  job's effects happen twice and the record is wrong. Every write by a worker therefore
  carries a fencing token (the attempt number), and the database refuses writes from an older
  attempt.
- **Clocks.** Worker clocks drift and can be wrong by minutes. If a worker decides from its own
  clock that its lease is still valid, two workers can both believe they hold the job. Every
  lease and schedule decision uses the database's `now()`.

## Decision

- **Record, then judge.** An append-only history, written by a recorder the queue code cannot
  modify, captures every operation. One checker judges the whole history against the
  invariants after each run, in the style of Jepsen.
- **Control when faults happen.** Workers stop at named fault points. In exhaustive mode a
  scheduler releases, kills (SIGKILL) or pauses (SIGSTOP) each worker at each point, covering
  every interleaving within stated bounds. In random mode, seeded campaigns run under
  Hypothesis stateful testing, which shrinks failures to a minimal replayable sequence.
- **Faults beyond processes.** `pg_ctl stop -m immediate`, a local TCP proxy that delays,
  drops or cuts connections mid-transaction, and per-worker clock offsets through an injected
  clock.
- **Planted bugs prove the checker.** Each guarantee has a deliberately broken implementation
  that the checker must catch, exhaustively or within a stated number of seeds. They stay as
  permanent tests.
- **The same checker judges fairness.** Bounded service lag per tenant is an invariant like
  the others, so fault campaigns attack fairness as hard as durability.

## Consequences

- Claims are bounded: "zero violations in these exhaustive bounds and N seeded campaigns".
  This is systematic exploration, not formal verification, and the docs say so.
- Queue code must expose fault points and use an injected clock, which shapes its design from
  the first session.
- Tests wait on conditions, never on sleeps, so timing does not decide results.
