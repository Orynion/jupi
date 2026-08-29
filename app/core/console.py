"""
Console encoding helpers for Windows.

On Windows, the default console encoding is often cp1252 or IBM437, which
cannot encode emoji (Saturnia likes to use 🪐, 👋, 👀, etc.) or other
non-BMP characters. When `print()` tries to write those characters, it raises
`UnicodeEncodeError` and the program crashes.

This module reconfigures stdout/stderr to UTF-8 and provides a `safe_print`
that survives even on terminals where the reconfigure doesn't take effect
(e.g. legacy PowerShell with `IBM437`).
"""

import sys


def _reconfigure_to_utf8():
    """Try to reconfigure stdout/stderr to UTF-8. No-op on streams that
    don't support reconfiguration (e.g. captured pipes in some setups)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Don't let a reconfigure failure take down the program.
            pass


def safe_print(*args, **kwargs):
    """Print that won't crash on emoji / non-ASCII output.

    Behaves like the built-in `print` but:
      - Replaces characters the terminal can't render with `?`
        rather than raising `UnicodeEncodeError`.
      - Falls back to ASCII if even UTF-8 encoding fails.
    """
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    file = kwargs.get("file", sys.stdout)
    flush = kwargs.get("flush", False)

    text = sep.join(str(a) for a in args)

    if file is None:
        file = sys.stdout

    try:
        file.write(text + end)
        if flush:
            try:
                file.flush()
            except Exception:
                pass
    except UnicodeEncodeError:
        # Final fallback: write the text in ASCII, dropping unsupported chars.
        try:
            ascii_text = text.encode("ascii", errors="replace").decode("ascii")
        except Exception:
            ascii_text = "[unprintable response]"
        try:
            file.write(ascii_text + end)
        except Exception:
            # Nothing more we can do.
            pass


# Reconfigure on import. Any module that does `from app.core.console import
# safe_print` (or anything else) implicitly triggers this, which is fine.
_reconfigure_to_utf8()
