# History

Completed work, in reverse chronological order.

---

## 2026-06-02 - Test coverage: sender.py and main.py

Added `tests/test_sender.py` and `tests/test_main.py` - both modules had zero coverage.

- `_subject_from_file`: 6 tests (SEND-suffix strip, title-case, no-suffix, full path)
- `_md_to_html`: 5 tests (plain text, bold, link, empty)
- `send_letter`: 1 test (Status-header stripped from MIME body via FakeSMTP)
- `log_delivery`: 4 tests (creates header, appends, creates parent dir, filename-only)
- `poll`: 5 tests (no pending, success path, failure path, multiple letters, partial failure)

Total suite: 18 -> 39 tests.

---

## 2026-05-30 - MVP built (repo created, scaffold, TDD, implementation)

**What was built:**

### Repo scaffold
- `README.md` - benefit-first intro (never copy-paste to emailfuture.com again), Ko-fi badge, comparison table of services that fall short, install/usage/config guide, filename convention
- `CLAUDE.md` - tech stack, run commands, key paths, safety rules (never commit config.yaml)
- `.gitignore` - credentials, data/, pycache
- `config/config.example.yaml` - generic SMTP template with placeholder values (no personal data)
- `config/requirements.txt` - schedule, pyyaml, markdown
- `docs/IDEAS.md` - MVP backlog + locked decisions
- `docs/HISTORY.md` - this file

### Tests (TDD - written before implementation)
- `tests/test_scheduler.py` - 18 tests covering:
  - `parse_send_date`: valid filenames, any prefix, no pattern, wrong extension, malformed date, missing day, SEND at start
  - `is_due`: past, today, tomorrow, far future
  - `get_pending_letters`: filters future-dated, already-delivered, no-pattern, empty dir, nonexistent dir
  - `mark_delivered`: prepends Status header, idempotent if already delivered, preserves full body

### Implementation
- `src/scheduler.py` - filename parser (`SEND-YYYY-MM-DD` regex), `is_due` date comparison, `get_pending_letters` (scans dir, filters), `mark_delivered` (prepends `Status: Delivered <timestamp>` header, idempotent)
- `src/sender.py` - loads markdown file, converts to HTML via `markdown` pkg, builds MIME multipart (plain + HTML), sends via smtplib STARTTLS (Outlook/Gmail), subject derived from filename
- `src/main.py` - loads `config/config.yaml`, runs `poll()` on startup + every hour + daily at configured `send_time`, logs each delivery to `data/logs/deliveries.csv`

**Status:** All 18 tests pass. End-to-end test (real SMTP send) pending - needs `config/config.yaml` with real credentials.

**Design decisions made:**
- Used `markdown` + `smtplib` over the `futuremail` pip package (more control, no extra abstraction)
- Filesystem-only persistence for MVP (`Status: Delivered` header = done, no database)
- Hourly poll + dedicated daily fire at `send_time` (belt and suspenders for the daily use case)
