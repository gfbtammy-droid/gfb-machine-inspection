# Test kit (dummy data only)
`python3 tests/run.py` from the repo root opens the real `index.html` in Chrome against `fake-supabase.js` (an in-memory stand-in, no real data or passwords) at phone and desktop sizes, and walks through: first-run checklist load, operator round, remark rules, check, return for correction, verify, lock, print, records, CSV, checklist editing, users, self-registration.
Needs `pip install playwright` and Google Chrome. Screenshots and sample PDFs go to `tests/out/` (ignored by git).
