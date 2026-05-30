# CapsuleMail

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/davodc)

Never manually copy-paste a letter into emailfuture.com again. CapsuleMail is a local daemon that watches a folder of markdown files and sends them as beautifully rendered HTML emails on their scheduled date - no SaaS dependency, no paid tier, no 1-year hard limit.

Write a letter, drop it in your folder with a send date in the filename, and forget about it. CapsuleMail handles the rest.

```
futureme-letter-2026-05-10-SEND-2031-05-10.md  ->  delivered 2031-05-10 at 09:00
```

---

## Why CapsuleMail?

Existing services fall short:

| Service | Problem |
|---------|---------|
| futureme.org | Now paid-only |
| emailfuture.com | Manual confirmation click required every time; dated UX |
| later.io | Free tier capped at 1-year max delay |
| Boomerang | Only delays existing drafts, no standalone scheduling |

CapsuleMail eliminates all of these: local storage, no account required, no delay limits, no subscriptions.

*Inspired by D-Mail from Steins;Gate.*

---

## Use cases

- Future-me letters (1 month, 1 year, 5 years out)
- Birthday and anniversary reminders to yourself
- Motivational notes timed to stressful future milestones
- Scheduled check-ins ("how did that project go?")
- Anything you want your future self to receive

---

## Install

```bash
pip install -r config/requirements.txt
```

Copy the config template and fill in your email credentials:

```bash
cp config/config.example.yaml config/config.yaml
# edit config/config.yaml with your SMTP settings
```

---

## Usage

**1. Write a letter** as a markdown file. Name it with the send date:

```
futureme-letter-2026-05-10-SEND-2027-05-10.md
```

Put it in the `letters_dir` folder you configured.

**2. Run the daemon:**

```bash
python src/main.py
```

CapsuleMail polls hourly. When the send date arrives, it converts your markdown to HTML and delivers it via your configured SMTP provider. The file gets a `Status: Delivered` header and a log entry is written to `data/logs/deliveries.csv`.

**3. Auto-start on login (optional):**

Create a shortcut to `scripts/start-capsulemail.bat` in your Windows startup folder (`Win+R` -> `shell:startup`). No registry, no Task Scheduler - just a shortcut.

---

## Configuration

See `config/config.example.yaml` for all options. Key settings:

```yaml
smtp:
  provider: outlook
  email: your.email@outlook.com
  app_password: "xxxx xxxx xxxx xxxx"

scheduling:
  send_time: "09:00"
  timezone: "Australia/Perth"

paths:
  letters_dir: "/path/to/your/scheduled/emails"
```

`config/config.yaml` is git-ignored - your credentials never leave your machine.

---

## Filename convention

```
futureme-letter-WRITTEN-DATE-SEND-SENDDATE.md
```

- `WRITTEN-DATE` - when you wrote it (YYYY-MM-DD)
- `SEND-SENDDATE` - when to deliver it (YYYY-MM-DD)

Any `.md` file without the `SEND-` pattern is ignored.

---

## License

MIT
