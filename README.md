# maildirsink

[![PyPI](https://img.shields.io/pypi/v/maildirsink)](https://pypi.org/project/maildirsink/)
[![Python](https://img.shields.io/pypi/pyversions/maildirsink)](https://pypi.org/project/maildirsink/)
[![License](https://img.shields.io/pypi/l/maildirsink)](https://github.com/sogatat/maildirsink/blob/main/LICENSE)

A tiny SMTP server that catches mail and writes it straight to disk — as a
standard Maildir or as JSON. No web UI, no forwarding, no database. It does one
job: **receive and store**.

日本語版は [README-ja.md](https://github.com/sogatat/maildirsink/blob/main/README-ja.md) を参照してください。

## Why

When you develop something that sends mail, you need somewhere safe for it to
land — not a real inbox. Tools like [mailpit](https://github.com/axllent/mailpit)
and MailHog solve this with a web UI you open in a browser.

maildirsink takes the opposite approach: it writes **standard Maildir** and then
gets out of the way. Because the output is a plain, boring Maildir:

- Read it with a Maildir-native MUA — mutt, neomutt — with no extra setup.
- Point existing tooling at it: procmail, mbsync, and friends.
- Or just use `ls`, `grep`, and `cat`. It's one file per message.

There is no UI to learn and no format to export from. If you'd rather have
structured data than RFC 5322, use `--format json` and get one JSON file per
message instead.

## Quick start

```bash
pipx install maildirsink          # or: pip install maildirsink
maildirsink --dir ~/Maildir
```

Point your app's SMTP config at `localhost:1025` and send. Mail shows up in
`~/Maildir/new/` immediately.

To try it without an app, send one from Python:

```bash
python - <<'EOF'
import smtplib
from email.message import EmailMessage

m = EmailMessage()
m["Subject"] = "Hello"
m["From"] = "app@example.com"
m["To"] = "you@example.com"
m.set_content("It works.")
smtplib.SMTP("localhost", 1025).send_message(m)
EOF
```

## Install

```bash
pipx install maildirsink     # recommended: isolated, and puts `maildirsink` on PATH
pip install maildirsink      # or into a venv of your choice
```

Requires Python 3.9+.

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

The storage directory is created on startup if it doesn't exist.

### Exposing on a LAN

The default `localhost` only accepts mail from the same machine. To receive from
another host — a container, an app on another machine — listen on all
interfaces:

```bash
maildirsink --host 0.0.0.0 --port 1025
```

> **Warning:** maildirsink has no authentication and no TLS, and it accepts every
> message it is handed. Use it only on a trusted network. Never expose it to the
> internet.

## Storage formats

### `--format maildir` (default)

A standard Maildir. Each message is written to `tmp/` and then moved into
`new/` — the atomic two-step delivery the format requires — with a filename that
is guaranteed unique (`timestamp.Ppid.hostname`).

```
~/Maildir/
├── cur/
├── new/     ← delivered mail lands here
│   └── 1784265259.M961931P358986Q1.hostname
└── tmp/
```

Mail lands in `new/`, which is exactly where MUAs look for unread messages, so
they pick it up with no extra configuration.

### `--format json`

One JSON file per message, for when you want to assert on mail in tests rather
than read it. Headers are MIME-decoded and the `text/plain` body is extracted:

```json
{
  "subject": "Hello",
  "from": "app@example.com",
  "to": "you@example.com",
  "date": "Fri, 17 Jul 2026 08:48:00 +0900",
  "message_id": "<abc123@example.com>",
  "body": "It works.\n"
}
```

## Reading mail with mutt / neomutt

Point your MUA at the directory maildirsink writes to — that's the whole setup:

```muttrc
set mbox_type = Maildir
set folder    = "/path/to/maildir"
set spoolfile = "+."
mailboxes     = "/path/to/maildir"

# Pick up mail that arrives while mutt is running
set mail_check = 5      # seconds
set timeout    = 10
```

Mail that lands in `new/` shows up automatically, including while mutt is open.

## Platform support

| Platform | Status |
|---|---|
| Linux | Supported |
| macOS | Should work (not regularly tested) |
| Windows 11 + WSL2 | Supported — see below |
| Windows (native) | Not supported |

Native Windows is out of scope: there's no systemd, and Maildir-native MUAs
aren't realistically available there. Use WSL2 — it runs a real Linux kernel, so
maildirsink and the systemd unit below work unmodified.

### Windows 11 (WSL2)

Three WSL2-specific things to get right:

**1. Enable systemd.** It's off by default. Add this to `/etc/wsl.conf` inside
your distro, then run `wsl --shutdown` from Windows to restart it:

```ini
[boot]
systemd=true
```

**2. Keep the Maildir on the Linux filesystem.** Use `~/Maildir`, never a path
under `/mnt/c/...`. Windows drives are mounted via drvfs, where the atomic
`rename`/`link` semantics Maildir depends on are unreliable — and it's slow.

**3. Networking.** WSL2 sits behind NAT by default. Sending from a Windows app to
`localhost:1025` reaches maildirsink via localhost forwarding, so the default
setup just works. If you need to receive from other machines on the LAN, note
that the WSL2 VM's IP changes on each boot; on Windows 11 22H2+ you can avoid
that with mirrored networking in `%UserProfile%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

## Running as a service (systemd --user)

To keep maildirsink running without starting it by hand, drop a user unit at
`~/.config/systemd/user/maildirsink.service`:

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

The `ExecStart` path assumes `pipx install maildirsink`, which puts the command
in `~/.local/bin`. Adjust it if you installed elsewhere — e.g. point it at
`<your-venv>/bin/maildirsink`.

```bash
systemctl --user daemon-reload
systemctl --user enable --now maildirsink.service
systemctl --user status maildirsink        # check
journalctl --user -u maildirsink -f        # follow logs
```

This starts maildirsink when you log in. To keep it running without an active
login — and to start it at boot — enable lingering:

```bash
sudo loginctl enable-linger "$USER"
```

## How it works

Roughly 200 lines of Python over two well-worn libraries:

- **SMTP:** [`aiosmtpd`](https://github.com/aio-libs/aiosmtpd) — the stdlib
  `smtpd` was removed in Python 3.12.
- **Maildir:** the stdlib `mailbox.Maildir`, whose `add()` already implements the
  `tmp/` → `new/` delivery sequence and the filename uniqueness rules.
- **Headers:** MIME-encoded headers (`=?UTF-8?B?...?=`) are decoded on the way
  into JSON. A malformed header degrades to its raw value rather than dropping
  the message.

If storing a message fails, maildirsink returns SMTP `451` so the sender knows
the mail wasn't kept, and logs the traceback.

## Development

```bash
git clone https://github.com/sogatat/maildirsink
cd maildirsink
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](https://github.com/sogatat/maildirsink/blob/main/LICENSE).
