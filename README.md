# GFB Machine Inspection Checklist (F52)

Web app for the daily machine inspection checklists under procedure P07 (Preventive and Corrective Maintenance), for PC and phone.

| Form | Machine |
|---|---|
| F52/1 | Drum Mixer 250 kg, Drum Mixer 100 kg |
| F52/2 | IBC |
| F52/3 | Semi-Auto Packing Machine 1, 2, 3 |
| F52/4 | Auto-Packing Machine 1 |
| F52/5 | Auto-Packing Machine 2 |

## How it works
- **Done by**: the operator signs in with their own account, starts an inspection round (time + batch), and marks every part OK / Not OK / Missing (X) / N/A against the condition criteria and reference photo. Not OK and Missing need a remark.
- **Check by**: a Checker (QC Inspector) signs each round, or returns it to the operator with a reason.
- **Verify by**: a Verifier (Production Executive) verifies the day's checklist once every round is checked. The checklist is then locked.
- Nobody can check their own round, or verify a checklist they filled in or checked. Names and times are stamped by the system from each person's sign-in.
- **Print F52** produces the checklist in the F52 layout (form number, revision, effective date, time and batch, condition, presence, done by, check by, verify by).
- Admin can edit criteria, revision and effective date per machine (Checklists tab) and manage users (Users tab).

## Files
- `index.html` the whole app. `config.js` Supabase URL and public (anon) key only. `vendor/` Supabase library, plus jsPDF and jsPDF-AutoTable (MIT licence) for the Download PDF button.
- `templates.json` the 8 standard checklists taken from the F52 workbook; loaded into the database the first time an Admin signs in. `img/` reference photos from the F52 workbook.
- `setup.sql` database tables, rules and functions (safe to run more than once). It uses the GFB CMMS Supabase project for sign-in and adds its own `mic_...` tables; it does not change CMMS tables.
- `supabase/functions/mic-create-user/` the small server-side function (deployed on Supabase) that lets an Admin create username accounts without any email being sent.
- `tests/` click-through test with dummy data (`python3 tests/run.py`).

## Accounts
An Admin adds people under Users > Add user: a username and password for staff without email, or an existing CMMS email account (no new password). Each person is given one or more functions by tick box: Inspect (Done by), Check by, Verify by, Admin. An active CMMS admin is an Admin here automatically. Admin can reset the password of username accounts.

Never put the Supabase `service_role` key in this repository.
