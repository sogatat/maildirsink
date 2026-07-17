"""storage モジュールのテスト（aiosmtpd 不要で完結する）。"""

from __future__ import annotations

import json
from email.message import EmailMessage

from maildirsink.storage import (
    JsonStorage,
    MaildirStorage,
    create_storage,
    decode_mime_header,
    extract_body,
)


def _sample_message() -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "テスト件名"
    msg["From"] = "sender@example.com"
    msg["To"] = "you@example.com"
    msg["Date"] = "Fri, 17 Jul 2026 08:48:00 +0900"
    msg["Message-ID"] = "<abc123@example.com>"
    msg.set_content("こんにちは\n本文です。")
    return msg


def test_decode_mime_header_b_encoded():
    # "テスト" を UTF-8 Base64 でエンコードしたもの
    encoded = "=?UTF-8?B?44OG44K544OI?="
    assert decode_mime_header(encoded) == "テスト"


def test_decode_mime_header_plain():
    assert decode_mime_header("plain text") == "plain text"
    assert decode_mime_header("") == ""


def test_extract_body_plain():
    msg = _sample_message()
    body = extract_body(msg)
    assert "こんにちは" in body
    assert "本文です。" in body


def test_extract_body_multipart_prefers_text_plain():
    msg = EmailMessage()
    msg["Subject"] = "multi"
    msg.set_content("プレーン本文")
    msg.add_alternative("<p>HTML本文</p>", subtype="html")
    body = extract_body(msg)
    assert "プレーン本文" in body


def test_maildir_storage_writes_to_new(tmp_path):
    storage = MaildirStorage(tmp_path / "mail")
    msg = _sample_message()
    key = storage.store(msg, msg.as_bytes())

    new_dir = tmp_path / "mail" / "new"
    files = list(new_dir.iterdir())
    assert len(files) == 1
    assert key  # キーが返る
    content = files[0].read_bytes()
    assert b"Subject" in content


def test_json_storage_fields(tmp_path):
    storage = JsonStorage(tmp_path / "json")
    msg = _sample_message()
    filename = storage.store(msg, msg.as_bytes())

    saved = (tmp_path / "json" / filename)
    assert saved.suffix == ".json"
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["subject"] == "テスト件名"
    assert data["from"] == "sender@example.com"
    assert data["to"] == "you@example.com"
    assert data["message_id"] == "<abc123@example.com>"
    assert "こんにちは" in data["body"]


def test_json_storage_unique_names(tmp_path):
    storage = JsonStorage(tmp_path / "json")
    msg = _sample_message()
    names = {storage.store(msg, msg.as_bytes()) for _ in range(5)}
    assert len(names) == 5  # 連番で衝突しない


def test_create_storage_dispatch(tmp_path):
    assert isinstance(create_storage("maildir", tmp_path / "a"), MaildirStorage)
    assert isinstance(create_storage("json", tmp_path / "b"), JsonStorage)
