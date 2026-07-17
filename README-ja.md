# maildirsink

[![PyPI](https://img.shields.io/pypi/v/maildirsink)](https://pypi.org/project/maildirsink/)
[![Python](https://img.shields.io/pypi/pyversions/maildirsink)](https://pypi.org/project/maildirsink/)
[![License](https://img.shields.io/pypi/l/maildirsink)](https://github.com/sogatat/maildirsink/blob/main/LICENSE)

メールを受け取ってディスクに書くだけの小さな SMTP サーバー。保存先は標準 Maildir か JSON。
Web UI も転送機能もデータベースも持たない。やることは一つ、**受けて保存する**。

English version: [README.md](https://github.com/sogatat/maildirsink/blob/main/README.md)

## 何のために

メールを送るものを開発していると、その送信先が必要になる。本物の受信箱に飛ばすわけにはいかない。
[mailpit](https://github.com/axllent/mailpit) や MailHog はこれをブラウザで開く Web UI で解決する。

maildirsink は逆のアプローチを取る。**標準 Maildir に書いて、あとは黙る**。
出力がごく普通の Maildir なので:

- Maildir ネイティブな MUA（mutt / neomutt）で追加設定なしに読める
- 既存のツール群（procmail・mbsync など）をそのまま向けられる
- `ls` / `grep` / `cat` でも十分。1 メール 1 ファイルなので

覚えるべき UI もなければ、エクスポートすべき独自形式もない。
RFC 5322 のままより構造化データが欲しければ `--format json` を使えば、
1 メール 1 ファイルの JSON になる。

## クイックスタート

```bash
pipx install maildirsink          # または: pip install maildirsink
maildirsink --dir ~/Maildir
```

アプリの SMTP 設定を `localhost:1025` に向けて送信する。`~/Maildir/new/` に即座に現れる。

アプリを用意せず試すなら、Python から 1 通送ってみる:

```bash
python - <<'EOF'
import smtplib
from email.message import EmailMessage

m = EmailMessage()
m["Subject"] = "テスト"
m["From"] = "app@example.com"
m["To"] = "you@example.com"
m.set_content("届きました。")
smtplib.SMTP("localhost", 1025).send_message(m)
EOF
```

## インストール

```bash
pipx install maildirsink     # 推奨。隔離環境に入り、`maildirsink` が PATH に載る
pip install maildirsink      # 任意の venv に入れる場合
```

Python 3.9 以上が必要。

## 使い方

```bash
maildirsink [--port PORT] [--host HOST] [--format maildir|json] [--dir DIR]
```

| オプション | 意味 | 既定値 |
|---|---|---|
| `--port` | SMTP 待ち受けポート | 1025 |
| `--host` | 待ち受けホスト | localhost |
| `--format` | 保存形式（maildir / json） | maildir |
| `--dir` | 保存先ディレクトリ | `./mail` |

保存先ディレクトリは、存在しなければ起動時に作られる。

### LAN に公開する

既定の `localhost` は同一マシンからの送信しか受け付けない。別ホスト（コンテナや
別マシンのアプリ）から受けたい場合は、全インターフェースで待ち受ける:

```bash
maildirsink --host 0.0.0.0 --port 1025
```

> **警告:** maildirsink は認証も TLS も持たず、渡されたメールをすべて受け入れる。
> 信頼できるネットワーク内でのみ使うこと。インターネットには絶対に晒さない。

## 保存形式

### `--format maildir`（既定）

標準 Maildir。各メールは `tmp/` に書いてから `new/` に移動する
（この形式が要求する原子的な 2 段階配信）。ファイル名は一意性が保証される
`タイムスタンプ.Pプロセス識別子.ホスト名` 形式。

```
~/Maildir/
├── cur/
├── new/     ← 配信されたメールはここに落ちる
│   └── 1784265259.M961931P358986Q1.hostname
└── tmp/
```

`new/` は MUA が未読メールを探す場所そのものなので、追加設定なしに拾われる。

### `--format json`

1 メール 1 ファイルの JSON。メールを「読む」のではなくテストで検証したいとき向け。
ヘッダは MIME デコードされ、`text/plain` の本文が抽出される:

```json
{
  "subject": "テスト",
  "from": "app@example.com",
  "to": "you@example.com",
  "date": "Fri, 17 Jul 2026 08:48:00 +0900",
  "message_id": "<abc123@example.com>",
  "body": "届きました。\n"
}
```

## mutt / neomutt で読む

maildirsink の保存先を MUA に指定するだけ。設定はこれで全部:

```muttrc
set mbox_type = Maildir
set folder    = "/path/to/maildir"
set spoolfile = "+."
mailboxes     = "/path/to/maildir"

# 起動中に届いたメールも自動で拾う
set mail_check = 5      # 秒
set timeout    = 10
```

`new/` に落ちたメールは、mutt を開いたままでも自動的に反映される。

## 対応プラットフォーム

| プラットフォーム | 状況 |
|---|---|
| Linux | サポート |
| macOS | 動作するはず（常時テストはしていない） |
| Windows 11 + WSL2 | サポート（下記参照） |
| Windows（ネイティブ） | 非サポート |

Windows ネイティブは対象外。systemd が無く、Maildir ネイティブな MUA も現実的に使えないため。
WSL2 なら本物の Linux カーネルが動くので、maildirsink も下記の systemd ユニットも無改造で動く。

### Windows 11（WSL2）

WSL2 特有の注意点が 3 つ。

**1. systemd を有効化する。** 既定では無効。ディストロ内の `/etc/wsl.conf` に以下を書き、
Windows 側から `wsl --shutdown` で再起動する:

```ini
[boot]
systemd=true
```

**2. Maildir は Linux 側のファイルシステムに置く。** `~/Maildir` を使い、`/mnt/c/...` 配下には置かない。
Windows ドライブは drvfs 経由でマウントされており、Maildir が依存する `rename`/`link` の
アトミック性が保証されない上に遅い。

**3. ネットワーク。** WSL2 は既定で NAT の内側にいる。Windows 上のアプリから `localhost:1025` に
送る分には localhost forwarding で届くので、既定の設定のままで動く。LAN 上の他マシンから
受信したい場合、WSL2 の IP は起動ごとに変わる点に注意。Windows 11 22H2 以降なら
`%UserProfile%\.wslconfig` でミラーモードにすればこの問題は消える:

```ini
[wsl2]
networkingMode=mirrored
```

## サービスとして常駐させる（systemd --user）

毎回手で起動しなくて済むよう、`~/.config/systemd/user/maildirsink.service` を置く:

```ini
[Unit]
Description=maildirsink - SMTP sink saving mail to Maildir
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/maildirsink --host localhost --port 1025 --format maildir --dir %h/Maildir
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

上記の `ExecStart` は `pipx install maildirsink`（コマンドが `~/.local/bin` に入る）を前提にしている。
別の場所にインストールした場合は `<自分の venv>/bin/maildirsink` などに書き換える。

```bash
systemctl --user daemon-reload
systemctl --user enable --now maildirsink.service
systemctl --user status maildirsink        # 状態確認
journalctl --user -u maildirsink -f        # ログ追尾
```

これでログイン時に起動する。ログインしていなくても常駐させたい（OS 起動時から動かしたい）場合は
linger を有効化する:

```bash
sudo loginctl enable-linger "$USER"
```

## 仕組み

枯れたライブラリ 2 つの上に載った、200 行ほどの Python。

- **SMTP:** [`aiosmtpd`](https://github.com/aio-libs/aiosmtpd) — 標準の `smtpd` は
  Python 3.12 で削除済みのため。
- **Maildir:** 標準ライブラリの `mailbox.Maildir`。その `add()` が `tmp/` → `new/` の
  配信手順とファイル名の一意性規則を既に実装している。
- **ヘッダ:** MIME エンコードされたヘッダ（`=?UTF-8?B?...?=`）は JSON に入れる際にデコードする。
  壊れたヘッダはメールを捨てずに生の値へフォールバックする。

保存に失敗した場合は SMTP `451` を返して送信側にメールが保持されなかったことを伝え、
トレースバックをログに出す。

## 開発

```bash
git clone https://github.com/sogatat/maildirsink
cd maildirsink
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## ライセンス

MIT — [LICENSE](https://github.com/sogatat/maildirsink/blob/main/LICENSE) を参照。
