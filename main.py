"""
ToxicUB - Main Entry Point
============================
Self-healing Pyrogram UserBot for Render / VPS.
"""

import patches  # noqa: F401 — MUST be first

import os
import sys
import time
import fcntl
import signal
import asyncio
import logging
import threading
import traceback
from datetime import datetime

from config import Config
from plugins import load_plugins, CMD_LIST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ToxicUB")

START_TIME = time.time()
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".toxicub.lock")


class InstanceLock:
    def __init__(self):
        self._fd = None

    def acquire(self):
        try:
            self._fd = open(LOCK_FILE, "w")
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd.write(f"{os.getpid()}\n")
            self._fd.flush()
            return True
        except OSError:
            self._fd = None
            return False

    def release(self):
        if self._fd:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                self._fd.close()
            except Exception:
                pass
            self._fd = None
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass


def _run_web_server():
    try:
        from flask import Flask, jsonify
        from werkzeug.serving import make_server

        app = Flask(__name__)

        @app.route("/")
        def home():
            return jsonify({
                "status": "alive", "bot": Config.BOT_NAME,
                "version": Config.BOT_VERSION,
                "uptime": round(time.time() - START_TIME, 2),
                "commands": sum(len(v) for v in CMD_LIST.values()),
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            })

        @app.route("/health")
        def health():
            return jsonify({"status": "ok"})

        port = int(os.getenv("PORT", Config.PORT))
        server = make_server("0.0.0.0", port, app)
        logger.info("Health server on port %d", port)
        server.serve_forever()
    except Exception as e:
        logger.error("Health server failed: %s", e)


def create_client():
    from pyrogram import Client
    return Client(
        name="ToxicUB",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.STRING_SESSION,
        app_version=f"{Config.BOT_NAME} {Config.BOT_VERSION}",
        device_model=f"{Config.BOT_NAME} Server",
        system_version=f"Python {sys.version_info.major}.{sys.version_info.minor}",
        sleep_threshold=10,
        max_concurrent_transmissions=5,
    )


class ToxicBot:
    def __init__(self):
        self.client = None
        self.restart_attempts = 0
        self.total_restarts = 0
        self._plugins_loaded = False
        self._stop = False

    @staticmethod
    def _backoff(attempts, base, maximum):
        import random
        delay = min(base * (2 ** attempts), maximum)
        return delay + random.uniform(0, delay * 0.25)

    def _uptime(self):
        s = int(time.time() - START_TIME)
        d, r = divmod(s, 86400)
        h, r = divmod(r, 3600)
        m, s = divmod(r, 60)
        return f"{d}d {h}h {m}m {s}s"

    async def _log(self, text):
        if self.client and Config.LOG_GROUP:
            try:
                await self.client.send_message(Config.LOG_GROUP, text)
            except Exception:
                pass

    async def _start(self):
        self.client = create_client()
        if not self._plugins_loaded:
            load_plugins(self.client)
            self._plugins_loaded = True
        await self.client.start()
        me = await self.client.get_me()
        logger.info("Logged in as %s (@%s) [ID: %s]", me.first_name, me.username, me.id)
        return me

    async def _stop_client(self):
        if self.client:
            try:
                await self.client.stop()
            except Exception:
                pass
            self.client = None

    async def run(self):
        from pyrogram.errors import ApiIdInvalid, AuthKeyDuplicated

        threading.Thread(target=_run_web_server, daemon=True).start()

        while not self._stop:
            try:
                me = await self._start()
                total = sum(len(v) for v in CMD_LIST.values())
                logger.info("Bot running — %d commands ready.", total)

                if self.restart_attempts > 0:
                    self.restart_attempts = 0

                if Config.LOG_GROUP:
                    await self._log(
                        f"**{Config.BOT_NAME} v{Config.BOT_VERSION} Started**\n"
                        f"**User:** {me.first_name} (@{me.username or 'N/A'})\n"
                        f"**Commands:** {total}\n"
                        f"**Restart #{self.total_restarts}**"
                    )

                try:
                    await self.client.idle()
                except (KeyboardInterrupt, SystemExit):
                    self._stop = True
                    break

                if self._stop:
                    break

                self.restart_attempts += 1
                self.total_restarts += 1
                d = self._backoff(self.restart_attempts, Config.RECONNECT_DELAY_BASE, Config.RECONNECT_DELAY_MAX)
                logger.warning("Disconnected. Reconnecting in %.1fs (attempt %d/%d)",
                               d, self.restart_attempts, Config.MAX_RESTART_ATTEMPTS)
                await self._log(f"**Reconnecting** ({self.restart_attempts}/{Config.MAX_RESTART_ATTEMPTS}) — wait {d:.0f}s")
                await self._stop_client()
                await asyncio.sleep(d)

            except (ApiIdInvalid, AuthKeyDuplicated) as e:
                logger.error("FATAL config error: %s", e)
                return

            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Crash:\n%s", tb)

                err = str(e).lower()
                if any(k in err for k in ("session revoked", "user deactivated", "banned")):
                    logger.error("FATAL: %s", e)
                    return

                self.restart_attempts += 1
                self.total_restarts += 1

                if self.restart_attempts >= Config.MAX_RESTART_ATTEMPTS:
                    logger.error("Max restarts reached (%d).", Config.MAX_RESTART_ATTEMPTS)
                    return

                d = self._backoff(self.restart_attempts, Config.RESTART_BACKOFF_BASE, Config.RESTART_BACKOFF_MAX)
                logger.warning("Crash #%d. Restart in %.1fs (attempt %d/%d)",
                               self.total_restarts, d, self.restart_attempts, Config.MAX_RESTART_ATTEMPTS)
                await self._log(f"**Crash Recovery** `{e}` — restart in {d:.0f}s")
                await self._stop_client()
                await asyncio.sleep(d)

    async def shutdown(self):
        self._stop = True
        if self.client:
            try:
                await self._log(f"**{Config.BOT_NAME} Stopped** | uptime: {self._uptime()}")
            except Exception:
                pass
        await self._stop_client()
        logger.info("Shutdown complete.")


def main():
    if not Config.validate():
        logger.error("Missing env vars: %s", ", ".join(Config.missing_vars()))
        sys.exit(1)

    lock = InstanceLock()
    if not lock.acquire():
        logger.error("Another instance is already running.")
        sys.exit(1)

    logger.info("%s v%s starting (Python %d.%d.%d)",
                Config.BOT_NAME, Config.BOT_VERSION,
                sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

    bot = ToxicBot()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def on_signal(sig, _):
        logger.info("Signal %s received", sig)
        loop.call_soon_threadsafe(lambda: asyncio.ensure_future(bot.shutdown()))

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    try:
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("Fatal: %s\n%s", e, traceback.format_exc())
    finally:
        try:
            loop.run_until_complete(bot.shutdown())
        except Exception:
            pass
        try:
            loop.close()
        except Exception:
            pass
        lock.release()


if __name__ == "__main__":
    main()
