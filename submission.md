# Week 4: AI-Augmented TDD & Branch Coverage Audit

## Bug log

No original `knight_cash_api.py` was supplied, so this project implements a compatible
FastAPI baseline from scratch. The following are the three high-severity vulnerabilities
the final regression suite was written to prevent:

- **Non-positive transfers:** An amount of `0` or less could be used to create a no-op
  transfer or reverse the direction of a payment. The API explicitly rejects `amount <= 0`
  with HTTP 400 before modifying either balance.
- **Overdrafts:** A sender could transfer more than their available balance, creating a
  negative balance. The API checks the sender's funds and returns HTTP 400 when the
  requested amount is too large; an exact-balance transfer remains valid.
- **Invalid or self-directed recipients:** Missing accounts could cause a server failure,
  while a same-account transfer has no valid business purpose. The API returns HTTP 404
  for unknown accounts and HTTP 400 for blank or identical sender/recipient values.

## Coverage proof

Final verified coverage: **100% overall coverage and 100% branch coverage** (38 statements,
10 branches, 0 partial branches), with 17 passing tests.

The final branch-coverage run and its HTML report are generated with:

```powershell
pytest --cov=knight_cash_api --cov-report=html --cov-branch
```

Open `htmlcov/index.html` locally to view the generated visual report. The in-app browser
blocks local `file:///` pages, so this environment cannot capture that page as a screenshot;
the HTML artifact is included in the project instead.

## Prompt audit

Exact Step 4 prompt used:

> Write a specific Pytest case that will trigger the untested insufficient-funds branch:
> submit a `/transfer` request where the sender exists but the amount is one cent greater
> than their balance, then assert HTTP 400, the `Insufficient funds` message, and that no
> recipient balance changed.

## Repository link

GitHub repository: https://github.com/pkj-web/week4-knight-cash-tdd

The fixed API and test suite are `knight_cash_api.py` and `test_knight_cash.py` in the
repository root.

