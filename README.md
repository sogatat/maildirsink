# maildirsink

SMTP でメールを受け取り、そのままファイルに保存するだけの小さなツール。
mailpit のような開発用メール受信ツールだが、UI も転送機能も持たず「受けて保存する」ことに徹する。

## 動機

[find-job](../find-job) プロジェクトでは、通知メールをシェルスクリプトで Maildir に直接書き込んでいた。
この「メールをローカルに保存する」部分だけを汎用ツールとして切り出したのが maildirsink。

保存先は **標準 Maildir** に徹する。Maildir をネイティブに扱う MUA（mutt / neomutt など）や
既存の Maildir ツール群（procmail・mbsync 等）とそのまま噛み合うのが狙い。

## 仕様

### 動作

1. 起動すると指定ポートで SMTP サーバーとして待ち受ける
2. メールを受信したら、指定ディレクトリに指定形式で保存する
3. それ以外のことはしない（転送しない・UIなし）

### 保存形式

- **maildir** — 標準 Maildir 形式。
  受信メールは `tmp/` に書き込んでから **`new/`**（未読メール置き場）に mv する。
  ファイル名は一意性を保証する標準命名（`時刻.Pプロセス識別子.ホスト名`）に従う。
  mutt / neomutt はこの `new/` を直接スキャンして新着を表示するため、追加設定は不要。

- **json** — 1メール1ファイルの JSON。最小構成:

  ```json
  {
    "subject": "件名",
    "body": "本文"
  }
  ```

  from / to / date なども入れるかは実装時に検討（入れる方向で考える）

> **補足:** Thunderbird 直配信はしない方針。Thunderbird は `.msf` サマリーキャッシュを持ち、
> 外部から Maildir に書き込んだメールを「フォルダ修復」まで認識しない。
> mutt など Maildir ネイティブの MUA にはこの問題が無く、`new/` への投函をそのまま検知する。

### CLI

```bash
maildirsink [--port PORT] [--host HOST] [--format maildir|json] [--dir DIR]
```

| オプション | 意味 | デフォルト |
|---|---|---|
| `--port` | SMTP 待ち受けポート | 1025 |
| `--host` | 待ち受けホスト | localhost |
| `--format` | 保存形式（maildir / json） | maildir |
| `--dir` | 保存先ディレクトリ | `./mail` |

### LAN に公開する

既定の `localhost` は同一ホストからの送信だけを受け付ける。別ホスト（コンテナや
LAN 上の find-job など）から送りたい場合は全インターフェースで待ち受ける:

```bash
maildirsink --host 0.0.0.0 --port 1025
```

> **注意:** 認証も TLS も持たないため、信頼できる LAN 内だけで使うこと。
> インターネットに直接晒さない。

## 表示側（mutt / neomutt）

maildirsink が出力した Maildir をそのまま指定するだけ。`.msf` のような
インデックスキャッシュを持たないため、修復操作は一切不要。

```muttrc
set mbox_type = Maildir
set folder    = "/path/to/maildir"
set spoolfile = "+."
mailboxes     = "/path/to/maildir"

# 起動中に届いたメールも自動で拾う
set mail_check = 5      # 秒
set timeout    = 10
```

`new/` にメールが落ちれば mutt 側に自動で反映される。

## 実装方針（案）

- Python を想定
  - SMTP サーバー: `aiosmtpd`（標準の `smtpd` は Python 3.12 で削除済み）
  - Maildir 書き込み: 標準ライブラリ `mailbox.Maildir` が使える。
    `Maildir.add()` は `tmp/` → `new/` の手順とファイル名の一意性を自動で処理してくれる
    （参考実装 `reference/maildir-delivery.sh` は手書きの実例）
- 文字コード: 件名の MIME エンコード（`=?UTF-8?B?...?=`）のデコードを忘れずに

## 参考資料

- `reference/maildir-delivery.sh` — find-job の check.sh から抜粋した Maildir 直接配信コード。
  ファイル名の一意性の作り方、tmp→保存 の手順の実例。
  ※ 抜粋元は Thunderbird 向けに `cur/` へ書いていたが、maildirsink は標準どおり `new/` に投函する

## 決定済み

- **JSON フィールド:** `subject` / `from` / `to` / `date` / `message_id` / `body` を保存する。
- **保存先ディレクトリのデフォルト:** `./mail`（カレント配下）。

## 未決定事項

- パッケージ名の衝突確認（PyPI / GitHub に maildirsink が既にないか）
