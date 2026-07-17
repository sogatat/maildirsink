# maildirsink

A tiny tool that receives mail over SMTP and just saves it to a file.
Like a development mail sink such as [mailpit](https://github.com/axllent/mailpit),
but with no UI and no forwarding — it sticks to one job: *receive and store*.

日本語版は [README-ja.md](README-ja.md) を参照してください。

## Why

In the [find-job](../find-job) project, notification mail was written directly
into a Maildir by a shell script. maildirsink extracts just that
"store mail locally" part into a general-purpose tool.

It commits to **standard Maildir** as the storage target, so it slots straight
into Maildir-native MUAs (mutt / neomutt) and existing Maildir tooling
(procmail, mbsync, and friends).

## What it does

1. On startup, listens as an SMTP server on the given port.
2. On receiving a message, stores it in the given directory in the given format.
3. Nothing else — no forwarding, no web UI.

## Storage formats

- **maildir** — standard Maildir. Incoming mail is written to `tmp/` and then
  moved into **`new/`** (the unread-mail spool). Filenames follow the standard
  uniqueness-guaranteeing scheme (`time.Ppid.hostname`). mutt / neomutt scan
  `new/` directly, so no extra setup is needed.

- **json** — one JSON file per message:

  ```json
  {
    "subject": "...",
    "from": "...",
    "to": "...",
    "date": "...",
    "message_id": "...",
    "body": "..."
  }
  ```

> **Note:** Direct delivery to Thunderbird is intentionally out of scope.
> Thunderbird keeps a `.msf` summary cache and won't notice mail written into a
> Maildir from outside until you "Repair Folder". Maildir-native MUAs like mutt
> don't have this problem and pick up mail dropped into `new/` immediately.

## Install

```bash
pip install .
# or, for development:
pip install -e ".[dev]"
```

## Usage

```bash
maildirsink [--port PORT] [--host HOST] [--format maildir|json] [--dir DIR]
```

| Option | Meaning | Default |
|---|---|---|
| `--port` | SMTP listen port | 1025 |
| `--host` | Listen host | localhost |
| `--format` | Storage format (maildir / json) | maildir |
| `--dir` | Storage directory | `./mail` |

### Exposing on a LAN

The default `localhost` only accepts mail sent from the same host. To receive
from another host (a container, a find-job instance on the LAN, etc.), listen on
all interfaces:

```bash
maildirsink --host 0.0.0.0 --port 1025
```

> **Warning:** There is no authentication and no TLS. Use it only within a
> trusted LAN. Do not expose it directly to the internet.

## Reading mail (mutt / neomutt)

Just point your MUA at the Maildir that maildirsink writes to. Because there is
no index cache like `.msf`, no repair step is ever needed.

```muttrc
set mbox_type = Maildir
set folder    = "/path/to/maildir"
set spoolfile = "+."
mailboxes     = "/path/to/maildir"

# Pick up mail that arrives while mutt is running
set mail_check = 5      # seconds
set timeout    = 10
```

Once mail lands in `new/`, mutt reflects it automatically.

## Implementation notes

- Written in Python.
  - SMTP server: `aiosmtpd` (the stdlib `smtpd` was removed in Python 3.12).
  - Maildir writing: the stdlib `mailbox.Maildir`. `Maildir.add()` handles the
    `tmp/` → `new/` sequence and filename uniqueness for you
    (`reference/maildir-delivery.sh` is a hand-written example of the same).
- Character sets: MIME-encoded headers (`=?UTF-8?B?...?=`) are decoded.

## Tests

```bash
pytest
```

## License

MIT — see [LICENSE](LICENSE).
