# Data Hygiene

RO Workstation is designed for local operational data, but source control should stay focused on application code, configuration, seed data, and documentation.

## Keep Out Of Git

- Runtime SQLite files: `data/*.db`, `data/*.sqlite`, `data/*.db-shm`, `data/*.db-wal`.
- Runtime logs: `data/audit.log`.
- Temporary test folders under `data/test_runtime/`.
- Scratch scripts and inspection output under `scratch/`.
- Generated exports under `files/generated/`.
- Local Excel/PDF working files unless they are intentional fixtures.

## Commit Only Intentional Fixtures

If a spreadsheet or PDF is needed for automated tests or examples, place a small sanitized fixture under `tests/fixtures/` and force-add it with a clear commit message. Avoid committing full operational archives.

## Backups

Use the `backups/` directory for local snapshots and keep it outside Git. For production, copy `data/`, `files/`, and `backups/` to an approved secure location on a regular schedule.
