# Ideas & Future Work

Completed items -> `HISTORY.md`.

---

## MVP (implement first)

- [ ] `src/scheduler.py` - filename parser (`SEND-YYYY-MM-DD` pattern), date comparison, state tracking (read/write `Status: Delivered` header)
- [ ] `src/sender.py` - futuremail wrapper: load markdown file, send as HTML email via Outlook SMTP, return success/failure
- [ ] `src/main.py` - poll loop (hourly via `schedule`), load config, scan `letters_dir`, call scheduler + sender, log to `data/logs/deliveries.csv`
- [ ] `config/requirements.txt` - freeze: `futuremail`, `schedule`, `pyyaml`
- [ ] End-to-end test: create `test-letter-SEND-<tomorrow>.md`, run daemon, verify email received + header updated + log written

## Phase 2 - Quality

- [ ] Retry logic for failed sends (3 attempts, exponential backoff)
- [ ] Multiple recipient support (`recipients.alt` list in config)
- [ ] Dashboard: print upcoming scheduled letters and sent history on startup
- [ ] Export log entries back to workspace archive on delivery

## Phase 3 - Polish

- [ ] HTML template customization (custom CSS wrapper around the converted markdown)
- [ ] Calendar integration - surface upcoming sends in a task list or notification
- [ ] Signature detection (parse "Love, David" style closings, treat separately from body)
- [ ] "Letter sent!" desktop notification at send time

---

## Decisions (locked)

| Decision | Choice | Reason |
|----------|--------|--------|
| SMTP provider | Outlook (primary) | Already used; app passwords supported |
| Persistence | Filesystem only for MVP | Letter file exists = pending; `Status: Delivered` header = done. SQLite only if this proves insufficient |
| Timezone | Australia/Perth (AWST, UTC+8) | User timezone |
| Email format | Markdown -> HTML via futuremail | Nice rendering in inbox |
| Retry | Phase 2 | MVP ships without it |
| Startup | Manual terminal run (like StreamPilot) | No tray needed for MVP |
| Sending layer | `futuremail` pip package + `schedule` | Handles markdown->HTML + SMTP. Do not reinvent |
| Scheduling layer | Novel part - this daemon IS the scheduler | Existing futuremail libs are sending-only |
| Poll frequency | Hourly | Low enough to not spin, accurate enough for daily sends |
