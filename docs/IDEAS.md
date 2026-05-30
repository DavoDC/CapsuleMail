# Ideas & Future Work

Completed items -> `HISTORY.md`.

---

## Next (MVP gate)

- [ ] **End-to-end test** - create `config/config.yaml` with real credentials, drop a `test-letter-SEND-<tomorrow>.md` in `letters_dir`, temporarily set `send_time` to now+2min, run `python src/main.py`, verify: email received in inbox, HTML renders correctly, `Status: Delivered` header written back to file, log entry in `data/logs/deliveries.csv`

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
