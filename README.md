# ToxicUB

**Production-grade Pyrogram UserBot — 600+ commands, self-healing, fully isolated plugins.**

## Deploy to Render

1. Fork this repo
2. Get API credentials from [my.telegram.org/apps](https://my.telegram.org/apps)
3. Generate session: `pip3 install -r requirements.txt && python3 generate_session.py`
4. Deploy on Render as a Web Service. Set these env vars:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API Hash |
| `STRING_SESSION` | Yes | Pyrogram string session |
| `BOT_PREFIX` | No | Command prefix (default: `.`) |
| `LOG_GROUP` | No | Chat ID for logs |
| `SUDO_USERS` | No | Space-separated user IDs |

## Local Setup

```bash
git clone https://github.com/SegsyToxic-95/ToxicUB.git && cd ToxicUB
pip3 install -r requirements.txt
python3 generate_session.py
cp .env.sample .env
python3 main.py
```

## Features

- Self-healing with exponential backoff
- Single-instance lock (no duplicate sessions)
- Multi-prefix commands (`.help` / `/help` / `!help`)
- Plugin isolation — one crash never stops others
- Flask health server (never blocks the bot)
- Python 3.12+ / 3.13+ / 3.14+ compatible
- Graceful SIGTERM/SIGINT shutdown

## Commands

Type `.help` to see all 600+ commands across 9 categories.

---

For educational purposes only. Use responsibly.
