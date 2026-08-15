---
type: Metric
title: Income Statement
generated:
  by: reference_agent/gemini-2.5-pro
  at: 2026-06-30T14:00:00Z
verified: { by: human:analyst, at: 2026-07-01T09:00:00Z }
status: stable
stale_after: 2999-12-31
sources:
  - id: income-policy
    resource: policies/income.md
    title: Income policy
    author: human:analyst
    usage_count: 12
    last_modified: 2026-06-15
usage_window: { from: 2026-01-01, to: 2026-06-30 }
executor:
  resource: skills/run.md
  receipt: [job_id]
attester:
  resource: attesters/check.py
---

# Definition

See [Machine metric](machine.md) and [Draft metric](draft.md).
