#!/bin/bash
# 既存のシェルスクリプトからの抜粋: Maildir 直接配信部分
#
# ポイント:
# - Maildir 形式は tmp/ に書き込んでから cur/ に mv する（配信の原子性を保証する標準手順）
# - ファイル名は「タイムスタンプ.PプロセスIDQ連番.ホスト名」で一意性を確保
# - X-Mozilla-Status / X-Mozilla-Status2 は Thunderbird (Icedove) が
#   未読状態を認識するためのヘッダ
# - 個人情報（実際の宛先・Maildir パス）はプレースホルダに置き換えてある

EMAIL_TO="you@example.com"
MAILDIR="$HOME/.thunderbird/PROFILE/Mail/Local Folders-maildir/フォルダ名"
SUBJECT="テスト件名 - $(date '+%Y-%m-%d %H:%M')"
BODY_FILE="/tmp/mail_body.txt"   # 本文となるテキストファイル

mkdir -p "${MAILDIR}/cur" "${MAILDIR}/tmp"

TIMESTAMP=$(date '+%s')
UNIQUE="${TIMESTAMP}.P$$Q1.$(hostname).eml"
MAIL_TMP="${MAILDIR}/tmp/${UNIQUE}"
MAIL_CUR="${MAILDIR}/cur/${UNIQUE}"

{
    echo "From - $(date -R)"
    echo "X-Mozilla-Status: 0000"
    echo "X-Mozilla-Status2: 00000000"
    echo "From: mailsink@localhost"
    echo "To: ${EMAIL_TO}"
    echo "Subject: ${SUBJECT}"
    echo "Date: $(date -R)"
    echo "Message-ID: <${TIMESTAMP}.$$@$(hostname)>"
    echo "Content-Type: text/plain; charset=UTF-8"
    echo "MIME-Version: 1.0"
    echo ""
    cat "$BODY_FILE"
} > "${MAIL_TMP}"

mv "${MAIL_TMP}" "${MAIL_CUR}"
echo "Maildirに保存しました: ${MAIL_CUR}"