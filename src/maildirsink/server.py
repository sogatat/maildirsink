"""aiosmtpd を使った SMTP 受信サーバー。受けたメールを Storage に渡すだけ。"""

from __future__ import annotations

import logging
import threading
from email import message_from_bytes

from aiosmtpd.controller import Controller

from .storage import Storage

log = logging.getLogger("maildirsink")


class SinkHandler:
    """受信した DATA を Storage に保存するだけのハンドラ。"""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def handle_DATA(self, server, session, envelope):  # noqa: N802 (aiosmtpd の規約名)
        raw = envelope.content
        if isinstance(raw, str):
            raw = raw.encode("utf-8", errors="surrogateescape")
        message = message_from_bytes(raw)
        try:
            key = self.storage.store(message, raw)
        except Exception:
            log.exception("failed to store message")
            return "451 Requested action aborted: local error in processing"
        log.info("saved: %s", key)
        return "250 Message accepted for delivery"


def serve(storage: Storage, host: str, port: int) -> None:
    """SMTP サーバーを起動し、Ctrl-C まで待ち受ける。"""
    handler = SinkHandler(storage)
    controller = Controller(handler, hostname=host, port=port)
    controller.start()
    log.info("listening on %s:%d", controller.hostname, controller.port)
    stop = threading.Event()
    try:
        stop.wait()
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        controller.stop()
