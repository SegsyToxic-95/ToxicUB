# ⚡ ToxicUB — The Ultimate Pyrogram UserBot

![ToxicUB](https://img.shields.io/badge/ToxicUB-2.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12%2B-green?style=for-the-badge)
![Commands](https://img.shields.io/badge/Commands-600%2B-orange?style=for-the-badge)

**A feature-packed Pyrogram UserBot with 600+ commands across 9 categories.**

---

## 🚀 Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Step-by-Step

1. **Fork this repo** to your GitHub account
2. **Get API credentials** from [https://my.telegram.org/apps](https://my.telegram.org/apps)
3. **Generate a String Session**: `pip install -r requirements.txt && python generate_session.py`
4. **Deploy on Render**: Create a Web Service, connect your repo, set env vars:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | Telegram API ID |
| `API_HASH` | ✅ | Telegram API Hash |
| `STRING_SESSION` | ✅ | Pyrogram string session |
| `PREFIX` | ❌ | Command prefix (default: `.`) |
| `LOG_GROUP` | ❌ | Chat ID for logs |

---

## 🖥️ Local Setup

```bash
git clone https://github.com/SegsyToxic-95/ToxicUB.git && cd KyrenUB
pip install -r requirements.txt
python generate_session.py
cp .env.sample .env  # Edit with your credentials
python main.py
```

---

## 📁 Project Structure

```
ToxicUB/
├── main.py              # Entry point + Flask web server
├── config.py            # Environment handler
├── patches.py           # Python 3.12+ monkey patches
├── generate_session.py  # Session generator
├── plugins/
│   ├── __init__.py      # Dynamic plugin loader + JSON persistence helpers
│   ├── core.py          # 34 commands
│   ├── admin.py         # 46 commands
│   ├── extra.py         # 10 commands  (NEW — see "What's new" below)
│   ├── fun.py           # 120 commands
│   ├── naughty.py       # 83 commands
│   ├── tools.py         # 119 commands
│   ├── text.py          # 134 commands
│   ├── spam.py          # 23 commands
│   ├── media.py         # 57 commands
│   └── system.py        # 56 commands
├── data/                # auto-created; stores notes/todos/sudo list/etc (gitignored)
├── .env.sample
├── .gitignore
├── requirements.txt
├── render.yml
└── README.md
```

---

## 🐍 Python 3.12+ Compatibility

`patches.py` is imported first and patches: `cgi`, `audioop`, `imghdr` (removed in 3.13), and `asyncio.get_event_loop` deprecation.

---

## 🆕 What's new — merge of the two uploaded projects

This build merges **NutzUB** (the zip, a Pyrogram bot — used as the base) with the
**second uploaded userbot.py** (a Telethon bot). The two use different frameworks, so
rather than pasting one into the other, unique/useful features from userbot.py were
rewritten as native Pyrogram plugins and dropped into the existing plugin system.

### New `.extra.py` plugin (10 commands)
| Command | What it does |
|---|---|
| `.afk [reason]` | Marks you AFK; auto-replies once per chat to incoming DMs while active |
| `.unafk` | Clears AFK status |
| `.ignore` / `.unignore` | Reply to a user to stop/resume AFK auto-replies to them |
| `.ignorelist` | Shows the AFK ignore list |
| `.addsudo` / `.delsudo` | Grant/revoke sudo access at runtime (reply or pass a user ID) |
| `.sudolist` | Shows current sudo users |
| `.antidel <on\|off>` | Resends your own deleted messages to Saved Messages |
| `.tts <text>` | Converts text (or a replied message) to a voice note |

### Bugs fixed
- **43 duplicate command names/aliases** existed across the original plugin files
  (e.g. `.reverse`, `.purge`, `.rot13`, `.contrast` were each bound in two or three
  plugins). Pyrogram would fire *every* matching handler on such a command, so these
  produced double/triple replies or unpredictable behavior. Each collision was
  resolved by keeping the command in the plugin it fits best and renaming the
  duplicate(s) with a short plugin-tag suffix (e.g. `.reverse` stays in `fun.py`;
  the `text.py` version is now `.reversetx`).
- **Notes and todos were never saved to disk** — a restart silently wiped them. Both
  now persist to `data/notes.json` and `data/todos.json`.

### 🔒 Security fix — hardcoded credentials removed
Both uploaded files shipped with **real-looking `API_ID`, `API_HASH`, and a full
`STRING_SESSION` baked in as default values** in `config.py`. A string session *is*
a login credential — anyone who reads that file (e.g. on a public GitHub repo) can
sign in as that Telegram account with zero further steps. This build removes every
hardcoded default; `API_ID` / `API_HASH` / `STRING_SESSION` are now required
environment variables with no fallback. **If you ever pushed the original file with
those values to a public place, treat that session as compromised and regenerate it.**

### 🚫 What was left out, and why
The second uploaded file also included several commands that were **not** ported:
- **Raid tools** (`.reply`/`.rr`/`.flag`/`.hrr`/`.god`-style commands) — these
  auto-reply or auto-react to *every message a targeted user sends*, which is a
  harassment tool aimed at another person, not a personal-use feature.
- **Profile "clone"** — copied another user's name, bio, username, and photo onto
  your account, which is straightforward identity impersonation.
- **Mass group creation ("fastgc")** and **mass bot-adding ("addbots")** — both are
  flood/spam infrastructure rather than personal utilities.

These sit well outside "bug fixing and merging features" and could get you (or
someone else) banned or genuinely hurt, so they were excluded rather than cleaned up.
Everything else useful was kept or improved.

---

For educational purposes only. Use responsibly and at your own risk. Telegram may ban accounts violating their ToS.

---

<div align="center">**ToxicUB** — Made with ⚡</div>
