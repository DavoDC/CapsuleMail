# Ideas & Future Work

Completed items -> `HISTORY.md`.

---

## Next (MVP gate)

- [ ] **End-to-end test** *(manual prerequisite: create `config/config.yaml` with real credentials - that's on you to set up)* - drop a `test-letter-SEND-<tomorrow>.md` in `letters_dir`, temporarily set `send_time` to now+2min, run `python src/main.py`, verify: email received in inbox, HTML renders correctly, `Status: Delivered` header written back to file, log entry in `data/logs/deliveries.csv`

## Automated Tests - Gaps

`scheduler.py` is fully covered (18 tests). Two modules have zero coverage:

**sender.py** (high value - subject line logic runs on every send):
- `_subject_from_file`: filename -> subject line cleanup. Pure function. Test: SEND-suffix stripped, dashes -> spaces, title case, already-title input, no SEND suffix preserved.
- `_md_to_html`: markdown rendering. Test: bold, link, plain text round-trips. Verify output is HTML string (starts with `<`).
- `send_letter` body: Status-header strip before send. Testable by mocking smtplib.SMTP and asserting the MIME body excludes the "Status: Delivered" line.

**main.py** (high value - poll() is the core delivery loop):
- `log_delivery`: CSV write. Test: creates file + header on first call, appends on second call, creates parent dir if missing.
- `poll` - no pending letters: returns without calling send. Test: mock get_pending_letters returns []; assert send_letter not called.
- `poll` - send succeeds: calls send_letter, mark_delivered, log_delivery with "delivered". Test: mock all three; assert calls in order.
- `poll` - send raises Exception: logs "failed: ...", does NOT call mark_delivered. Test: mock send_letter to raise; assert mark_delivered not called, log_delivery called with "failed" status.

## Phase 2 - Quality

- [ ] Retry logic for failed sends (3 attempts, exponential backoff)
- [ ] Multiple recipient support (`recipients.alt` list in config)
- [ ] Dashboard: print upcoming scheduled letters and sent history on startup
- [ ] Export log entries back to a local archive on delivery

## Phase 3 - Polish

- [ ] HTML template customization (custom CSS wrapper around the converted markdown)
- [ ] Calendar integration - surface upcoming sends in a task list or notification
- [ ] Signature detection (parse "Love, David" style closings, treat separately from body)
- [ ] "Letter sent!" desktop notification at send time

---

## Decisions (locked)

| Decision | Choice | Reason |
|----------|--------|--------|
| SMTP provider | Outlook (primary), Gmail supported | App passwords supported on both |
| Persistence | Filesystem only for MVP | Letter file exists = pending; `Status: Delivered` header = done. SQLite only if this proves insufficient |
| Timezone | Configurable - default `Australia/Perth` (AWST, UTC+8) | User-defined in config |
| Email format | Markdown -> HTML via `markdown` pip package + smtplib | Clean rendering; no external service needed |
| Retry | Phase 2 | MVP ships without it |
| Startup | Manual terminal run | No tray needed for MVP; shell:startup shortcut optional |
| Scheduling layer | This daemon - polls hourly via `schedule` pkg | Existing libs are sending-only, not schedulers |
| Poll frequency | Hourly + dedicated daily fire at `send_time` | Low spin, accurate enough for daily sends |
