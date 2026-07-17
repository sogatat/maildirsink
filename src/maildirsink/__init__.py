"""maildirsink — SMTP でメールを受け取り Maildir / JSON に保存するだけのツール。"""

from __future__ import annotations

__version__ = "0.1.0"

from .storage import JsonStorage, MaildirStorage, Storage

__all__ = ["Storage", "MaildirStorage", "JsonStorage", "__version__"]
