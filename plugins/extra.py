"""
ToxicUB - Extra Plugin
========================
New features merged in from the second uploaded userbot script:
  - AFK auto-responder (with a per-user ignore list)
  - Runtime SUDO_USERS management (persisted to disk)
  - Antidelete (resend your own messages if you delete them)
  - Text-to-speech (.tts)

Note: several features from that script were intentionally NOT ported here.
See README.md -> "What was left out" for the reasons why.
"""


def register(app):
    from pyrogram import filters
    from pyrogram.types import Message
    from plugins import register_command, load_json, save_json
    from config import Config
    import time
    import os
    import tempfile

    # ── AFK ──────────────────────────────────────────────────────────────
    _afk = {"on": False, "reason": "", "since": 0}
    _ignored = set(load_json("ignored_users", []))
    _afk_replied = {}  # chat_id -> last reply timestamp, to avoid spamming a chat

    def _save_ignored():
        save_json("ignored_users", list(_ignored))

    @app.on_message(filters.command("afk") & filters.me)
    async def afk_cmd(client, message: Message):
        args = message.text.split(None, 1)
        reason = args[1] if len(args) > 1 else "AFK"
        _afk["on"] = True
        _afk["reason"] = reason
        _afk["since"] = time.time()
        _afk_replied.clear()
        await message.edit(f"💤 **AFK set:** {reason}")

    register_command("Extra", "afk", "Set yourself as AFK with an optional reason", [])

    @app.on_message(filters.command("unafk") & filters.me)
    async def unafk_cmd(client, message: Message):
        if not _afk["on"]:
            await message.edit("❌ You're not AFK.")
            return
        dur = int(time.time() - _afk["since"])
        _afk["on"] = False
        _afk["reason"] = ""
        await message.edit(f"✅ **Welcome back!** You were AFK for {dur}s.")

    register_command("Extra", "unafk", "Clear your AFK status", [])

    @app.on_message(filters.command("ignore") & filters.me)
    async def ignore_cmd(client, message: Message):
        if not message.reply_to_message:
            await message.edit("❌ Reply to a user's message to ignore them.")
            return
        uid = message.reply_to_message.from_user.id
        _ignored.add(uid)
        _save_ignored()
        await message.edit(f"🔇 **Ignoring** `{uid}` for AFK auto-replies.")

    register_command("Extra", "ignore", "Stop AFK auto-replies to a user (reply to their message)", [])

    @app.on_message(filters.command("unignore") & filters.me)
    async def unignore_cmd(client, message: Message):
        if not message.reply_to_message:
            await message.edit("❌ Reply to a user's message to unignore them.")
            return
        uid = message.reply_to_message.from_user.id
        _ignored.discard(uid)
        _save_ignored()
        await message.edit(f"🔊 **No longer ignoring** `{uid}`.")

    register_command("Extra", "unignore", "Re-enable AFK auto-replies to a user (reply to their message)", [])

    @app.on_message(filters.command("ignorelist") & filters.me)
    async def ignorelist_cmd(client, message: Message):
        if not _ignored:
            await message.edit("📋 **Ignore list is empty.**")
            return
        text = "📋 **Ignored users (no AFK auto-reply):**\n\n"
        text += "\n".join(f"  • `{uid}`" for uid in sorted(_ignored))
        await message.edit(text)

    register_command("Extra", "ignorelist", "Show users on the AFK ignore list", [])

    # Auto-reply to incoming messages while AFK, at most once per chat per AFK session.
    @app.on_message(filters.incoming & filters.private & ~filters.me, group=5)
    async def afk_autoreply(client, message: Message):
        if not _afk["on"]:
            return
        if not message.from_user or message.from_user.id in _ignored:
            return
        chat_id = message.chat.id
        if chat_id in _afk_replied:
            return
        _afk_replied[chat_id] = time.time()
        try:
            await client.send_message(
                chat_id,
                f"💤 **I'm currently AFK:** {_afk['reason']}\n"
                f"_Away since {int(time.time() - _afk['since'])}s ago. I'll reply when I'm back._",
            )
        except Exception:
            pass

    # ── Runtime SUDO_USERS management (persisted) ──────────────────────
    _sudo = set(load_json("sudo_users", list(Config.SUDO_USERS)))

    def _save_sudo():
        save_json("sudo_users", list(_sudo))
        Config.SUDO_USERS = list(_sudo)

    @app.on_message(filters.command("addsudo") & filters.me)
    async def addsudo_cmd(client, message: Message):
        if not message.reply_to_message and len(message.text.split()) < 2:
            await message.edit("❌ Reply to a user or pass their user ID.")
            return
        if message.reply_to_message:
            uid = message.reply_to_message.from_user.id
        else:
            try:
                uid = int(message.text.split(None, 1)[1])
            except ValueError:
                await message.edit("❌ Invalid user ID.")
                return
        _sudo.add(uid)
        _save_sudo()
        await message.edit(f"✅ **Added** `{uid}` **to sudo users.**")

    register_command("Extra", "addsudo", "Grant a user sudo access (reply or pass ID)", [])

    @app.on_message(filters.command("delsudo") & filters.me)
    async def delsudo_cmd(client, message: Message):
        if not message.reply_to_message and len(message.text.split()) < 2:
            await message.edit("❌ Reply to a user or pass their user ID.")
            return
        if message.reply_to_message:
            uid = message.reply_to_message.from_user.id
        else:
            try:
                uid = int(message.text.split(None, 1)[1])
            except ValueError:
                await message.edit("❌ Invalid user ID.")
                return
        _sudo.discard(uid)
        _save_sudo()
        await message.edit(f"✅ **Removed** `{uid}` **from sudo users.**")

    register_command("Extra", "delsudo", "Revoke a user's sudo access (reply or pass ID)", [])

    @app.on_message(filters.command("sudolist") & filters.me)
    async def sudolist_cmd(client, message: Message):
        if not _sudo:
            await message.edit("📋 **No sudo users set.**")
            return
        text = "📋 **Sudo users:**\n\n" + "\n".join(f"  • `{uid}`" for uid in sorted(_sudo))
        await message.edit(text)

    register_command("Extra", "sudolist", "List current sudo users", [])

    # ── Antidelete: resend your own messages if you delete them ────────
    _antidel_on = {"state": load_json("antidel_state", {"on": False}).get("on", False)}
    _msg_cache = {}  # message_id -> (chat_id, text_or_None)
    _MAX_CACHE = 500

    @app.on_message(filters.me, group=6)
    async def _cache_own_message(client, message: Message):
        if not _antidel_on["state"]:
            return
        if len(_msg_cache) > _MAX_CACHE:
            for k in list(_msg_cache.keys())[: _MAX_CACHE // 2]:
                _msg_cache.pop(k, None)
        _msg_cache[message.id] = (message.chat.id, message.text or message.caption or "[non-text message]")

    @app.on_message(filters.command("antidel") & filters.me)
    async def antidel_cmd(client, message: Message):
        args = message.text.split(None, 1)
        if len(args) < 2 or args[1].lower() not in ("on", "off"):
            state = "ON" if _antidel_on["state"] else "OFF"
            await message.edit(f"🛡 **Antidelete is currently {state}.**\nUsage: `.antidel <on|off>`")
            return
        _antidel_on["state"] = args[1].lower() == "on"
        save_json("antidel_state", {"on": _antidel_on["state"]})
        if not _antidel_on["state"]:
            _msg_cache.clear()
        await message.edit(f"🛡 **Antidelete turned {args[1].upper()}.**")

    register_command(
        "Extra", "antidel",
        "Resend your own messages to Saved Messages if deleted (.antidel on|off)", [],
    )

    try:
        from pyrogram.handlers import DeletedMessagesHandler

        async def _on_deleted(client, messages):
            if not _antidel_on["state"]:
                return
            for m in messages:
                cached = _msg_cache.pop(m.id, None)
                if not cached:
                    continue
                chat_id, text = cached
                try:
                    await client.send_message(
                        "me",
                        f"🛡 **Deleted message detected**\nChat: `{chat_id}`\n\n{text}",
                    )
                except Exception:
                    pass

        app.add_handler(DeletedMessagesHandler(_on_deleted))
    except ImportError:
        pass

    # ── Text-to-speech ──────────────────────────────────────────────────
    @app.on_message(filters.command("tts") & filters.me)
    async def tts_cmd(client, message: Message):
        args = message.text.split(None, 1)
        text = args[1] if len(args) > 1 else None
        if not text and message.reply_to_message:
            text = message.reply_to_message.text or message.reply_to_message.caption
        if not text:
            await message.edit("❌ **Usage:** `.tts <text>` (or reply to a text message)")
            return
        try:
            from gtts import gTTS
        except ImportError:
            await message.edit(
                "❌ **gTTS isn't installed.** Run `pip install gTTS` and add it to requirements.txt."
            )
            return
        await message.edit("🔊 **Generating speech...**")
        out_path = os.path.join(tempfile.gettempdir(), f"tts_{message.id}.mp3")
        try:
            gTTS(text=text[:1000], lang="en").save(out_path)
            await client.send_voice(message.chat.id, out_path)
            await message.delete()
        except Exception as e:
            await message.edit(f"❌ **TTS failed:** `{e}`")
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    register_command("Extra", "tts", "Convert text to a voice message (reply or pass text)", [])
