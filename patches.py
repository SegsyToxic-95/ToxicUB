"""
ToxicUB - Monkey Patches for Python 3.13+ Compatibility
=========================================================
MUST be imported before any other third-party library.
Recreates removed stdlib modules that Pyrogram/dependencies rely on.
"""

import sys
import types
import warnings

# ── Patch `cgi` – removed in Python 3.13 (PEP 594) ──────────
if sys.version_info >= (3, 13):
    try:
        import cgi  # noqa: F401
    except ImportError:
        from email.message import Message as _EmailMessage

        class _CgiModule(types.ModuleType):
            def parse_header(self, string):
                if not string:
                    return "", {}
                msg = _EmailMessage()
                msg["content-type"] = string
                params = msg.get_params(failobj={})
                if isinstance(params, list):
                    main = params[0][0] if params[0] else ""
                    param_dict = {}
                    for pair in params[1:]:
                        if len(pair) >= 2:
                            param_dict[pair[0].lower()] = pair[1]
                    return main, param_dict
                return string, {}

        sys.modules["cgi"] = _CgiModule("cgi")


# ── Patch `audioop` – removed in Python 3.13 (PEP 594) ──────
if sys.version_info >= (3, 13):
    try:
        import audioop  # noqa: F401
    except ImportError:
        class _AudioopModule(types.ModuleType):
            error = Exception
            def add(self, f1, f2, w): return f1
            def bias(self, f, w, b): return f
            def byteswap(self, f, w): return f
            def cross(self, f, w): return 0
            def findfactor(self, f, r): return 1.0
            def findfit(self, f, r): return (0, 0.0)
            def findmax(self, f, w): return 0
            def getsample(self, f, w, i): return 0
            def lin2lin(self, f, w, nw): return f
            def lin2alaw(self, f, w): return f[: len(f) // w]
            def lin2ulaw(self, f, w): return f[: len(f) // w]
            def alaw2lin(self, f, w): return f
            def ulaw2lin(self, f, w): return f
            def minmax(self, f, w): return (0, 0)
            def mul(self, f, w, factor): return f
            def ratecv(self, f, w, ch, ir, or_, s, wA=1, wB=0): return (f, (0, 0.0))
            def reverse(self, f, w): return f
            def rms(self, f, w): return 0
            def tomono(self, f, w, lf, rf): return f[: len(f) // 2]
            def tostereo(self, f, w, lf, rf): return f * 2

        sys.modules["audioop"] = _AudioopModule("audioop")


# ── Patch `imghdr` – removed in Python 3.13 (PEP 594) ───────
if sys.version_info >= (3, 13):
    try:
        import imghdr  # noqa: F401
    except ImportError:
        class _ImghdrModule(types.ModuleType):
            def what(self, file, h=None):
                if h is None:
                    if hasattr(file, "read"):
                        h = file.read(32)
                    else:
                        with open(file, "rb") as fh:
                            h = fh.read(32)
                if h[:8] == b"\x89PNG\r\n\x1a\n": return "png"
                if h[:2] == b"\xff\xd8": return "jpeg"
                if h[:4] == b"GIF8": return "gif"
                if h[:4] == b"RIFF" and h[8:12] == b"WEBP": return "webp"
                if h[:2] == b"BM": return "bmp"
                return None
            tests = []
        sys.modules["imghdr"] = _ImghdrModule("imghdr")


# ── Patch `shelve` – removed in Python 3.13 (PEP 594) ────────
if sys.version_info >= (3, 13):
    try:
        import shelve  # noqa: F401
    except ImportError:
        class _ShelveModule(types.ModuleType):
            class _Shelf:
                def __init__(self, *a, **kw): self._d = {}
                def __getitem__(self, k): return self._d[k]
                def __setitem__(self, k, v): self._d[k] = v
                def __delitem__(self, k): del self._d[k]
                def __contains__(self, k): return k in self._d
                def __enter__(self): return self
                def __exit__(self, *a): self.close()
                def close(self): pass
                def sync(self): pass
                def get(self, k, d=None): return self._d.get(k, d)
                def keys(self): return self._d.keys()
                def items(self): return self._d.items()
            def open(self, *a, **kw): return self._Shelf()
        sys.modules["shelve"] = _ShelveModule("shelve")


# ── Patch `pipes` – removed in Python 3.13 (PEP 594) ─────────
if sys.version_info >= (3, 13):
    try:
        import pipes  # noqa: F401
    except ImportError:
        class _PipesModule(types.ModuleType):
            def quote(self, s):
                return "'" + s.replace("'", "'\\''") + "'"
        sys.modules["pipes"] = _PipesModule("pipes")


# ── Patch asyncio.get_event_loop for Python 3.10+ ────────────
# Pyrogram's sync module calls asyncio.get_event_loop() at import time,
# which raises RuntimeError in Python 3.10+ when no loop exists.
import asyncio as _asyncio

_orig_get_event_loop = _asyncio.get_event_loop

def _safe_get_event_loop():
    try:
        loop = _orig_get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
        return loop
    except RuntimeError:
        loop = _asyncio.new_event_loop()
        _asyncio.set_event_loop(loop)
        return loop

_asyncio.get_event_loop = _safe_get_event_loop

# ── Suppress deprecation warnings from pyrogram/asyncio ──────
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*get_event_loop.*")
