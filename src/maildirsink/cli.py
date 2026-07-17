"""コマンドラインインターフェース。"""

from __future__ import annotations

import argparse
import logging
from typing import Optional, Sequence

from . import __version__
from .server import serve
from .storage import create_storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maildirsink",
        description="SMTP でメールを受け取り Maildir / JSON に保存するだけのツール。",
    )
    parser.add_argument("--port", type=int, default=1025, help="SMTP 待ち受けポート (既定: 1025)")
    parser.add_argument(
        "--host",
        default="localhost",
        help="待ち受けホスト。LAN に公開するなら 0.0.0.0 を指定 (既定: localhost)",
    )
    parser.add_argument(
        "--format",
        choices=["maildir", "json"],
        default="maildir",
        help="保存形式 (既定: maildir)",
    )
    parser.add_argument(
        "--dir",
        default="./mail",
        help="保存先ディレクトリ (既定: ./mail)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    storage = create_storage(args.format, args.dir)
    serve(storage, args.host, args.port)
    return 0
