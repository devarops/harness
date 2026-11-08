---
description: Close the in-progress TODO item when its Test line and the suite agree.
---

We are in the acceptance phase of the local TDD loop. Read
`.opencode/local-loop.md` and follow it.

## Task

- Find the single `[*]` item in `TODO.md` and its `Test:` line.
- Verify that the working tree is clean.
- Run `make tests`. If any test fails, report the failures as the gap and stop;
  the next command is `local-red`.
- Evaluate the `Test:` line against the repository: run the commands it names
  and inspect the artifacts it cites. Do not accept a claim the repository
  cannot show.
- If the line is not satisfied, report what remains as the gap, specific enough
  for one failing test, and stop without editing `TODO.md`.
- If the line is satisfied, change the item's marker to `[x]`.
- Stage only `TODO.md` and commit:

📝 Mark <item summary> done

<the Test line and the evidence that satisfies it>

- Report the commit hash and `git revert <hash>`. Do not start Red.
