# CapsuleMail

Local scheduled email daemon. Polls a folder of `.md` files, sends them as HTML emails when their scheduled date is reached (parsed from the filename), and updates the file header with delivery status.

## Tech stack

- Python 3.x
- `futuremail` - markdown to HTML email via SMTP
- `schedule` - polling loop
- `pyyaml` - config file parsing

## Install

```
pip install -r config/requirements.txt
```

## Run

```
python src/main.py
```

Reads `config/config.yaml` (git-ignored, copy from `config/config.example.yaml`).

## Test

```
python -m pytest tests/ -v
```

## Key paths

- `src/scheduler.py` - filename parser, date logic, state tracking (header read/write)
- `src/sender.py` - futuremail wrapper (markdown -> HTML email via SMTP)
- `src/main.py` - poll loop entry point
- `config/config.example.yaml` - committed generic template
- `config/config.yaml` - real credentials (git-ignored, never commit)
- `data/logs/deliveries.csv` - delivery log (git-ignored)

## Filename convention

```
futureme-letter-WRITTEN-DATE-SEND-SENDDATE.md
Example: futureme-letter-2026-05-10-SEND-2027-05-10.md
```

The daemon parses the `SEND-YYYY-MM-DD` segment. Any `.md` file in `letters_dir` without this pattern is ignored.

## Safety rules

- Never commit `config/config.yaml` - it contains real credentials
- Never commit files from `data/` - logs and runtime state are local only
- Test emails use a real SMTP connection - verify in inbox before marking a feature done
