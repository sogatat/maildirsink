"""受信メールの保存先。maildir / json の 2 形式を提供する。"""

from __future__ import annotations

import json
import mailbox
import os
import socket
import time
from email.header import decode_header, make_header
from email.message import Message
from pathlib import Path
from typing import Union

PathLike = Union[str, os.PathLike]


def decode_mime_header(value: str) -> str:
    """``=?UTF-8?B?...?=`` などの MIME エンコードヘッダをデコードする。"""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        # 壊れたヘッダでも保存自体は止めない
        return value


def extract_body(message: Message) -> str:
    """text/plain の本文を取り出してデコードする。無ければ最初のテキストを返す。"""
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue
            if part.get_content_type() == "text/plain":
                return _decode_part(part)
        # text/plain が無ければ最初の非マルチパートを本文として扱う
        for part in message.walk():
            if not part.is_multipart():
                return _decode_part(part)
        return ""
    return _decode_part(message)


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        result = part.get_payload()
        return result if isinstance(result, str) else ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


class Storage:
    """保存先の共通インターフェース。"""

    def store(self, message: Message, raw: bytes) -> str:
        """メールを保存し、生成したファイル名（またはキー）を返す。"""
        raise NotImplementedError


class MaildirStorage(Storage):
    """標準 Maildir 形式。``tmp/`` → ``new/`` の投函を ``mailbox.Maildir`` に任せる。"""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)
        # create=True で new/ cur/ tmp/ を用意する
        self._maildir = mailbox.Maildir(str(self.path), create=True)

    def store(self, message: Message, raw: bytes) -> str:
        msg = mailbox.MaildirMessage(raw)
        # info を付けずに new/ へ投函する（未読メール置き場）
        msg.set_subdir("new")
        return self._maildir.add(msg)


class JsonStorage(Storage):
    """1 メール 1 ファイルの JSON 保存。"""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._counter = 0

    def store(self, message: Message, raw: bytes) -> str:
        data = {
            "subject": decode_mime_header(message.get("Subject", "")),
            "from": decode_mime_header(message.get("From", "")),
            "to": decode_mime_header(message.get("To", "")),
            "date": message.get("Date", ""),
            "message_id": message.get("Message-ID", ""),
            "body": extract_body(message),
        }
        filename = self._unique_name()
        target = self.path / filename
        target.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return filename

    def _unique_name(self) -> str:
        # Maildir の命名規則にならった一意名（時刻.Pプロセス連番.ホスト名）
        self._counter += 1
        stamp = time.time()
        secs = int(stamp)
        micros = int((stamp - secs) * 1_000_000)
        host = socket.gethostname().replace("/", "-").replace(":", "-")
        return f"{secs}.M{micros}P{os.getpid()}Q{self._counter}.{host}.json"


def create_storage(fmt: str, path: PathLike) -> Storage:
    """``--format`` の値から保存先を生成する。"""
    if fmt == "maildir":
        return MaildirStorage(path)
    if fmt == "json":
        return JsonStorage(path)
    raise ValueError(f"unknown format: {fmt!r}")
