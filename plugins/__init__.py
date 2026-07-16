"""
ToxicUB - Plugin System
========================
Dynamic plugin loader with multi-prefix support and full error isolation.
"""

import os
import sys
import json
import logging
import importlib
import traceback
from typing import Dict, List, Any

logger = logging.getLogger("ToxicUB.Plugins")

CMD_LIST: Dict[str, List[Dict[str, Any]]] = {}
_loaded = False

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_json(name: str, default):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(name: str, data) -> bool:
    path = os.path.join(DATA_DIR, f"{name}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def register_command(category: str, name: str, help_text: str, aliases: List[str] = None):
    if category not in CMD_LIST:
        CMD_LIST[category] = []
    CMD_LIST[category].append({
        "name": name,
        "aliases": aliases or [],
        "help": help_text,
    })


def _patch_filters_command():
    """Patch pyrogram.filters.command to support . / ! prefixes by default.

    Called AFTER pyrogram is fully imported so the patch is safe and reliable.
    Every filters.command("xxx") call in every plugin will now match
    .xxx  /xxx  and  !xxx  automatically.
    """
    try:
        from pyrogram import filters as _f

        _orig_cmd = _f.command

        @staticmethod
        def _multi_prefix_cmd(commands, prefixes=None, case_sensitive=False):
            if prefixes is None:
                prefixes = [".", "/", "!"]
            return _orig_cmd(commands, prefixes=prefixes, case_sensitive=case_sensitive)

        _f.command = _multi_prefix_cmd
        logger.info("Patched filters.command -> multi-prefix [., /, !]")
    except Exception as e:
        logger.error("Failed to patch filters.command: %s", e)


def load_plugins(app):
    """Load all plugins with full error isolation and multi-prefix support."""
    global _loaded
    if _loaded:
        logger.info("Plugins already loaded, skipping.")
        return
    _loaded = True

    # Patch filters.command BEFORE loading any plugin
    _patch_filters_command()

    plugins_dir = os.path.dirname(os.path.abspath(__file__))
    loaded = 0
    failed = 0

    priority = ["extra", "admin", "core", "fun", "media", "naughty",
                "spam", "system", "text", "tools"]

    plugin_files = sorted(
        f for f in os.listdir(plugins_dir)
        if f.endswith(".py") and f != "__init__.py" and not f.startswith("_")
    )

    def _sort_key(f):
        stem = f[:-3]
        try:
            return priority.index(stem)
        except ValueError:
            return len(priority)

    plugin_files.sort(key=_sort_key)

    for filename in plugin_files:
        module_name = f"plugins.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                module.register(app)
                loaded += 1
                logger.info("Loaded: %s", module_name)
            else:
                logger.debug("Skipped (no register): %s", module_name)
        except Exception as e:
            failed += 1
            logger.error("FAILED: %s — %s", module_name, e)
            logger.debug(traceback.format_exc())

    total = sum(len(v) for v in CMD_LIST.values())
    logger.info("Plugins: %d loaded, %d failed | %d total commands", loaded, failed, total)
    for cat, cmds in sorted(CMD_LIST.items()):
        logger.info("  %s: %d commands", cat, len(cmds))
