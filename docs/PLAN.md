# Plan

Queuebed is built in sessions, each with a clear success test. Later sessions build on
earlier ones. The queue core stays modest. Most of the work is the machinery that proves it
keeps its promises, and the fair claim engine that machinery judges.

## How guarantees are proven

A test that kills a worker at a random moment usually kills it somewhere harmless. Passing it
is hope, not proof. Queuebed proves its guarantees with:

- **A history recorder** the queue code cannot touch. Every enqueue, claim, heartbeat,
  completion, failure, lease expiry and Postgres restart is appended to it.
- **One invariant checker** that judges each whole history:
  - no lost jobs;
  - no ghost jobs from rolled-back transactions;
  - no overlapping execution;
  - no completion by a fenced (stale) worker;
  - exactly one run per schedule slot;
  - bounded service lag per tenant.
- **A seeded fault scheduler** with named fault points: SIGKILL, SIGSTOP and SIGCONT, per-worker
  clock skew, `pg_ctl stop -m immediate`, and a TCP proxy that delays, drops or cuts
  connections mid-transaction.
- **Bounded exhaustive exploration** (2 workers, 3 jobs, every interleaving of up to 3 fault
  points) and **seeded campaigns** with Hypothesis shrinking. A failure is a seed and a shrunk
  sequence that replays, never "flaky".
- **Planted bugs** that the checker must catch, each kept as a permanent test.

## The numbers

- **Teeth:** 12 planted bugs, each caught by the exhaustive run or within 200 seeded
  campaigns, as stated per bug:
  1. fencing check removed;
  2. lease expiry from the worker's clock;
  3. acknowledgement before the result is recorded;
  4. claim without SKIP LOCKED;
  5. heartbeats skipped;
  6. enqueue outside the caller's transaction;
  7. lease not renewed after a reconnect;
  8. retry count not incremented on crash;
  9. dead-lettering skipped at the attempt limit;
  10. fairness deficit not charged on claim;
  11. per-tenant cap bypassed under concurrent claims;
  12. schedule slot not unique.
- **No violations** across the exhaustive runs, 1,000 seeded campaigns, and a soak of at
  least 2 hours with faults injected every few seconds.
- **Twin agreement:**
  - under serialised arrivals, the real dispatch order equals the in-memory twin's, claim by
    claim, for every seed;
  - under W concurrent workers, each tenant's maximum service lag is at most the twin's plus
    W - 1 claims.
- **Fairness against FIFO:** with one tenant enqueuing 100,000 jobs and 20 trickling, the
  trickling tenants' p99 wait stays within 2x their unloaded p99, and the Jain index of
  service share is at least 0.95.
- **Scheduling:** exactly one run per slot with 3 racing schedulers, across a fixed table of
  real daylight-saving transitions.

## Sessions

| # | Session | Success |
|---|---|---|
| 1 | Queue core and history: transactional enqueue, SKIP LOCKED claims, leases with fencing tokens; the history recorder; first invariants (no lost jobs, no ghost jobs) | The checker runs on every test; planted bugs 1 and 6 are caught |
| 2 | Fault scheduler: named fault points, kill, SIGSTOP, clock skew, immediate Postgres restarts, the TCP proxy; bounded exhaustive exploration | Zero violations; planted bugs 1 to 5 and 7 caught exhaustively |
| 3 | A checker worth trusting: Hypothesis stateful campaigns with shrinking, seeds that replay, the planted-bug suite in CI | Every planted bug so far caught within 200 seeds; every failure replays from its seed with a shrunk sequence |
| 4 | Retries, timeouts and dead letters under the harness | A poison job never blocks the queue; bugs 8 and 9 caught; zero violations across 1,000 campaigns |
| 5 | Fair claim engine: deficit round-robin over per-tenant virtual time in one SKIP LOCKED claim; sharded per-tenant caps; bounded-lag invariant | Bugs 10 and 11 caught; bounded lag holds under every fault campaign |
| 6 | Deterministic twin and fairness measurement: an in-memory implementation of the same policy, written separately from the SQL | Identical order under serialised arrivals; lag within the twin's bound plus W - 1; the fairness numbers against FIFO |
| 7 | Slot-identity scheduling and the soak: unique (schedule, slot), explicit catch-up policies, the DST table; a 2-hour soak with faults; measured limits | Bug 12 caught; one run per slot with 3 schedulers; zero violations over the soak; limits documented |

## Out of scope

The web dashboard, Playwright, container images and Kubernetes. None could be verified here,
and the hours go to the harness. Operators get a CLI, an admin API and metrics in Prometheus
text format. Multi-step workflows with compensation are a separate product; Queuebed provides
idempotency keys, fencing and clear at-least-once semantics for one to build on.

## Rules

- Postgres is the only stateful dependency. No Redis, no message broker.
- Delivery is at least once. Exactly-once effects come from idempotent jobs, and the docs say
  so.
- Every lease and schedule decision uses the database's clock, never a worker's.
- Every new guarantee comes with a planted bug, and the checker catching it comes first.
- Claims are stated with their bounds: "zero violations in these exhaustive bounds and N
  seeds", never "proven".
- Tests that need Postgres use a separate test database and never touch a developer's data.
- No secrets in logs, errors, URLs or the command line.
