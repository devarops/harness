# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [x] Find the criterion a multi-line skip removal belongs to.
      Test: the skip owner is the criterion whose skip line left the spec, even when its description spans several lines and the diff hunk omits the opening line; `make tests` passes.
