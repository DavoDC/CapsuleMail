# Ideas & Future Work

Completed items -> `HISTORY.md`.

---

## MVP (implement first)

- [x] `src/scheduler.py` - filename parser, date comparison, state tracking (18 tests passing)
- [x] `src/sender.py` - markdown->HTML via `markdown` pkg, SMTP via smtplib (Outlook/Gmail)
- [x] `src/main.py` - hourly poll loop + daily send at configured time, delivery log
- [x] `config/requirements.txt` - schedule, pyyaml, markdown
- [ ] **End-to-end test** - create `config/config.yaml` with real credentials, create `test-letter-SEND-<tomorrow>.md` in letters_dir, run `python src/main.py`, temporarily set send_time to now+2min, verify email received + `Status: Delivered` header in file + log entry written

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
