# NOTES.md — memory/ (cross-run session state vs. durable log)

- "Session" here is defined purely operationally — a run of consecutive
  invocations of the same script sharing one `session.json` — with no wall
  clock involved at all. The session id is derived by counting
  `session_start` events already in the durable log, which turned out to be
  a clean way to get deterministic, monotonically-increasing session ids
  without a timestamp or a counter file.
- The promotion step (`session_summary` appended *before* `session.json` is
  deleted) is the part that actually matters, more than the expiry itself.
  Deleting session state without promoting first would just be `state/`'s
  crash-and-wipe failure mode again, one layer up (session-scoped instead
  of run-scoped) — expiry alone isn't the safe part, promotion is.
- Ordering mattered in the code: append the summary to the log, confirm
  that write, and only then delete `session.json`. If those two operations
  were reversed (or not sequenced), a crash between them would produce
  exactly the data loss this tier separation exists to prevent — running
  this made that ordering dependency concrete instead of theoretical.
- Surprise: nothing about "session vs. durable log" required a different
  storage mechanism (both are still plain files) — the difference is
  entirely in what's allowed to happen to each file: `session.json` is
  disposable-by-design and gets deleted outright; `log.jsonl` is never
  deleted, only ever appended to. The lifetime is a policy the code
  enforces, not a property of the storage layer.
- Run #3 landing on a brand-new session id (S2) rather than resuming S1 is
  the correct behavior, but it's worth flagging as a real design decision:
  this script treats "session expired" as "start over with no continuity,"
  not "start over with S1's summary loaded back in." A system wanting
  continuity would need to explicitly read the last `session_summary` back
  out of the log when bootstrapping a new session — that's a deliberate
  choice this exercise did NOT make, and NOT an automatic consequence of
  the tiering pattern itself.
- `SESSION_MAX_RUNS = 2` is an arbitrary, small threshold chosen only to make
  expiry visible in 3 runs for this proof. Nothing else in the design
  depends on that specific number; a real system would key expiry off of
  something meaningful (idle time, token budget, explicit close) rather
  than a fixed run count.
- What this does NOT prove: it doesn't test concurrent runs of the session
  (two processes racing on `session.json`), and it doesn't demonstrate
  reading facts back OUT of a past `session_summary` for use in a new
  session — only that the summary is safely captured in the log when the
  session dies.
